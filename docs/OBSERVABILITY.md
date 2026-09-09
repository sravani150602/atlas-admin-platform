# Observability and UX measurement

## What is instrumented

The gateway starts an OpenTelemetry tracer provider and a meter. FastAPI and gRPC instrumentation produce HTTP/RPC spans, including propagation between gateway and policy service. An explicit `ai.draft` span marks provider interpretation. The C function itself has no separate exporter or direct SDK dependency; its execution occurs inside the instrumented RPC server span.

When `OTEL_EXPORTER_OTLP_ENDPOINT` is unset, there is no external exporter. When configured, batch traces and periodic metrics use OTLP HTTP. The Compose Collector forwards traces to Jaeger and exposes Prometheus-format metrics. The exporter interval means metrics are not necessarily visible immediately.

| Metric | Type | Labels | Meaning |
|---|---|---|---|
| atlas.ux.events | Counter | event.name, surface | Accepted allowlisted frontend events |
| atlas.ux.task.duration | Histogram, ms | event.name, surface | Duration submitted at completion/failure |

The frontend emits task_started when selecting an identity or reviewing a proposal, proposal_created after a successful draft, and task_completed after a successful apply. API support for task_failed exists but the current UI does not emit it. Event data is best-effort and client-supplied, so it is unsuitable for billing, security decisions or authoritative usage counts. A failed telemetry request never blocks a user action.

## Local inspection

1. Start `docker compose up --build`.
2. Perform a login, manual draft and apply.
3. Open `http://localhost:16686`, choose `atlas-gateway`, and inspect the HTTP → gRPC trace.
4. Inspect `http://localhost:8889/metrics` after the periodic export interval.
5. Trigger a denied operation and verify that it produces an error response and no identity mutation.

Collector and Jaeger execution requires Docker and was not verified in this environment. The API integration tests do exercise the instrumented application without an exporter.

## Privacy

Custom metrics carry only allowlisted event and surface labels. No prompt, email, user ID, session token or cookie is intentionally attached to custom telemetry. Do not enable HTTP header capture for Authorization/Cookie/CSRF headers. Default server spans can still contain URL/route information; use collector redaction and access controls appropriate to the deployment. Audit and proposal data contain identity IDs and rationale, so they are separate protected application data.

## Measuring the résumé outcome honestly

Instrumentation alone does not prove improved completion speed or reduced support friction. Use a within-subject study with counterbalanced manual and assisted tasks on synthetic identities. Define success as the correct final access state, record completion time and corrections, and collect perceived ease and confidence. Predefine exclusions and report both accuracy and timing.

Task time starts on target selection and ends at successful apply in the current directory flow. The review-surface timer starts when opening an existing proposal. These definitions are different; do not merge their distributions without labeling the surface. Sessions abandoned before apply are missing from completion metrics. More complete funnel analysis needs session-scoped anonymous task IDs and abandonment handling, designed with privacy review.

A proposed comparison can use median duration, interquartile range, correct-task completion rate and error count. Do not put a percentage on the résumé until a reproducible study produces it. Support friction could be studied through observed help requests or support tickets, but this project has no collected support data.
