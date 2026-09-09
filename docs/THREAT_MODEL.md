# Threat model

## Assets and boundaries

Assets: bootstrap password hash, raw session cookie, CSRF token, internal policy credential, Azure key, identity state, proposal ownership, and audit records. Boundaries: browser↔gateway, gateway↔gRPC service, Python↔C ABI, gateway↔SQLite, and gateway↔Azure inference.

| Threat | Implemented mitigation | Remaining limitation |
|---|---|---|
| Viewer attempts access mutation | C policy denies viewers; gateway supplies current role | No real tenant or external IAM integration |
| Operator promotes themselves | Self changes and operator role changes denied | Bootstrap administrator is still a privileged local account |
| Last admin removed | Current active-admin count re-evaluated in write transaction | Managed admin records need not have login credentials; this is record-level policy |
| Session theft | Random opaque token, stored digest, HttpOnly, SameSite, configurable Secure, expiry | No MFA/device binding; local HTTP only for loopback development |
| Cross-site mutation | Same-origin architecture, Origin allowlist and CSRF token | Deployment must set exact origin and HTTPS settings correctly |
| SQL injection | Fixed statements with bound values | SQLite file access bypasses application controls |
| Stale or replayed proposal | Version, status, ownership and expiry rechecked atomically | No cross-region/distributed consistency |
| AI prompt injection | No tools; fixed target; strict output schema; C policy; explicit human confirmation | Rationale can still be misleading and users may approve a poor suggestion |
| Unauthenticated direct gRPC | Constant-time shared-token check; private network/loopback | Plaintext internal channel; no workload identity or mTLS |
| C memory corruption | Small bounded structs, no dynamic allocation, strict compiler flags and sanitizers | Tests are not formal verification; ABI drift must be tested |
| Credential leakage | Untracked .env; server-only secrets; no custom sensitive telemetry | Manual screenshots/log changes can still leak secrets |
| Brute-force or cost abuse | Login, AI and event limits; bounded bodies; gRPC deadline | Per-process rate limit; no global ingress DoS protection |
| Audit manipulation | Audit is committed with mutation; no edit/delete API | Database owner can modify it; not append-only external storage |
| Feature flag used to bypass RBAC | Flags never authorize mutations; AI kill switch rechecked | Client-visible flags are not secret |

## Residual scope

The application has one workspace. It should not be called multi-tenant. Synthetic records and bootstrap authentication are suitable for demonstration. Sessions expire after one hour; proposals after ten minutes. New identity records have no credentials and cannot sign in. No password-reset flow is exposed. Do not open the app to untrusted real users without addressing the deployment and identity gaps.

The protection against the last active administrator refers to the role/state data model. A true identity provider must additionally preserve a usable recovery administrator and recovery mechanisms. The repository does not claim that broader guarantee.

## Verification priorities

For future changes, test authorization at apply time, actor suspension/demotion between draft and apply, simultaneous final-admin changes, provider failures, malformed model outputs, cancelled/replayed proposals, expired sessions and sensitive-field exclusion. Commission an independent security review before production use.
