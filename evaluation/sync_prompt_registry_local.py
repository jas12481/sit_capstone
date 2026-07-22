"""
One-time (re-runnable) sync: copies every prompt + full version history from the Databricks
Unity-Catalog-backed Prompt Registry (source of truth, written by register_prompts.py /
prompt_advisor.py) into a local, self-hosted MLflow tracking server. Purely a *viewing*
convenience — this Databricks Free Edition workspace has no browsing UI for its Prompt Registry
(confirmed: Catalog Explorer's Models tab and the experiment's tabs neither show one), but a
locally-hosted MLflow server (backend-store-uri = sqlite, no Unity Catalog involved) does render
a normal "Prompts" page, since prompts there are plain registered-model-style objects with no
catalog/schema requirement.

The local copy is a mirror, not a second source of truth — always register new/updated prompts
against Databricks first (register_prompts.py / prompt_advisor.py), then re-run this script to
refresh the local mirror before a demo.

Prerequisites:
    A local MLflow tracking server must already be running, e.g.:
        mlflow server --backend-store-uri sqlite:///mlflow_local_registry/mlflow.db \\
            --default-artifact-root "$(pwd)/mlflow_local_registry/artifacts" \\
            --host 127.0.0.1 --port 5001

Usage:
    python evaluation/sync_prompt_registry_local.py --local-uri http://127.0.0.1:5001
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / "mcp_server" / ".env")

SOURCE_CATALOG_SCHEMA_PREFIX = "workspace.default."


def _init_databricks():
    import mlflow
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    if not host or not token:
        raise RuntimeError("DATABRICKS_HOST / DATABRICKS_TOKEN missing from mcp_server/.env")
    os.environ["DATABRICKS_HOST"] = host
    os.environ["DATABRICKS_TOKEN"] = token
    mlflow.set_tracking_uri("databricks")


def _read_all_from_databricks() -> dict[str, list[tuple[int, str, str, dict]]]:
    """Returns {local_name: [(version, template, commit_message, tags), ...]} sorted ascending
    by version. commit_message/tags are carried through so the local mirror's UI can actually
    show what changed between versions, not just the raw text — a prompt registered with a
    descriptive commit_message (e.g. "v1.2 update: ...") is meaningless in the local viewer if
    that message never makes it across."""
    import mlflow.genai as genai
    from mlflow.tracking import MlflowClient

    _init_databricks()
    client = MlflowClient()
    remote_prompts = genai.search_prompts(filter_string="catalog = 'workspace' AND schema = 'default'")

    out: dict[str, list[tuple[int, str, str, dict]]] = {}
    for p in sorted(remote_prompts, key=lambda p: p.name):
        local_name = p.name[len(SOURCE_CATALOG_SCHEMA_PREFIX):] if p.name.startswith(SOURCE_CATALOG_SCHEMA_PREFIX) else p.name
        versions = sorted(v.version for v in client.search_prompt_versions(p.name))
        entries = []
        for v in versions:
            loaded = genai.load_prompt(p.name, version=v)
            entries.append((v, loaded.template, loaded.commit_message or "", loaded.tags or {}))
        out[local_name] = entries
    return out


def _write_all_to_local(data: dict[str, list[tuple[int, str, str, dict]]], local_uri: str) -> None:
    import mlflow
    import mlflow.genai as genai

    mlflow.set_tracking_uri(local_uri)

    total_versions = 0
    for i, (name, entries) in enumerate(sorted(data.items()), start=1):
        for version, template, commit_message, tags in entries:
            genai.register_prompt(name=name, template=template, commit_message=commit_message, tags=tags)
            total_versions += 1
        print(f"  [{i}/{len(data)}] {name}  ({len(entries)} version(s) replayed)")
    print(f"\nDone. {len(data)} prompts, {total_versions} versions written to {local_uri}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mirror the Databricks Prompt Registry into a local MLflow server for demo browsing")
    parser.add_argument("--local-uri", default="http://127.0.0.1:5001", help="Tracking URI of the running local mlflow server")
    args = parser.parse_args()

    print(f"Reading full prompt + version history from Databricks (workspace.default)...")
    data = _read_all_from_databricks()
    print(f"Found {len(data)} prompts.\n")

    print(f"Writing to local server at {args.local_uri} ...")
    _write_all_to_local(data, args.local_uri)


if __name__ == "__main__":
    main()
