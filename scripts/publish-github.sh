#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v gh >/dev/null || { echo 'Install the GitHub CLI and run gh auth login first.' >&2; exit 1; }
gh auth status
repo_name="${1:-atlas-admin-platform}"
[[ "$repo_name" =~ ^[a-zA-Z0-9._-]+$ ]] || { echo 'Use a repository name, without a URL or owner prefix.' >&2; exit 1; }
if ! git rev-parse --git-dir >/dev/null 2>&1; then git init -b main; fi
if git remote get-url origin >/dev/null 2>&1; then
  echo 'An origin remote already exists. Review it and push manually; this helper will not replace it.' >&2
  exit 1
fi
git var GIT_AUTHOR_IDENT >/dev/null
git add .
if ! git diff --cached --quiet; then git commit -m 'Build Atlas C policy engine and shared admin UX platform'; fi
gh repo create "$repo_name" --private --source . --remote origin --push \
  --description 'C-powered identity administration with shared React UX, reviewed AI proposals, gRPC and OpenTelemetry'
gh repo view --json url --jq .url
