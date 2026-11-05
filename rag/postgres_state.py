"""PostgreSQL durability adapter for the *existing* validated RAG quarantine state.

Only enabled with SG_NAVI_STATE_DATABASE_URL, supplied privately as an environment
variable by the host. Never log DSNs. All mutations acquire a database-wide
transactional advisory lock and commit the complete JSON state atomically.

PostgreSQL backing storage is separate from the five version-controlled source
files. Free hosted databases can expire; durable != permanently retained.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar

import psycopg


_LOCK_ID = 74903971042
_ROW_ID = "quarantine-v1"


class DurableStateError(ValueError):
    """Remote state cannot safely be read or written; fail closed."""


class PostgresStateStore:
    def __init__(self, dsn: str):
        if not isinstance(dsn, str) or not dsn.strip():
            raise DurableStateError("Persistent state database is not configured")
        self._dsn = dsn
        self._transaction = ContextVar("sg_navi_quarantine_transaction", default=None)

    def _connect(self):
        try:
            return psycopg.connect(self._dsn, connect_timeout=7)
        except psycopg.Error:
            # Do not render a driver error: it can contain host/credentials.
            raise DurableStateError("Persistent quarantine database is unavailable") from None

    def prepare(self):
        """Set up the two state tables, never remove or reset an existing row."""
        try:
            with self._connect() as db:
                db.execute("""
                    CREATE TABLE IF NOT EXISTS sgnavi_quarantine_state (
                        state_key TEXT PRIMARY KEY,
                        state_json JSONB NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                """)
                db.execute("""
                    CREATE TABLE IF NOT EXISTS sgnavi_quarantine_backups (
                        backup_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                        backup_label TEXT NOT NULL,
                        state_json JSONB NOT NULL,
                        backed_up_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                """)
                db.execute("""
                    CREATE TABLE IF NOT EXISTS sgnavi_quarantine_metadata (
                        metadata_key TEXT PRIMARY KEY,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                """)
                # A missing row is legal only during first initialization.
                # An initialized DB with missing state must fail closed.
                db.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_ID,))
                marker = db.execute(
                    "SELECT metadata_key FROM sgnavi_quarantine_metadata WHERE metadata_key=%s",
                    (_ROW_ID,),
                ).fetchone()
                state = db.execute(
                    "SELECT state_key FROM sgnavi_quarantine_state WHERE state_key=%s",
                    (_ROW_ID,),
                ).fetchone()
                if marker and not state:
                    raise DurableStateError("Initialized quarantine state row is missing")
                if not marker:
                    if not state:
                        db.execute("""
                            INSERT INTO sgnavi_quarantine_state (state_key, state_json)
                            VALUES (%s, %s::jsonb)
                        """, (_ROW_ID, '{"format_version":1,"blocked_sources":{},"events":[]}'))
                    db.execute(
                        "INSERT INTO sgnavi_quarantine_metadata (metadata_key) VALUES (%s)",
                        (_ROW_ID,),
                    )
        except psycopg.Error:
            raise DurableStateError("Could not prepare durable quarantine state") from None

    def read(self):
        active = self._transaction.get()
        try:
            if active is not None:
                result = active.execute(
                    "SELECT state_json::text FROM sgnavi_quarantine_state WHERE state_key = %s",
                    (_ROW_ID,),
                ).fetchone()
            else:
                with self._connect() as db:
                    result = db.execute(
                        "SELECT state_json::text FROM sgnavi_quarantine_state WHERE state_key = %s",
                        (_ROW_ID,),
                    ).fetchone()
            if not result:
                raise DurableStateError("Persistent quarantine row is missing")
            return json.loads(result[0])
        except (psycopg.Error, ValueError, TypeError):
            raise DurableStateError("Persistent quarantine state cannot be read") from None

    @contextmanager
    def locked(self):
        """Whole read/validate/write operation under a single PG transaction lock."""
        if self._transaction.get() is not None:
            raise DurableStateError("Nested quarantine transactions are not supported")
        try:
            with self._connect() as db:
                db.execute("SELECT pg_advisory_xact_lock(%s)", (_LOCK_ID,))
                token = self._transaction.set(db)
                try:
                    yield
                finally:
                    self._transaction.reset(token)
        except psycopg.Error:
            raise DurableStateError("Quarantine transaction was not committed") from None

    def save(self, state):
        db = self._transaction.get()
        if db is None:
            raise DurableStateError("Quarantine write requires a transaction lock")
        try:
            payload = json.dumps(state, ensure_ascii=False, separators=(",", ":"))
            db.execute("""
                INSERT INTO sgnavi_quarantine_state (state_key, state_json)
                VALUES (%s, %s::jsonb)
                ON CONFLICT (state_key)
                DO UPDATE SET state_json=EXCLUDED.state_json, updated_at=now()
            """, (_ROW_ID, payload))
        except (psycopg.Error, TypeError, ValueError):
            raise DurableStateError("Quarantine write failed and was rolled back") from None

    def backup(self, label: str):
        """Append an immutable database backup row; never overwrite older backups."""
        if not isinstance(label, str) or not (0 < len(label.strip()) <= 120):
            raise DurableStateError("A 1-120 character backup label is required")
        try:
            with self.locked():
                db = self._transaction.get()
                row = db.execute("""
                    INSERT INTO sgnavi_quarantine_backups (backup_label, state_json)
                    SELECT %s, state_json FROM sgnavi_quarantine_state WHERE state_key = %s
                    RETURNING backup_id
                """, (label, _ROW_ID)).fetchone()
                if row is None:
                    raise DurableStateError("Cannot back up missing quarantine state")
                return row[0]
        except psycopg.Error:
            raise DurableStateError("Quarantine backup failed") from None

    def inspect_backup(self, backup_id: int):
        try:
            with self._connect() as db:
                row = db.execute("""
                    SELECT state_json::text FROM sgnavi_quarantine_backups WHERE backup_id=%s
                """, (backup_id,)).fetchone()
            if not row:
                raise DurableStateError("Quarantine backup was not found")
            return json.loads(row[0])
        except (psycopg.Error, ValueError, TypeError):
            raise DurableStateError("Quarantine backup cannot be read") from None

    def restore(self, backup_id: int, *, validate_state, confirm=False):
        """Restore only when an explicit operator confirmation and validator exist.

        Immediately back up the previous live value in the *same transaction*
        before changing it. Fail closed on invalid historical source IDs/events.
        """
        if not confirm:
            raise DurableStateError("Restore requires explicit operator confirmation")
        try:
            with self.locked():
                db = self._transaction.get()
                row = db.execute("""
                    SELECT state_json::text FROM sgnavi_quarantine_backups WHERE backup_id=%s
                    FOR UPDATE
                """, (backup_id,)).fetchone()
                if not row:
                    raise DurableStateError("Quarantine backup was not found")
                payload = json.loads(row[0])
                self._apply_restore(payload, validate_state, "before_restore_" + str(backup_id))
            return payload
        except (psycopg.Error, ValueError, TypeError):
            raise DurableStateError("Quarantine restore failed; original state retained") from None

    def _apply_restore(self, payload, validate_state, label):
        """Caller holds the transaction lock; never replace unreadable current state."""
        current = self.read()
        validate_state(current)
        validate_state(payload)
        self._transaction.get().execute("""
            INSERT INTO sgnavi_quarantine_backups (backup_label, state_json)
            VALUES (%s, %s::jsonb)
        """, (label, json.dumps(current, ensure_ascii=False)))
        self.save(payload)

    def restore_external(self, payload, *, validate_state, confirm=False):
        """Operator-only import of an authenticated, corpus-matched off-provider archive."""
        if not confirm:
            raise DurableStateError("Restore requires explicit operator confirmation")
        try:
            with self.locked():
                self._apply_restore(payload, validate_state, "before_external_restore")
            return payload
        except (psycopg.Error, ValueError, TypeError):
            raise DurableStateError("External restore failed; original state retained") from None
