# Five-minute interview demonstration

## 0:00 — Explain the project accurately

“Atlas is my independent portfolio project for identity-style administration. The authorization and rollout engine is written in C. React and TypeScript provide a reusable UX package, with a Python gateway and gRPC adapter. It operates on synthetic local identities.”

Show the README scope table before suggesting any production usage or organization-wide adoption.

## 0:30 — Directory and shared components

Sign in, search for an identity and explain the selected target. Point to consistent buttons, badges, panels and feedback. Show `packages/ux` and the imports in both `main.tsx` and `Review.tsx`.

## 1:15 — Safe manual change

Preview a suspension. Explain that a proposal is persisted with a target version and expiry. Close the dialog, open Access review and review the same proposal there. Confirm it and show the audit before/after state.

## 2:15 — AI-assisted proposal

In demo mode, explicitly say it is a deterministic interpreter. Enter “Change role to operator.” Show the target, action, rationale, source and risk. If Azure is configured and has been tested, explain which deployment is used; do not call demo rules a model.

## 3:00 — Policy and failure cases

Try to modify the signed-in administrator and show the denial. Explain the C policy's fail-closed rules and why UI-only checks are insufficient. Describe the stale-proposal integration test. Turn AI rollout to zero and explain why pending AI proposals are also denied on apply.

## 4:00 — Engineering evidence

Show test results, the protobuf schema, transaction boundaries and telemetry design. Explain that gRPC transport is in Python while policy is native C. Distinguish audit accountability from aggregate UX measurement.

## 4:45 — Tradeoffs and next steps

Discuss SQLite single-writer simplicity versus managed-database scalability, local auth versus OIDC, a shared secret versus mTLS, and synthetic UX evaluation versus real usability evidence.

## Questions to prepare for

- Why use C here? Predictable small policy ABI, explicit validation and native testability; transport remains in mature libraries.
- What prevents AI from granting admin access automatically? No mutation tools, strict schema, C role checks and explicit apply confirmation.
- What if permissions change after a draft? Apply rereads actor/target, checks version and re-evaluates policy inside a transaction.
- How do cohorts stay stable? Hash server identity ID plus feature key and compare a deterministic bucket against rollout percentage.
- Is this Entra integrated? No. It is an identity-style portfolio system with documented future integration work.
- Did this improve task time by a percentage? No study has been conducted. Explain the measurement plan instead of inventing a number.
- What did you personally learn/change? Review the code, run it, make a feature change and explain your decisions honestly, including AI assistance.
