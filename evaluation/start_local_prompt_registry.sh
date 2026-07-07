#!/usr/bin/env bash
# Starts the self-hosted local MLflow server backing the Prompt Registry mirror
# (see evaluation/sync_prompt_registry_local.py for how it's populated).
# Run from anywhere — always resolves paths relative to the repo root.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

source venv/bin/activate

exec mlflow server \
  --backend-store-uri "sqlite:///mlflow_local_registry/mlflow.db" \
  --default-artifact-root "$REPO_ROOT/mlflow_local_registry/artifacts" \
  --host 127.0.0.1 \
  --port 5001
