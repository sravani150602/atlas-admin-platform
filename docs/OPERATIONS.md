# Local operations and troubleshooting

## Startup health

`/api/health` checks the HTTP process only. `/api/ready` checks database schema access and an authenticated gRPC call. A healthy HTTP process can be unready if the policy service is down. All mutations fail closed on policy unavailability.

| Symptom | Likely cause | Action |
|---|---|---|
| Cannot load libatlas.so | Native build missing | Run `make all` from repository root |
| policy_pb2 import failure | Generated bindings missing | Activate venv and run `make proto` |
| Sign-in fails after changing .env | Existing DB still has original hash | Use original password; reset disposable data only if intended |
| 403 Origin not allowed | Browser address differs from APP_ORIGIN | Match scheme, hostname and port exactly |
| Session cookie missing over HTTP | COOKIE_SECURE=true on local HTTP | Use local false or configure HTTPS |
| 503 policy unavailable | Service/token/address mismatch | Check both services use same token and correct target |
| 409 identity changed | Stale proposal | Refresh, review current state and create a fresh proposal |
| AI disabled | Cohort excluded or global rollout 0 | Check Feature rollout; do not bypass the API check |
| Azure 502 | Credentials, endpoint, capability, quota or availability | Check server-side configuration safely; use manual controls |
| UI cannot resolve @atlas/ux | Shared package not built | Run `npm run build` |
| Port in use | Another local stack is running | Stop that stack; launcher uses fixed default ports |
| SQLite locked | Long-running writer or unsupported filesystem | Keep one gateway replica; use local disk and inspect blocking process |
| Sanitizer fatal /proc error | LeakSanitizer restricted by sandbox | Record limitation; use detect_leaks=0 for address/UB checks |

## Credentials

`scripts/setup.py` refuses to overwrite an existing `.env`. The admin account is created only when users is empty. There is no online password-reset API. For a disposable demo, stop services, back up if needed, and explicitly remove the demo database and its WAL/SHM sidecars before starting with a newly generated configuration. This deletes application state. For real data, implement a reviewed recovery workflow rather than manual database edits.

To rotate POLICY_TOKEN, update both services and restart them together. To rotate Azure credentials, update the server environment and restart the gateway. Existing sessions persist in SQLite until expiry, logout or target access changes.

## Backup

For a consistent online SQLite snapshot, use Python's SQLite backup API, not an arbitrary copy of the main database while WAL writes are in flight. Example using local paths you control:

```python
import sqlite3
with sqlite3.connect('data/atlas.db') as source:
    with sqlite3.connect('/secure/path/atlas-backup.db') as destination:
        source.backup(destination)
```

Protect snapshots as sensitive data. To restore, stop services and restore a tested snapshot in an isolated environment first. Backup/restore automation is not included.

## Rollback

For code rollback, return to a known commit, reinstall locked dependencies and rebuild the C library/protobuf/frontend. Current schema uses initial creation only; future schema changes require explicit migrations and rollback policy. A restored database can reintroduce old sessions, so plan session invalidation when restoring state.

For a bad access change, use a new inverse proposal (restore after suspend, or the previous role from audit) and review it. Do not rewrite historical audit entries. The system does not provide one-click automatic undo.

## Operational limits

One gateway replica, synthetic datasets, no pagination beyond bounded audit/proposal lists, no background expiry cleanup for proposals, no scheduled backups and no external alert delivery. Expired proposals are rejected at apply time and displayed as expired by the client. Client time is only presentation; the server checks actual expiry.
