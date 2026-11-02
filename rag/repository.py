"""Fresh knowledge reads, source quarantine and checked source-bundle updates."""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from rag.import_knowledge_base import DEFAULT_KB, KnowledgeBaseError, load_knowledge_base, nonblank, read_json, timestamp
from rag.source_review import capture, normalize_space

DEFAULT_STATE = DEFAULT_KB.parents[1] / "instance" / "rag_quarantine.json"


class RepositoryError(ValueError):
    """The knowledge bundle or its operational source state is unavailable."""


def ensure(condition, message):
    if not condition:
        raise RepositoryError(message)


def _load(directory):
    try:
        return load_knowledge_base(directory)
    except (KnowledgeBaseError, OSError, TypeError, KeyError) as error:
        raise RepositoryError("Knowledge bundle failed validation") from error


class EvidenceRepository:
    """No evidence cache: each operation reads the current checked five-file bundle."""

    def __init__(self, directory=DEFAULT_KB, *, state_file=DEFAULT_STATE):
        self.directory = Path(directory).resolve()
        self.state_file = Path(state_file).resolve()
        ensure(not self.state_file.is_relative_to(self.directory), "Quarantine state must be outside the five-file source directory")

    def _state(self, bundle):
        try:
            with self.state_file.open(encoding="utf-8") as stream:
                state = read_json(stream.read())
        except FileNotFoundError:
            return {"format_version": 1, "blocked_sources": {}, "events": []}
        except (OSError, ValueError) as error:
            raise RepositoryError("Quarantine state cannot be read") from error
        ensure(isinstance(state, dict) and set(state) == {"format_version", "blocked_sources", "events"}, "Invalid quarantine state fields")
        ensure(type(state["format_version"]) is int and state["format_version"] == 1, "Unsupported quarantine state version")
        ensure(isinstance(state["blocked_sources"], dict) and isinstance(state["events"], list), "Invalid quarantine state structure")
        for source_id, entry in state["blocked_sources"].items():
            self._check_event(entry, source_id, bundle, blocked=True)
        for entry in state["events"]:
            ensure(isinstance(entry, dict), "Invalid source event")
            self._check_event(entry, entry.get("source_id"), bundle, blocked=False)
        return state

    @staticmethod
    def _check_event(entry, source_id, bundle, *, blocked):
        fields = {"actor", "reason", "at", "source_version"}
        if not blocked:
            fields |= {"source_id", "action"}
        ensure(isinstance(entry, dict) and set(entry) == fields, "Invalid source event fields")
        ensure(isinstance(source_id, str) and source_id in bundle["sources"], "Unknown source in quarantine state")
        ensure(all(nonblank(entry.get(key)) for key in ("actor", "reason", "source_version")), "Source event needs actor, reason and version")
        if not blocked:
            ensure(entry["action"] in ("quarantine", "release"), "Invalid source event action")
        try:
            timestamp(entry["at"], "source event")
        except KnowledgeBaseError as error:
            raise RepositoryError("Invalid source event timestamp") from error

    def snapshot(self):
        bundle = _load(self.directory)
        state = self._state(bundle)
        return bundle, frozenset(state["blocked_sources"])

    def source_state(self):
        bundle = _load(self.directory)
        return copy.deepcopy(self._state(bundle))

    @contextmanager
    def _locked_state(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        lock = self.state_file.with_name(self.state_file.name + ".lock")
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except OSError as error:
            raise RepositoryError("Source state is busy or cannot be locked") from error
        try:
            os.close(fd)
            yield
        finally:
            lock.unlink()

    def _save(self, state):
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.state_file.parent,
                                             prefix=self.state_file.name + ".", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(state, stream, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_file)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def quarantine_source(self, source_id, *, actor, reason):
        ensure(nonblank(actor) and nonblank(reason), "Quarantine needs an actor and reason")
        bundle = _load(self.directory)
        ensure(isinstance(source_id, str) and source_id in bundle["sources"], "Unknown source")
        with self._locked_state():
            state = self._state(bundle)
            previous = state["blocked_sources"].get(source_id)
            if previous and previous["actor"] == actor and previous["reason"] == reason:
                return copy.deepcopy(state)
            entry = {"actor": actor, "reason": reason, "source_version": bundle["source_version"],
                     "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            state["blocked_sources"][source_id] = entry
            state["events"].append({"source_id": source_id, "action": "quarantine", **entry})
            self._save(state)
        return copy.deepcopy(state)

    @staticmethod
    def _check_live_source(bundle, source_id):
        source = bundle["sources"][source_id]
        if source["status"] != "verified":
            return "UNVERIFIED"
        current = capture(source["url"])
        if current["http_status"] != 200 or current["url"] != source["url"]:
            return "UNAVAILABLE"
        reviews = [row for row in bundle["review_log"].values() if row["source_id"] == source_id
                   and row["new_version"] == source["version"] and row["review_status"] == "verified"
                   and row["reviewed_at"] == source["reviewed_at"] and row["reviewed_by"] == source["reviewed_by"]]
        if not any(row["content_sha256"] == current["content_sha256"] for row in reviews):
            return "CHANGED"
        text = normalize_space(current["text"])
        if any(normalize_space(passage["text"]) not in text for passage in bundle["passages"].values()
               if passage["source_id"] == source_id):
            return "CHANGED"
        return "MATCHED"

    def check_live_sources(self, *, actor):
        """Quarantine a changed/unavailable source; never automatically release one."""
        ensure(nonblank(actor), "Source check needs an actor")
        bundle = _load(self.directory)
        results = []
        for source_id in bundle["sources"]:
            try:
                status = self._check_live_source(bundle, source_id)
            except (OSError, ValueError):
                status = "UNAVAILABLE"
            if status != "MATCHED":
                self.quarantine_source(source_id, actor=actor, reason="live_source_" + status.lower())
            results.append({"source_id": source_id, "check_status": status})
        return results

    def release_source(self, source_id, *, actor, reason):
        """Release only after a fresh match to the current recorded source review."""
        ensure(nonblank(actor) and nonblank(reason), "Release needs an actor and reason")
        bundle = _load(self.directory)
        ensure(isinstance(source_id, str) and source_id in bundle["sources"], "Unknown source")
        try:
            status = self._check_live_source(bundle, source_id)
        except (OSError, ValueError) as error:
            raise RepositoryError("Source could not be checked for release") from error
        ensure(status == "MATCHED", "Source must match its current review before release")
        with self._locked_state():
            # Re-read current files to avoid accepting a review changed during the network check.
            ensure(_load(self.directory) == bundle, "Knowledge changed during release; retry")
            state = self._state(bundle)
            ensure(source_id in state["blocked_sources"], "Source is not quarantined")
            del state["blocked_sources"][source_id]
            state["events"].append({"source_id": source_id, "action": "release", "actor": actor,
                                    "reason": reason, "source_version": bundle["source_version"],
                                    "at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
            self._save(state)
        return copy.deepcopy(state)

    def update_from(self, directory, *, verify_live=True):
        """Switch this repository instance to a complete checked candidate directory."""
        candidate_path = Path(directory).resolve()
        ensure(not self.state_file.is_relative_to(candidate_path), "State must remain outside source files")
        old = _load(self.directory)
        candidate = _load(candidate_path)
        if candidate["source_version"] == old["source_version"]:
            ensure(all(candidate[key] == old[key] for key in ("passages", "rules", "templates")),
                   "Evidence content updates require a new source_version")
        self._state(candidate)  # Existing quarantine survives a version/path change.
        if verify_live:
            try:
                ensure(all(self._check_live_source(candidate, source_id) == "MATCHED" for source_id in candidate["sources"]),
                       "Candidate source review does not match the live pages")
            except (OSError, ValueError) as error:
                raise RepositoryError("Candidate could not pass live source checks") from error
        ensure(_load(candidate_path) == candidate, "Candidate changed during update; retry")
        self.directory = candidate_path
        return candidate["source_version"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("state", "quarantine", "release", "check-live"))
    parser.add_argument("--source")
    parser.add_argument("--actor")
    parser.add_argument("--reason")
    parser.add_argument("--directory", type=Path, default=DEFAULT_KB)
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args(argv)
    try:
        repository = EvidenceRepository(args.directory, state_file=args.state_file)
        if args.command == "state":
            result = repository.source_state()
        elif args.command == "check-live":
            result = repository.check_live_sources(actor=args.actor)
        elif args.command == "quarantine":
            result = repository.quarantine_source(args.source, actor=args.actor, reason=args.reason)
        else:
            result = repository.release_source(args.source, actor=args.actor, reason=args.reason)
        print(json.dumps(result, indent=2))
        return 1 if args.command == "check-live" and any(row["check_status"] != "MATCHED" for row in result) else 0
    except (RepositoryError, OSError) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
