# HTTP API

Base path `/api`. All application endpoints except health/readiness/login require the `atlas_session` cookie. Mutation endpoints also require `X-CSRF-Token`, obtained after sign-in or through `/me`. Browser mutation Origins must match `APP_ORIGIN` exactly. There is no wildcard CORS policy.

## Endpoints

| Method | Path | Access | Result |
|---|---|---|---|
| GET | /health | Public | Liveness/version |
| GET | /ready | Public | Database and gRPC readiness |
| POST | /login | Public; rate limited | Sets cookie; returns CSRF token |
| POST | /logout | Signed in + CSRF | Deletes current server session and cookie |
| GET | /me | Signed in | Current identity and CSRF token |
| GET | /users | Signed in | Managed identity list without password fields |
| POST | /users | Administrator | Creates a managed record, not a login invitation |
| POST | /proposals | Operator/admin, policy dependent | Creates a manual proposal |
| POST | /ai/draft | Operator/admin + enabled cohort | Creates validated provider proposal |
| GET | /proposals | Signed in | Latest 100 proposals belonging to the actor |
| POST | /proposals/{id}/apply | Owner + current policy | Commits confirmed proposal |
| POST | /proposals/{id}/cancel | Owner | Cancels pending proposal |
| GET | /flags | Signed in | Global rollout values and current actor's effective cohort |
| PUT | /flags/{name} | Administrator | Updates percentage with version check |
| GET | /audit | Operator/admin | Latest 200 audit events |
| POST | /events | Signed in; rate limited | Accepts bounded aggregate UX telemetry |

List limits are intentionally small and pagination is not implemented. The identity directory is intended for a small demo dataset. API documentation is in this file; unauthenticated interactive Swagger endpoints are disabled.

## Example bodies

Create managed identity:

```json
{"name":"Taylor Kim","email":"taylor@example.test","role":"viewer"}
```

Manual proposal:

```json
{"target_id":"u-priya","action":"change_role","role":"operator"}
```

Actions: `suspend`, `restore`, `change_role`. Roles: `viewer`, `operator`, `admin`. For non-role operations, the role field defaults to viewer and does not change the target's role.

AI proposal:

```json
{"target_id":"u-priya","prompt":"Change role to operator"}
```

The model is not asked to select the target. An illustrative proposal response has fields:

```json
{"id":"server-generated-id","actor_id":"u-admin","target_id":"u-priya","action":"change_role","role":"operator","target_version":1,"reason":"Provider rationale","provider":"azure","risk":2,"status":"pending","created":0,"expires":600}
```

The timestamps above are schematic; actual values are Unix seconds. Proposal lifetime is 600 seconds. The server is authoritative about expiry.

Apply:

```json
{"confirmed":true}
```

Flag update:

```json
{"percent":25,"version":1}
```

Frontend event:

```json
{"name":"task_completed","surface":"admin","duration_ms":32000}
```

Event names: task_started, proposal_created, task_completed, task_failed. Surface is admin or review. Durations are bounded to 0–3,600,000 milliseconds. Extra fields are rejected, preventing accidental email/prompt payloads. The event API accepts `task_failed`, while the current frontend emits starts, proposal creation and completions; see the observability guide before calculating failure rates.

## Errors

Most errors use `{"detail":"human-readable reason"}`. Validation errors use FastAPI's structured detail list; the frontend presents a short form-validation message.

| Code | Meaning | Suggested UI behavior |
|---|---|---|
| 401 | Invalid credentials, missing/expired session or inactive account | Sign in again |
| 403 | CSRF/Origin/policy/rollout denial | Show reason; do not retry automatically |
| 404 | Identity/proposal/flag not found | Refresh or select a current record |
| 409 | Duplicate email, stale version, expired or resolved proposal | Refresh and draft again if needed |
| 413 | More than 16 KiB request body | Reduce input |
| 422 | Invalid schema or ambiguous AI interpretation | Correct request |
| 429 | Login/AI/event rate limit | Wait and retry later |
| 502 | AI provider failure | Use manual controls |
| 503 | Policy service unavailable | Wait for readiness; no mutation committed |

## Internal gRPC

`atlas.Policy/Evaluate` takes authoritative role/state inputs and returns allowed/risk/reason. `atlas.Policy/Flight` takes subject/flag/percent and returns enabled. Every call requires `x-policy-token` metadata. The gateway uses a two-second deadline. The adapter limits inbound message size to 16 KiB and authenticates before calling C. The internal channel is plaintext and must remain on loopback or the private container network.
