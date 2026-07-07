"""
Lists everything currently in the MLflow Prompt Registry (workspace.default catalog/schema),
since this Databricks Free Edition workspace doesn't appear to expose a browsing UI for it
(checked Catalog Explorer's Models tab and the experiment's tab list — neither shows Prompts).

Usage:
    python evaluation/list_prompt_registry.py                 # list all names + version counts
    python evaluation/list_prompt_registry.py --show <name>   # print full template + version history for one prompt
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / "mcp_server" / ".env")


def _init_mlflow():
    import mlflow
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    if not host or not token:
        raise RuntimeError("DATABRICKS_HOST / DATABRICKS_TOKEN missing from mcp_server/.env")
    os.environ["DATABRICKS_HOST"] = host
    os.environ["DATABRICKS_TOKEN"] = token
    mlflow.set_tracking_uri("databricks")


def list_all() -> None:
    import mlflow.genai as genai
    from mlflow.tracking import MlflowClient

    client = MlflowClient()
    results = genai.search_prompts(filter_string="catalog = 'workspace' AND schema = 'default'")
    names = sorted(p.name for p in results)
    print(f"{len(names)} prompts registered under workspace.default:\n")
    for name in names:
        versions = client.search_prompt_versions(name)
        latest = max(v.version for v in versions)
        print(f"  {name}  (versions: {sorted(v.version for v in versions)}, latest: {latest})")


def show_one(name: str) -> None:
    import mlflow.genai as genai
    from mlflow.tracking import MlflowClient

    full_name = name if name.startswith("workspace.default.") else f"workspace.default.{name}"
    client = MlflowClient()
    versions = client.search_prompt_versions(full_name)
    if not versions:
        print(f"No prompt found: {full_name}")
        return

    for v in sorted(versions, key=lambda x: x.version):
        p = genai.load_prompt(full_name, version=v.version)
        print(f"\n{'=' * 70}\n  {full_name}  — version {v.version}\n{'=' * 70}")
        print(p.template)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the MLflow Prompt Registry (workspace.default)")
    parser.add_argument("--show", help="Print full template + version history for one prompt name")
    args = parser.parse_args()

    _init_mlflow()
    if args.show:
        show_one(args.show)
    else:
        list_all()


if __name__ == "__main__":
    main()
