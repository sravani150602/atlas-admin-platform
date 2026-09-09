# AI configuration and boundaries

## Demo mode

`AI_PROVIDER=demo` uses a deterministic keyword interpreter. It does not contact a language model. The interface labels it **Demo assistant**, and each proposal stores `demo (rules, no model)` as its provider.

Try one simple operation: `Suspend access`, `Restore access`, or `Change role to operator`. This mode is a reproducible test facility, not evidence of AI inference quality. Do not use it to interpret complex or multi-step instructions.

## Azure mode

Create an Azure OpenAI resource and a chat-capable deployment supporting JSON-object responses. Configure the server environment:

```dotenv
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com
AZURE_OPENAI_API_KEY=YOUR-RESOURCE-KEY
AZURE_OPENAI_DEPLOYMENT=YOUR-DEPLOYMENT-NAME
```

These are placeholders, not actual credentials. Restart the gateway after configuration. The adapter calls `/openai/v1/chat/completions` using `api-key` authentication, the deployment name as model, and `response_format: {type: json_object}`. The endpoint must be an HTTPS resource root. Model capabilities vary; choose a compatible deployment and confirm the endpoint against the official Azure documentation.

No particular model version is promised. The repository does not claim access to GPT-6 or another unavailable model. Configuration, model availability, access permissions, region, billing, and quotas belong to the user's Azure account.

## Data and safeguards

- Only the typed prompt and fixed system instruction go to the provider; the adapter does not automatically send the identity directory or target email.
- A user can still type personal information into a prompt. The UI asks them not to; this is not an automatic DLP system.
- The target ID is selected in the interface and passed separately to the server. Model output cannot switch it.
- The provider receives no mutation tools and no session or policy credential.
- Only an allowlisted action, role and bounded rationale are accepted. Malformed or ambiguous output is rejected.
- All proposed changes pass C policy, explicit review, expiry and version checks.
- Provider outages do not trigger silent demo fallback; the API returns an error and manual controls remain available.
- Azure keys stay on the server and are excluded from source control.
- Prompts are not stored in the database or attached to telemetry spans. Rationale is stored with the proposal; it may reflect user input, so treat proposal data as sensitive.

## Evaluation protocol

Build a synthetic prompt suite with unambiguous requests, ambiguity, multiple actions, privilege escalation, instruction injection, unrelated text, long input, malformed responses and provider timeout. Measure valid-schema rate, intended-action agreement, policy denial behavior, and user corrections. The current integration tests exercise deterministic demo output and the policy/kill-switch path; they do not measure a live model's accuracy.

Human approval reduces accidental execution risk but does not make an incorrect recommendation correct. Review the target and action rather than trusting fluent rationale.
