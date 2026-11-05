"""Authenticated export boundaries; real database round-trip runs in the PG suite."""
import copy
import json
import shutil

import pytest
from cryptography.fernet import Fernet

from rag.import_knowledge_base import DEFAULT_KB
from rag.repository import EvidenceRepository, RepositoryError
from rag.state_archive import corpus_digests, export_archive, restore_archive, write_new


class IsolatedStore:
    def __init__(self):
        self.state = {"format_version": 1, "blocked_sources": {}, "events": []}
        self.writes = 0

    def read(self):
        return copy.deepcopy(self.state)

    def restore_external(self, payload, *, validate_state, confirm=False):
        assert confirm
        validate_state(self.state)
        validate_state(payload)
        self.writes += 1
        self.state = copy.deepcopy(payload)
        return copy.deepcopy(payload)


@pytest.fixture()
def archive(tmp_path):
    directory = tmp_path / "kb"
    shutil.copytree(DEFAULT_KB, directory)
    repo = EvidenceRepository(directory, state_file=tmp_path / "state.json")
    expected = repo.quarantine_source("cea-complaint", actor="ArchiveUnitTest", reason="synthetic export test")
    key = Fernet.generate_key()
    token = export_archive(repo, key)
    repo._pgstore = IsolatedStore()
    return repo, key, token, expected


def test_authenticated_archive_preserves_exact_events_and_needs_confirmation(archive):
    repo, key, token, expected = archive
    assert b"ArchiveUnitTest" not in token
    with pytest.raises(RepositoryError, match="confirmation"):
        restore_archive(repo, token, key)
    assert repo._pgstore.writes == 0
    outcome = restore_archive(repo, token, key, confirm=True)
    assert outcome["event_count"] == outcome["blocked_source_count"] == 1
    assert repo.source_state() == expected


@pytest.mark.parametrize("fault", ["wrong_key", "tampered", "corpus", "version", "history", "unknown_source"])
def test_untrusted_archives_never_reach_a_state_write(archive, fault):
    repo, key, token, _ = archive
    if fault == "wrong_key":
        key = Fernet.generate_key()
    elif fault == "tampered":
        token = token[:-10] + b"AAAAAAAAAA"
    else:
        payload = json.loads(Fernet(key).decrypt(token))
        if fault == "corpus":
            payload["corpus_sha256"]["sources.csv"] = "0" * 64
        elif fault == "version":
            payload["source_version"] = "unreviewed-version"
        elif fault == "history":
            payload["state"]["events"] = []
        else:
            payload["state"]["events"][0]["source_id"] = "unknown-source"
        token = Fernet(key).encrypt(json.dumps(payload).encode())
    with pytest.raises(ValueError):
        restore_archive(repo, token, key, confirm=True)
    assert repo._pgstore.writes == 0
    assert repo._pgstore.state["events"] == []


def test_archive_and_key_creation_never_overwrite_existing_files(tmp_path):
    target = tmp_path / "private.key"
    write_new(target, b"original", ".key")
    with pytest.raises(FileExistsError):
        write_new(target, b"replacement", ".key")
    assert target.read_bytes() == b"original"
    with pytest.raises(RepositoryError):
        write_new(tmp_path / "unsafe.txt", b"private", ".key")


def test_same_corpus_recovers_across_windows_and_linux_newlines(archive):
    repo, key, token, expected = archive
    previous = corpus_digests(repo.directory)
    for path in repo.directory.iterdir():
        path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert corpus_digests(repo.directory) == previous
    assert restore_archive(repo, token, key, confirm=True)["restored"]
    assert repo.source_state() == expected
