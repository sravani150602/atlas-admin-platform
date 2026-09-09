# C engine: implementation and extension guide

Build with `make all`; output is `build/libatlas.so`. `make test` links the same implementation into a native test executable. The implementation uses C11, stack-allocated structs and bounded `snprintf`; it performs no allocation, filesystem I/O or network I/O.

## ABI

`atlas_request` contains seven `int` fields, in this exact order: actor_role, is_self, target_role, target_active, active_admins, action, requested_role. `atlas_decision` contains allowed, risk, and a 160-byte reason buffer. The Python adapter mirrors the field order with `ctypes.c_int` and `ctypes.c_char * 160`.

| Concept | Mapping |
|---|---|
| Roles | viewer=0; operator=1; admin=2 |
| Actions | suspend=0; restore=1; change_role=2 |
| Risk | low=0; medium=1; high=2 |
| evaluate return value | 0 means a decision was written; -1 means output pointer is null |
| authorization | inspect `decision.allowed`; return code 0 does not imply authorization |

Bad inputs deny by default. An absent output pointer returns -1 because there is nowhere to put an error. Risk is high for role changes or administrator targets, medium for other modeled changes. No supported mutation is classified low risk.

## Rule order

Validate all enum/boolean/count inputs → deny viewers → deny self changes → limit operators → preserve the last active administrator → reject no-op transitions → allow with required confirmation.

| Actor | Viewer/operator target suspend/restore | Admin target suspend/restore | Role change |
|---|---|---|---|
| Viewer | Denied | Denied | Denied |
| Operator | Allowed if change has an effect | Denied | Denied |
| Administrator | Allowed | Allowed subject to last-admin and self rules | Allowed subject to last-admin and self rules |

The engine assumes input describes authenticated, current state. It cannot verify session validity, tenant boundaries or database freshness itself. Those are gateway responsibilities. The engine deliberately does not trust client-provided role or active-admin count.

## Cohort algorithm

`atlas_flight(subject, flag, percent)` computes 32-bit FNV-1a over `flag + ':' + subject`. Unsigned 32-bit overflow is defined in C. An identity is enabled when `hash % 100 < percent`. The same subject and flag always get the same bucket. Raising the percentage includes all earlier buckets; 0 disables everyone and 100 enables everyone.

This hash is not cryptographic. The gateway uses server-assigned identity IDs, and feature flags never substitute for authorization. Cohort keys are bounded and reject NUL in the transport adapter. Invalid percentage or empty/null keys deny.

## Adding a new operation

1. Extend the documented enum contract and validation.
2. Specify both allowed and denied role/target combinations.
3. Add native tests including invalid input and no-op cases.
4. Update the protobuf/gateway action mapping and strict input schema.
5. Add transactional application behavior and audit payload.
6. Update UI labels and confirmation text.
7. Regenerate bindings and run API integration tests to catch ABI/contract drift.

Do not place SQL, provider calls or UI strings in this library. Keep C error reasons safe to expose. If the ABI changes, update both structs and version information together.
