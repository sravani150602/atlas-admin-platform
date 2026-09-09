# Security posture and reporting

This is an independent portfolio implementation for synthetic identities. It is not an identity provider, Microsoft Entra integration, or audited production IAM system. The local API changes this application's records only.

Report vulnerabilities privately to the repository owner using GitHub private vulnerability reporting after it is enabled. If unavailable, request a private contact route without publishing exploit details or secrets.

Implemented controls: scrypt password hashing with per-account salt; opaque server-side sessions stored as hashes; HttpOnly/SameSite cookies; configurable Secure cookies; Origin and CSRF validation; same-origin API; schema and size validation; role checks in C; self-change denial; last-active-admin protection; transactionally revalidated proposals; expiry, ownership and replay checks; session revocation on access changes; fixed SQL statements with bound values; protected internal gRPC credential; bounded message size; no external gRPC port in Compose; nonroot containers; restrictive response headers; rate limits for login, AI and events.

Known limitations: no OIDC/Entra SSO, MFA, password reset or account invitation; only bootstrap admin has a password; SQLite single-replica persistence; no organization/tenant isolation; in-memory rate limiting; internal plaintext gRPC (loopback/Compose network only); no immutable external audit store; no penetration test or compliance certification; Azure configuration is an evaluation template with ephemeral data; image and dependency versions need normal maintenance. Review `docs/THREAT_MODEL.md` before considering external use.

Do not expose development services, collector ports, or Jaeger publicly. For a deployment with real data, replace local authentication with a vetted OIDC integration, use a managed transactional database, configure TLS/mTLS and secret management, enforce tenant boundaries, ship audit records to protected storage, and perform a security review.
