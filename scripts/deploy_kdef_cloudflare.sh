#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="${CF_PAGES_PROJECT:-kdef}"
BRANCH_NAME="${CF_PAGES_BRANCH:-main}"
SKIP_INSTALL="${SKIP_INSTALL:-false}"

export CLOUDFLARE_API_TOKEN="${CF_API_TOKEN:-${CLOUDFLARE_API_TOKEN:-}}"

if [[ -z "${CLOUDFLARE_API_TOKEN}" ]]; then
  echo "Error: missing CF_API_TOKEN or CLOUDFLARE_API_TOKEN"
  exit 1
fi

if [[ -z "${CF_ACCOUNT_ID:-}" ]]; then
  echo "Error: missing CF_ACCOUNT_ID"
  exit 1
fi

cd "$ROOT_DIR"

echo "==> Building Quartz site"
if [[ "$SKIP_INSTALL" != "true" ]]; then
  npm ci
fi
npx quartz build

echo "==> Deploying public/ to Cloudflare Pages"
npx wrangler pages deploy public/ \
  --project-name "$PROJECT_NAME" \
  --branch "$BRANCH_NAME" \
  --commit-dirty=true

echo "Done: deployed to project '$PROJECT_NAME' branch '$BRANCH_NAME'"
