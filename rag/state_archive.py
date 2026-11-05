"""Operator-only authenticated encrypted state export/recovery; no HTTP admin route.

Keep the key separately from the encrypted archive. An export is a state snapshot,
not a provider database dump, automatic backup schedule or credential backup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from rag.import_knowledge_base import DEFAULT_KB, FILES, load_knowledge_base, read_json, timestamp
from rag.repository import EvidenceRepository, RepositoryError


def corpus_digests(directory):
    # Git checkouts may use CRLF on Windows and LF on Render. Bind the exact
    # UTF-8 text with canonical LF endings, not the checkout's newline choice.
    return {name: hashlib.sha256((Path(directory) / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for name in sorted(FILES)}


def export_archive(repository, key):
    """Validate state and bind its encrypted snapshot to all five exact source files."""
    bundle = load_knowledge_base(repository.directory)
    digests = corpus_digests(repository.directory)
    state = repository.source_state()
    if corpus_digests(repository.directory) != digests:
        raise RepositoryError("Knowledge changed during export; retry")
    payload = {"format_version": 2, "created_at": datetime.now(timezone.utc).isoformat(),
               "source_version": bundle["source_version"], "corpus_sha256": digests, "state": state}
    return Fernet(key).encrypt(json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def restore_archive(repository, token, key, *, confirm=False):
    """Reject wrong keys, tampering, unknown source history and corpus mismatches first."""
    if not confirm:
        raise RepositoryError("Restore requires explicit operator confirmation")
    if repository._pgstore is None:
        raise RepositoryError("Archive restoration requires configured PostgreSQL persistence")
    try:
        payload = read_json(Fernet(key).decrypt(token).decode("utf-8"))
    except (InvalidToken, ValueError, UnicodeError, TypeError):
        raise RepositoryError("Archive authentication or decoding failed") from None
    fields = {"format_version", "created_at", "source_version", "corpus_sha256", "state"}
    if not isinstance(payload, dict) or set(payload) != fields or type(payload["format_version"]) is not int or payload["format_version"] != 2:
        raise RepositoryError("Unsupported archive format")
    timestamp(payload["created_at"], "archive creation")
    bundle = load_knowledge_base(repository.directory)
    if payload["source_version"] != bundle["source_version"] or payload["corpus_sha256"] != corpus_digests(repository.directory):
        raise RepositoryError("Archive corpus differs; source-owner reconciliation required")
    repository._validate_state(payload["state"], bundle)
    restored = repository._pgstore.restore_external(
        payload["state"], validate_state=lambda state: repository._validate_state(state, bundle), confirm=True)
    return {"restored": True, "source_version": bundle["source_version"],
            "event_count": len(restored["events"]), "blocked_source_count": len(restored["blocked_sources"])}


def write_new(path, value, suffix):
    path = Path(path)
    if path.suffix != suffix:
        raise RepositoryError("Use the required ignored file suffix: " + suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["keygen", "export", "restore"])
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--confirm-restore", action="store_true")
    parser.add_argument("--expected-target-host", help="Required for restore; exact intended database host, without credentials")
    args = parser.parse_args(argv)
    try:
        if args.key_file.resolve().is_relative_to(DEFAULT_KB.resolve()):
            raise RepositoryError("Private key must be outside the reviewed corpus")
        if args.command == "keygen":
            write_new(args.key_file, Fernet.generate_key(), ".key")
            print("A new private archive key was written; keep it separate from backups.")
            return 0
        if not args.archive:
            parser.error("--archive is required for export and restore")
        key = args.key_file.read_bytes().strip()
        repository = EvidenceRepository()
        if args.archive.resolve().is_relative_to(repository.directory):
            raise RepositoryError("Archive must be outside the reviewed corpus")
        if args.command == "export":
            write_new(args.archive, export_archive(repository, key), ".sgnavi-backup")
            print("Encrypted state snapshot exported; no credentials or source release included.")
        else:
            from psycopg.conninfo import conninfo_to_dict
            target_host = conninfo_to_dict(os.environ.get("SG_NAVI_STATE_DATABASE_URL", "")).get("host")
            if not args.expected_target_host or target_host != args.expected_target_host:
                raise RepositoryError("Confirm the exact intended database host before restoring")
            print(json.dumps(restore_archive(repository, args.archive.read_bytes(), key, confirm=args.confirm_restore)))
        return 0
    except (OSError, ValueError):
        # Driver errors, filenames and secret values are deliberately not rendered.
        print("State archive operation failed. Check target, confirmation, key, corpus and storage; original state is retained.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
