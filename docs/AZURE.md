# Azure evaluation deployment

## Included, but not deployed

`infra/main.bicep` defines a Log Analytics workspace, Container Apps environment, and one Container App containing gateway and policy containers. The image is shared by both containers. HTTP ingress requires HTTPS, policy listens only on loopback, and secrets are passed through Container Apps secret references. The maximum replica count is one.

This template is an **evaluation starting point**. No Azure credentials were available during generation, so Bicep deployment, container startup on Azure, cost, region availability and live Azure AI inference were not verified. Validate the template and review a what-if result in your own subscription before creating resources.

## Data warning specific to this template

The `EmptyDir` data volume is ephemeral. A replica replacement can reset identities, sessions, proposals and audit data. This is deliberate to avoid presenting network-mounted SQLite as a production database. Do not put real identity information into this evaluation deployment. Before durable use, migrate to a managed transactional database and implement migrations and backups; do not simply scale replicas over SQLite.

The mount must also be writable by UID 10001. Container platform volume ownership can vary; inspect startup logs and readiness during evaluation. Do not solve permission failures by making the entire container privileged.

## Build and deploy procedure

1. Install Azure CLI with Bicep support, Docker, and authenticate to your own Azure subscription.
2. Build the image with `docker build -t YOUR-REGISTRY/atlas-admin:1.0.0 .`.
3. Push it to a registry the Container App can pull. The provided template assumes a publicly pullable image. For a private registry, first add an appropriate managed identity and registry configuration; those are not included.
4. Pin the evaluated image by digest for repeatability.
5. Generate independent strong admin and policy secrets. Do not reuse committed test credentials.
6. Validate with `az bicep build --file infra/main.bicep` and run an Azure deployment what-if with your chosen parameters.
7. Pass secure parameters through your approved secret mechanism or a restrictive, untracked parameter file. Do not paste secrets into command history or source control.
8. Deploy the reviewed template to a dedicated evaluation resource group.
9. Confirm HTTPS login, `/api/ready`, draft/apply, audit and cookie behavior at the returned URL.
10. Delete the evaluation resource group when finished to stop ongoing charges.

Example validation shape, with a separately prepared secret-bearing parameter file:

```bash
az deployment group what-if --resource-group YOUR-EVALUATION-GROUP \
  --template-file infra/main.bicep --parameters @/secure/path/atlas.parameters.json

az deployment group create --resource-group YOUR-EVALUATION-GROUP \
  --template-file infra/main.bicep --parameters @/secure/path/atlas.parameters.json
```

The file must provide image, adminPassword and policyToken; review optional parameters in the template. The generated FQDN is used for `APP_ORIGIN`. A custom domain requires updating that exact origin as well.

## Observability on Azure

The template configures container logs through Log Analytics. It does not deploy the local Collector/Jaeger stack or configure Application Insights exports. To receive OpenTelemetry on Azure, add an authenticated collector/exporter route and set the OTLP endpoint. Container logs alone are not equivalent to the distributed trace pipeline.

## Production work still required

Replace bootstrap auth with validated Entra/OIDC flows and tenant-aware authorization; use managed database transactions; add migrations; durable protected audit storage; managed identity for secrets and registry; scoped ingress; distributed rate limiting; backup/restore drills; TLS/mTLS across any non-loopback service boundary; dependency and image scanning; alerts; data retention; incident response and capacity tests.

These are not claimed as completed capabilities. See [SECURITY.md](../SECURITY.md).
