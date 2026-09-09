# Atlas — AI-Powered Admin Experience & Shared UX Platform

**A C-powered access policy engine with a React/TypeScript administration experience, reusable UX components, human-reviewed AI proposals, gRPC, OpenTelemetry, and Docker.**

**Project owner:** Sravani Elavarthi · Master of Science in Data Science, University of Maryland, College Park.

**Project context:** Independent portfolio project, created with AI-assisted development. The education line describes the owner's background; this is not represented as University of Maryland coursework, sponsored research, an official university deployment, or Microsoft work. Review and understand the implementation before presenting it as personal experience.

## What this project does

Atlas lets a workspace administrator browse synthetic managed identities, create identity records, preview access changes, and explicitly approve each change. Operators can suspend or restore non-administrator identities. Viewers can inspect the directory. AI can translate a short request into a structured proposal, but cannot execute a change.

The identity directory and access-review surface consume the same `@atlas/ux` package. They share buttons, status badges, panels, form controls, feedback, empty states, design tokens, and confirmation behavior. The result is a runnable demonstration of consistent administrative UX backed by enforceable server-side policy.

This repository **does not modify real Entra, Azure, or university accounts**. It manages its own SQLite records. “Identity/access-style” describes the product domain, not an integration with an external identity provider.

## Start here

