# Contributing

Use the local setup in README.md. Start a branch with a focused change. Keep authorization and flighting rules in C, transport in the Python adapter, and shared visual primitives in `packages/ux`.

Before a pull request, run `make test`, `make sanitize`, `.venv/bin/python -m pytest tests/test_api.py -q`, `npm run check`, and `npm run test:e2e`. If a required check cannot run, explain the specific limitation. Generate protobuf stubs after changing the contract. Never edit generated stubs directly.

For a permission change, add a denial test and a stale-state test. For a component API change, update consumers in both the directory and review surface. For a database change, design an explicit versioned migration; `CREATE TABLE IF NOT EXISTS` does not migrate an existing table. Keep errors helpful and free of secrets.

Use plain-language commit and PR descriptions. Describe the user problem, change, and evidence. Obtain consent before collecting real usability-study data. Do not commit `.env`, a database, real identities, access tokens, or raw AI prompts.

Accessibility is part of the component contract. Preserve labels, native semantics, visible focus, focus return, sufficient contrast, keyboard interaction, and reduced-motion behavior.
