"""Actual PostgreSQL durability acceptance using a disposable CI database.

Do not run with any production database. Requires both explicit test flags.
No official source review state is changed; all facts are synthetic.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest


@pytest.fixture(scope="module")
def transient_database():
    if os.getenv("SG_NAVI_TEST_EPHEMERAL_POSTGRES") != "1":
        pytest.skip("NOT RUN: dedicated disposable PostgreSQL test service not configured")
    dsn = os.getenv("SG_NAVI_POSTGRES_TEST_DSN")
    if not dsn:
        pytest.skip("NOT RUN: disposable PostgreSQL test DSN absent")

    import psycopg
    from rag.postgres_state import PostgresStateStore
    store = PostgresStateStore(dsn)
    store.prepare()
    with psycopg.connect(dsn) as conn:
        conn.execute("DELETE FROM sgnavi_quarantine_backups")
        conn.execute("DELETE FROM sgnavi_quarantine_state")
        conn.execute("DELETE FROM sgnavi_quarantine_metadata")
    store.prepare()
    previous = {key: os.environ.get(key) for key in (
        "SG_NAVI_STATE_DATABASE_URL", "SG_NAVI_FREE_DEMO",
        "SG_NAVI_REQUIRE_PERSISTENCE", "RENDER",
    )}
    os.environ.update({
        "SG_NAVI_STATE_DATABASE_URL": dsn,
        "SG_NAVI_FREE_DEMO": "1",
        "SG_NAVI_REQUIRE_PERSISTENCE": "1",
        "RENDER": "true",
    })
    yield store
    with psycopg.connect(dsn) as conn:
        conn.execute("DELETE FROM sgnavi_quarantine_backups")
        conn.execute("DELETE FROM sgnavi_quarantine_state")
        conn.execute("DELETE FROM sgnavi_quarantine_metadata")
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _run_state():
    cmd = [sys.executable, "-m", "rag.repository", "state"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    assert result.returncode == 0, "A separate process failed to read PG quarantine state"
    return json.loads(result.stdout)


def _launch_gunicorn():
    from contextlib import closing
    import socket

    with closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    command = [
        sys.executable, "-m", "gunicorn", "--bind", "127.0.0.1:" + str(port),
        "--workers", "1", "--threads", "2", "--timeout", "20",
        "backend.production:app",
    ]
    proc = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        result = None
        for _ in range(90):
            if proc.poll() is not None:
                pytest.fail("Gunicorn terminated before localhost health was available")
            try:
                with urlopen("http://127.0.0.1:" + str(port) + "/api/version", timeout=2) as r:
                    result = json.loads(r.read())
                    assert r.status == 200
                    assert r.headers["X-SG-Navi-Deployment-Mode"] == "postgres-backed-free-demo"
                    break
            except OSError:
                time.sleep(0.15)
        assert result and result["rule_version"] == "mock-1"
        return result
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=8)


def test_actual_postgres_quarantine_restart_backup_and_recovery(transient_database):
    """Actual transaction, 2 separate server processes, durable backup/restore."""
    from rag.repository import EvidenceRepository
    repo = EvidenceRepository()
    bundle, blocked = repo.snapshot()
    assert not blocked
    assert repo._pgstore is not None

    before_backup = repo.backup_state(label="ci_before_test")
    assert before_backup["verified"]
    source_id = next(iter(bundle["sources"]))

    changed = repo.quarantine_source(
        source_id, actor="Task7DisposableCI",
        reason="synthetic_test_write_restart_recovery",
    )
    assert source_id in changed["blocked_sources"]
    assert len(changed["events"]) == 1

    # An entirely new Python process must see exactly the committed event.
    independent = _run_state()
    assert independent == changed
    _launch_gunicorn()  # First real WSGI process starts and stops.
    _launch_gunicorn()  # Second distinct WSGI process reads same PostgreSQL state.
    repo_after_restart = EvidenceRepository()
    _, blocked_after_restart = repo_after_restart.snapshot()
    assert source_id in blocked_after_restart
    assert repo_after_restart.source_state() == changed

    after_backup = repo_after_restart.backup_state(label="ci_after_quarantine")
    assert after_backup["verified"]
    assert repo_after_restart._pgstore.inspect_backup(after_backup["backup_id"]) == changed

    # Restore protected by explicit confirmation; original live value backed up.
    with pytest.raises(ValueError, match="confirmation"):
        repo_after_restart.restore_state(before_backup["backup_id"], confirm=False)
    outcome = repo_after_restart.restore_state(before_backup["backup_id"], confirm=True)
    assert outcome["blocked_source_count"] == 0
    assert repo_after_restart.source_state()["events"] == []

    recovered = repo_after_restart.restore_state(after_backup["backup_id"], confirm=True)
    assert recovered["blocked_source_count"] == 1
    assert recovered["event_count"] == 1
    assert _run_state() == changed
    assert source_id in EvidenceRepository().snapshot()[1]

    print("PG_DURABILITY_PASS", json.dumps({
        "source_version": bundle["source_version"], "quarantine_source": source_id,
        "cross_process_restart": "2 independent Gunicorn instances",
        "backup_ids": [before_backup["backup_id"], after_backup["backup_id"]],
        "restore_round_trip": True, "event_count": 1,
    }))


def test_actual_postgres_corrupt_event_fails_closed(transient_database):
    from rag.repository import EvidenceRepository, RepositoryError
    import psycopg
    repo = EvidenceRepository()
    bundle, _ = repo.snapshot()
    source = next(iter(bundle["sources"]))
    repo.quarantine_source(source, actor="Task7DisposableCI", reason="fault_test")
    with psycopg.connect(os.environ["SG_NAVI_POSTGRES_TEST_DSN"]) as conn:
        conn.execute("""UPDATE sgnavi_quarantine_state
                          SET state_json = '{"format_version":1,"blocked_sources":{"fake-source":{}},"events":[]}'::jsonb
                          WHERE state_key = 'quarantine-v1'""")
    try:
        with pytest.raises(RepositoryError):
            EvidenceRepository().snapshot()
    finally:
        # Disposable CI database only. Never delete real quarantines to fix errors.
        with psycopg.connect(os.environ["SG_NAVI_POSTGRES_TEST_DSN"]) as conn:
            conn.execute("""UPDATE sgnavi_quarantine_state
                            SET state_json = '{"format_version":1,"blocked_sources":{},"events":[]}'::jsonb
                            WHERE state_key = 'quarantine-v1'""")
