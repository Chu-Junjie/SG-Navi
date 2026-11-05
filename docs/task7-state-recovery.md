# Task 7 — verified state persistence and operator recovery

Readiness/hosted-WSGI checkpoint: `3994850f29a04356c3a708daee56815294278895` / PR #64.
Final archive format 2 and its fresh restore are bound to the actual operator
code digest in the machine proof; final PR-head CI checks that complete change.
This is a tested operator procedure for RAG quarantine history, not user cases,
source text, credentials, full database contents or an automatic backup service.

## Actual hosted experiment — 2026-11-05

- User approved the isolated credential transfer and the creation of a **Free**
  Render test service. No paid resource or production state was changed.
- Neon project damp-scene-05807412, nondefault branch
  **br-dawn-sky-azha88sn / task7-recovery-20261105**; source database neondb.
  Its one synthetic quarantine event/source is operational test data.
- Render **srv-dbm4v2rbc2fs738b2in0**, Singapore, Free, auto-deploy off:
  [test service](https://dashboard.render.com/web/srv-dbm4v2rbc2fs738b2in0).
  Same code first Live as dep-dbm4v3bbc2fs738b2jrg and then Live after the actual
  same-code redeploy dep-dbm5035bedkc73b8bg1g. State digest before/after:
  `34e9edb91fc40dd9e5dd292189a3d4ca96e48f949fb8306a85f5c7a4c208059b`.
  Both actual health requests returned 200 and postgres-backed-free-demo.
- An encrypted archive was physically written on the Windows coordinator
  machine, outside Neon/Render. It restored the exact event history into the
  separate freshly created database **sgnavi_recovery_restore_v2** on the test
  branch. Wrong-key decryption left the empty target unchanged.
- Keygen, export, wrong-target rejection and confirmed CLI restore were also
  executed successfully. No database URL, archive key or decrypted state is
  included in repository evidence. [Machine record](test-results/task7-hosted-recovery-20261105.json).
- Separate real disposable PostgreSQL CI
  [42004044526](https://github.com/Chu-Junjie/SG-Navi/actions/runs/42004044526)
  passed all three tests, including encrypted external recovery and corrupt
  history failing closed.

The test resources remain available with automatic deployment disabled; they
are separate from the public demo. Review resource retention and free quotas
before reusing them. This single controlled drill does not claim a provider
outage, recovery on a second physical machine, scheduled exports or key escrow.

## Operator procedure

Use the repository's installed requirements. The database connection is supplied
privately through `SG_NAVI_STATE_DATABASE_URL`; do not paste it into commands or
public records. Confirm its intended role/database/branch before each operation.

```powershell
python -m rag.state_archive keygen --key-file instance/recovery-private.key
python -m rag.state_archive export --key-file instance/recovery-private.key --archive instance/state.sgnavi-backup
```

Key files and `.sgnavi-backup` files are Git-ignored and created exclusively,
without overwriting existing backups. Use a new archive name each time. Keep
the key separately in protected storage; copy the encrypted archive to an
approved off-provider location. The local Windows copy was used in the actual
drill; an organization-wide export schedule or secret-management system has
not been provisioned by this change.

To restore, provision and verify an isolated target first, configure its private
connection, initialize/validate the current canonical corpus/state and confirm
the **exact target hostname**. Archive format 2 binds all five UTF-8 source-file
digests with canonical LF newlines, so Windows CRLF and Render LF checkouts of
the same files can recover each other. Source version and all other bytes must
match. A source update requires owner reconciliation,
not an override switch.

```powershell
python -m rag.state_archive restore --key-file instance/recovery-private.key --archive instance/state.sgnavi-backup --expected-target-host <confirmed-target-host> --confirm-restore
```

This command takes a validated pre-restore snapshot in the target database in
the same transaction before applying the authenticated archive. Missing or
invalid current state, invalid history, wrong key, changed corpus, wrong host
or omitted confirmation fails closed. The database must already be initialized
and readable; this is not an emergency bypass for a corrupted live database.
Preserve broken state for investigation and involve the RAG owner if it cannot
be validated. There is no public administrative HTTP route.

Application rollback does not roll back source truth or quarantine events.
Pin a reviewed compatible code SHA, preserve the database and encrypted archive,
validate the source corpus and restored state, then confirm actual HTTP health,
version and both synthetic flows. Never delete history to make a check pass.
