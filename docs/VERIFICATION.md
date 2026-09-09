# Verification report

Recorded for the generated 1.0.0 implementation on 2026-09-09. Results below describe checks actually run in the local Linux workspace; they are not GitHub Actions or Azure deployment results.

| Check | Result | Evidence and scope |
|---|---|---|
| Native C compile | Passed | C11 with Wall, Wextra, Werror, Wpedantic and stack protector |
| Native policy tests | Passed | Authorization, invalid inputs, self/last-admin rules, role changes and deterministic flighting |
| 25% cohort sample | 2,476 of 10,000 enabled | Synthetic IDs; repeat assignment deterministic; not a UX outcome |
| AddressSanitizer and UBSan | Passed | Leak detection disabled because sandbox /proc inspection is restricted |
| LeakSanitizer | Not run successfully | Initial run failed due to environment introspection restriction, not a reported code leak |
| API/gRPC/C/SQLite integration | 18 tests passed | Real policy subprocess; temporary database; session, CSRF, policy, stale/expired/replayed proposals, AI kill switch, flag conflict, size and rate limits |
| Shared UX unit tests | 3 tests passed | Accessible descriptions, live error role and disabled-action behavior |
| TypeScript and production build | Passed | Shared package emitted declarations; app built with Vite |
| Full browser workflow | 1 scenario passed | Real services and compiled frontend; sign-in, draft, review, apply and audit |
| Automated accessibility | Passed on tested states | axe on login, directory, modal and feature rollout; no violations returned in those scans |
| Keyboard confirmation | Passed | Safe initial focus, Escape, and return focus |
| Mobile overflow | Passed | Feature rollout at 390×844 did not overflow document width |
| Docker/Compose execution | Not run | Docker executable/daemon unavailable |
| OpenTelemetry collector export | Not run | Collector/Jaeger stack requires Docker here; instrumented API itself was exercised |
| Azure Bicep compile/deployment | Not run | Azure CLI/Bicep and subscription credentials unavailable |
| Live Azure AI inference | Not run | No Azure endpoint/key/deployment supplied |
| GitHub Actions | Not run | Repository has not been pushed from this environment |
| Usability outcome study | Not performed | No measured task-time or support-friction improvement claimed |

## Issues discovered and resolved during verification

The first browser run discovered two React runtimes resolving through the workspace packages. Vite now explicitly deduplicates React and React DOM. A later keyboard check discovered that opening a modal while submission controls were disabled could lose the safe initial focus and invoking-control reference. The shared dialog now focuses its safe action when work completes and receives an explicit return-focus target from the workflow. The complete browser scenario passed after those fixes.

## Reproduction

Use the locked setup from README. Generate protobuf bindings, build the C library and frontend, then run the listed test commands. Browser tests use a disposable database and synthetic credentials. The HTML test report and traces are local build artifacts excluded from the source archive; they can contain session material and should not be published unredacted.

No statement here constitutes a penetration test, formal proof, WCAG certification, production-readiness review, live-cloud validation or personal employment evidence.
