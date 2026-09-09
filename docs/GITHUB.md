# Publishing to your GitHub

The project is prepared for the repository name **atlas-admin-platform**. GitHub publication requires an authenticated account with repository-creation and push permission. A local commit or ZIP file is not a published repository.

## With the GitHub CLI on your computer

1. Install Git and the GitHub CLI through their official instructions.
2. Run `gh auth login` and complete the browser/device flow. Do not send a password or access token in chat.
3. Confirm the account using `gh auth status`.
4. Review the source and `.gitignore`; no `.env`, database, installed dependencies or generated binaries should be tracked.
5. From this project directory, run `bash scripts/publish-github.sh`.

The helper creates a **private** repository by default and pushes `main`. It refuses to create a new remote if an origin already exists. If the repository name already exists in your account, the GitHub command will fail without overwriting it. Choose a different name by passing it as the first script argument after reviewing the intended destination.

The script uses your configured Git author identity. If missing, set your desired name and GitHub privacy email locally before running it. Do not invent an email identity. If the supplied archive contains no Git history, the script creates an initial commit of the project.

## After publishing

- Open the returned repository URL and confirm files and README render correctly.
- Inspect the Actions run; fix genuine failures before presenting its status as passing.
- Add a repository description: “C-powered identity administration with shared React UX, reviewed AI proposals, gRPC and OpenTelemetry.”
- Suggested topics: `c`, `react`, `typescript`, `grpc`, `opentelemetry`, `access-control`, `azure`, `portfolio`.
- Enable private vulnerability reporting if supported.
- Decide whether to make the repository public after reviewing attribution, license, and contents.

No GitHub token belongs in a script, README, environment example or issue. Use the CLI's credential workflow or an authenticated GitHub connection.