| Goal | Read |
|---|---|
| Run it locally | [Local setup](#local-setup-linux-macos-or-wsl2) |
| Run containers | [Docker setup](#docker-setup) |
| Understand every layer | [Architecture](docs/ARCHITECTURE.md) |
| Explore endpoints and payloads | [API guide](docs/API.md) |
| Learn the C implementation | [C engine guide](docs/C_ENGINE.md) |
| Enable an actual AI model | [AI configuration](docs/AI.md) |
| Understand reusable frontend components | [Shared UX guide](docs/SHARED_UX.md) |
| Accessibility behavior and checks | [Accessibility](docs/ACCESSIBILITY.md) |
| Inspect traces and task metrics | [Observability](docs/OBSERVABILITY.md) |
| Evaluate deployment to Azure | [Azure guide](docs/AZURE.md) |
| Review risks and operational limits | [Threat model](docs/THREAT_MODEL.md), [Operations](docs/OPERATIONS.md) |
| Prepare an interview walkthrough | [Demo script](docs/DEMO.md), [Resume claims](docs/RESUME.md) |
| Publish the repository | [GitHub publishing](docs/GITHUB.md) |
| See what was verified | [Verification report](docs/VERIFICATION.md) |

## Scope and evidence

| Requested capability | Implementation | Boundary |
|---|---|---|
| C implementation | C11 role policy, transition checks, privilege risk, deterministic feature cohorts | The full web stack is not pure C; React/TypeScript and Python handle their respective layers |
| React + TypeScript | Responsive identity directory, review queue, audit activity, rollout controls | One application with distinct admin/review surfaces; not multiple independently deployed products |
| Shared UX platform | Separately built workspace package with JavaScript, declarations, and shared stylesheet | Locally reusable npm package; not published to npm |
| Secure admin interface | Server-side sessions, CSRF, role checks, proposal ownership, expiry, optimistic concurrency, last-admin protection | Portfolio-grade local auth; no SSO/MFA/tenant isolation |
| AI-assisted actions | Deterministic demo interpreter and configurable Azure OpenAI client | Demo mode uses rules; Azure mode needs credentials and was not live-tested here |
| Human approval | Every manual/AI change is a proposal, followed by an explicit confirmation request | One actor reviews their own proposal; not two-person approval |
| gRPC | Protobuf contract, Python generated server/client, authenticated internal RPC to C via ctypes | C implements policy; Python implements the transport adapter |
| Feature flighting | C FNV-1a stable cohort assignment and versioned persisted rollout configuration | No statistical experimentation platform |
| OpenTelemetry | FastAPI and gRPC instrumentation, AI spans, allowlisted UX events and task-duration metrics | Export requires collector; default local mode makes no external export |
| Accessibility | Semantic controls, labelled inputs, visible focus, native modal, live feedback, axe and keyboard tests | Automated checks are not WCAG certification |
| Docker | Multistage nonroot image, Compose app/policy/collector/Jaeger | Docker engine was unavailable for local execution during generation |
| Azure | Container Apps Bicep evaluation template and Azure AI configuration | Not deployed; evaluation data is ephemeral |
| Task completion/support outcomes | Measurement design and instrumented task events | No measured productivity improvement or reduced support volume is claimed |
| Design/product collaboration | Written product rationale and usability-study plan | No claim of working with an actual product/design team |

## Why there are three languages

The request combines “in C” with a React/TypeScript UX platform. Atlas puts the policy engine in C and keeps the requested web technology for the interface. Python provides the gRPC adapter, HTTP service, SQLite persistence, session handling and telemetry.

This keeps authorization rules readable and unit-testable in C without implementing an HTTP/2 stack, JSON parser, password system, or browser UI from scratch in C. See the [C ABI](engine/policy.h) and [adapter](services/policy/server.py) to inspect the boundary. This is a **C-powered full-stack project**, not an all-C application.

## Local setup (Linux, macOS, or WSL2)

Prerequisites:

- Python 3.12, including `venv` and pip.
- Node.js 22 and npm.
- C compiler (`gcc` or `clang`) and Make.
- Git for version control. A GitHub account is only needed to publish.
- Chromium installed by Playwright if running the browser suite.

On Windows, run these commands inside WSL2, or use Docker Desktop. The native build creates a Linux/macOS-style shared library and is not a Windows MSVC build.

From the extracted repository directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock.txt
npm ci
make all
make proto
npm run build
python scripts/setup.py
python scripts/dev.py
```

Open **http://localhost:5173**. The setup script writes a unique password and service token into your local `.env`, with restrictive file permissions. Open that file locally and use `ADMIN_EMAIL` and `ADMIN_PASSWORD` to sign in. Do not paste credentials into an issue, commit, chat, or screenshot.

`scripts/dev.py` loads simple `KEY=value` lines from `.env`; do not add shell expressions or quotes. It starts the policy service, HTTP gateway, and Vite. Press Ctrl+C once to stop all three. Ports are 50051 (internal gRPC), 8000 (API), and 5173 (frontend). The Vite proxy forwards `/api` to the gateway so the browser uses a single origin.

To serve the production frontend locally after a build:

```bash
python scripts/dev.py --production
```

Open **http://127.0.0.1:8000**. The launcher sets the matching local origin in this mode. `--production` here means serving the compiled assets; it does not turn the portfolio app into a hardened production IAM service.

### First-use walkthrough

1. Sign in with the bootstrap admin credentials.
2. Search for Priya Rao and choose **Manage**.
3. Choose **Suspend access**, then **Preview manual change**.
4. Review the selected identity, action, risk and expiry. Choose **Go back** to leave the proposal pending, or **Confirm change** to apply.
5. Open **Access review** to inspect, apply, or cancel your pending proposals.
6. Open **Audit activity** to see the actor, target, timestamp and before/after state.
7. Select an identity and enter **Change role to operator** in the assistant to test the deterministic demo mode.
8. In **Feature rollout**, set AI-assisted proposals to 0%. AI drafting and applying existing AI proposals are disabled immediately on subsequent server checks.

### Seeded identities

| Identity | Role | Initial state | Can sign in initially? |
|---|---|---|---|
| Workspace administrator | admin | active | Yes, with your generated password |
| Jordan Lee | operator | active | No; managed demonstration record |
| Priya Rao | viewer | active | No; managed demonstration record |
| Morgan Chen | viewer | suspended | No; managed demonstration record |
| Alex Rivera | viewer | active | No; managed demonstration record |

All seed email domains use `example.test`. Adding an identity creates a managed record, not a password or invitation. This distinction is visible in the success message. Set `SEED_DEMO=false` before initializing a fresh database for only the bootstrap administrator.

## Docker setup

Generate `.env` as above, then:

```bash
docker compose up --build
```

Open **http://localhost:8000**. The gateway's origin is set to that address in Compose. Open Jaeger at **http://localhost:16686** for traces. The Collector exposes Prometheus-format metrics at **http://localhost:8889/metrics**.

Compose uses a named volume for the database. `docker compose down` keeps that volume. `docker compose down -v` permanently deletes it; do not use `-v` unless you intend to reset the local data. The database contains sessions and managed identity records and should be treated as sensitive.

The policy service has no published host port. Gateway, collector, and Jaeger published ports bind to loopback. Do not change those bindings to a public interface without reviewing the threat model.

## Environment reference

| Variable | Purpose | Default/example |
|---|---|---|
| `ADMIN_EMAIL` | Bootstrap login email, used only on first database creation | `admin@example.test` |
| `ADMIN_PASSWORD` | Bootstrap password, at least 14 characters | Generated by setup |
| `POLICY_TOKEN` | Shared internal service credential, at least 32 characters | Generated by setup |
| `POLICY_ADDRESS` | Gateway's gRPC target | `127.0.0.1:50051` |
| `POLICY_BIND` | gRPC listener | `127.0.0.1:50051` |
| `DATABASE_PATH` | SQLite file | `data/atlas.db` |
| `APP_ORIGIN` | Exact allowed browser origin | `http://localhost:5173` |
| `COOKIE_SECURE` | HTTPS-only session cookie | `false` locally; `true` for HTTPS |
| `SEED_DEMO` | Add synthetic records on first initialization | `true` |
| `AI_PROVIDER` | `demo` or `azure` | `demo` |
| `AZURE_OPENAI_ENDPOINT` | Azure resource root HTTPS URL | No `/openai` suffix |
| `AZURE_OPENAI_API_KEY` | Azure resource API key | Empty until configured |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | Empty until configured |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP HTTP collector root URL | Unset locally; `http://collector:4318` in Compose |

Changing `ADMIN_PASSWORD` after the database exists does not reset the stored password. See the operations guide. Never put AI keys in `VITE_*` variables or frontend source.

## Verification commands

```bash
make test
make sanitize
python -m pytest tests/test_api.py -q
npm run check
npx playwright install --with-deps chromium
npm run test:e2e
```

The API tests launch a real gRPC process and compile-time C shared library integration, using an isolated temporary SQLite database. Browser tests launch the actual services against a disposable database and compiled web assets. The test-only password is restricted to `scripts/dev.py --test`; normal startup never chooses it.

The C sanitizer suite uses AddressSanitizer and UndefinedBehaviorSanitizer. In restricted tracing sandboxes, LeakSanitizer may fail to inspect `/proc`; `ASAN_OPTIONS=detect_leaks=0 make sanitize` runs address and undefined-behavior checks without leak detection. Record that distinction when reporting results.

GitHub Actions runs the core checks and builds the container after publication. The workflow file is configuration, not evidence of a completed GitHub run. See [VERIFICATION.md](docs/VERIFICATION.md) for results actually observed during this build.

## Repository map

| Path | Responsibility |
|---|---|
| `engine/policy.h` | Public C structs, role/action/risk contract |
| `engine/policy.c` | Fail-closed policy decisions and deterministic rollout hashing |
| `engine/test_policy.c` | Policy, invalid input and cohort checks |
| `proto/policy.proto` | gRPC wire contract |
| `services/policy/server.py` | Authenticated gRPC transport and ctypes binding |
| `services/gateway/app.py` | HTTP routes, session/CSRF, proposal orchestration, audit and flags |
| `services/gateway/db.py` | Schema, transactions, initial identities and password hashing |
| `services/gateway/ai.py` | Demo interpreter and Azure inference adapter |
| `services/telemetry.py` | OpenTelemetry providers and exporters |
| `packages/ux/src/index.tsx` | Reusable accessible React primitives |
| `packages/ux/src/styles.css` | Shared design tokens and component styling |
| `apps/admin/src/main.tsx` | Login, directory, audit and rollout experience |
| `apps/admin/src/Review.tsx` | Second shared-component consumer: access review |
| `apps/admin/src/api.ts` | Typed HTTP client and allowlisted UX event helper |
| `apps/admin/src/style.css` | Product layout, responsive behavior and presentation |
| `tests/test_api.py` | Full policy/HTTP/database integration tests |
| `tests/ux.test.tsx` | Accessible naming, errors and disabled-action contracts |
| `tests/browser/admin.spec.ts` | Browser flow, focus, axe and mobile overflow checks |
| `scripts/setup.py` | Unique local secret generation |
| `scripts/dev.py` | Service launcher and test environment teardown |
| `scripts/publish-github.sh` | Optional private GitHub publication helper |
| `Dockerfile`, `compose.yaml` | App image and local multi-service environment |
| `observability/collector.yaml` | Trace and metric receiver/export pipelines |
| `infra/main.bicep` | Azure Container Apps evaluation deployment |
| `.github/workflows/ci.yml` | CI verification and container build |
| `requirements.txt` | Direct Python dependencies |
| `requirements.lock.txt`, `package-lock.json` | Resolved dependency versions |
| `docs/` | Design, operations, API, test evidence and interview guides |

Build outputs, generated protobuf Python files, databases, secrets, and installed dependencies are intentionally excluded. They are recreated by the commands above.

## Product rationale

Administrators need to understand who is affected before changing access. Atlas centers the identity directory and keeps the assistant adjacent to the chosen identity. AI never selects a hidden target. The selected identity is bound by the server request; the model only drafts an action and role. A review dialog explains the action, source, risk and time limit.

Consistency is enforced through shared primitives rather than copied markup. Accessible labels, feedback behavior, disabled states and confirmation focus are component responsibilities. Deterministic feature cohorts support controlled exposure without letting a frontend flag bypass authorization.

Telemetry is intentionally separated from audit. Audit records support accountability inside this demonstration; aggregate UX events support a future usability study. No measured productivity or support-volume claim should be inferred from the presence of instrumentation.

## License and attribution

MIT © 2026 Sravani Elavarthi. See [LICENSE](LICENSE).

React, FastAPI, gRPC, OpenTelemetry, Lucide, SQLite and other dependencies retain their respective licenses. No Microsoft, university or employer logos are used. Product names identify integration technologies only. See [SOURCE_NOTES.md](docs/SOURCE_NOTES.md) for official technical references.
