"""
One-time MLflow Prompt Registry bootstrap.

Walks every dify-data/*.yml workflow, extracts each LLM node's prompt content via the
existing dsl_manager.parser.parse_workflow() (reused, not reimplemented — see CLAUDE.md:
node-extraction logic must only ever change in dsl_manager/), and registers it in the
MLflow Prompt Registry as {workflow_name}_{node_name}_v1.0, per PROJECT_CONTEXT.md §12's
naming convention.

Scope: LLM nodes only. code/agent node content is already version-tracked via
workflow_nodes / DSL Change Management (a separate governance mechanism) — the Prompt
Registry is specifically for LLM prompt text, per §12 ("version control for all system
prompts").

Usage:
    python evaluation/register_prompts.py              # register everything
    python evaluation/register_prompts.py --dry-run     # preview names/content, no MLflow calls
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from dsl_manager.parser import parse_workflow  # noqa: E402

DIFY_DATA_DIR = REPO_ROOT / "dify-data"
ENV_FILE = REPO_ROOT / "mcp_server" / ".env"

# This Databricks account's Prompt Registry is Unity Catalog-backed, which requires
# fully-qualified 3-level names (catalog.schema.name) — a bare name is rejected with a
# misleading "not a valid name" error that looks like a character-set complaint but is
# actually about the missing catalog/schema prefix (confirmed by testing a bare name vs.
# a qualified one against the live registry). "workspace.default" is the standard/default
# catalog+schema for a single-workspace Databricks account.
UC_CATALOG_SCHEMA = "workspace.default"


def _slug(value: str) -> str:
    """Lowercase, non-alnum -> underscore, collapse repeats. Matches the workflow_type
    convention already used in production (e.g. Dify's own default 'life_assess_claim')."""
    value = re.sub(r"[^0-9a-zA-Z]+", "_", value.strip())
    value = re.sub(r"_+", "_", value).strip("_")
    return value.lower()


def _init_mlflow() -> None:
    import mlflow
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    if not host or not token:
        raise RuntimeError("DATABRICKS_HOST / DATABRICKS_TOKEN missing from mcp_server/.env")
    os.environ["DATABRICKS_HOST"] = host
    os.environ["DATABRICKS_TOKEN"] = token
    mlflow.set_tracking_uri("databricks")


def register_all(dry_run: bool = False) -> None:
    if not DIFY_DATA_DIR.exists():
        raise FileNotFoundError(f"dify-data/ not found at {DIFY_DATA_DIR}")

    yaml_files = sorted(DIFY_DATA_DIR.glob("*.yml"))
    if not yaml_files:
        raise FileNotFoundError("No .yml files found in dify-data/")

    if not dry_run:
        _init_mlflow()
        import mlflow.genai as genai

    registered: list[str] = []
    failed: list[tuple[str, str, str]] = []

    for yaml_file in yaml_files:
        try:
            nodes = parse_workflow(yaml_file)
        except Exception as exc:
            failed.append((yaml_file.name, "<parse>", str(exc)))
            continue

        for node in nodes:
            if node["node_type"] != "llm":
                continue

            # PROJECT_CONTEXT.md §12 documents "{workflow_type}_{node_name}_v1.0" as the
            # unqualified name — "_v1_0" (not "_v1.0") because periods aren't allowed
            # within a single UC name segment, and UC_CATALOG_SCHEMA prefixes it into the
            # catalog.schema.name form Unity Catalog actually requires.
            unqualified = f"{_slug(node['workflow_name'])}_{_slug(node['node_name'])}_v1_0"
            prompt_name = f"{UC_CATALOG_SCHEMA}.{unqualified}"

            if dry_run:
                print(f"[DRY RUN] {prompt_name}  ({len(node['content'])} chars)")
                registered.append(prompt_name)
                continue

            try:
                genai.register_prompt(
                    name=prompt_name,
                    template=node["content"],
                    commit_message="Initial v1.0 bootstrap from dify-data/ DSL export",
                    tags={
                        "workflow_name": node["workflow_name"],
                        "node_name": node["node_name"],
                        "source_file": yaml_file.name,
                        "content_hash": node["content_hash"],
                    },
                )
                print(f"  registered: {prompt_name}")
                registered.append(prompt_name)
            except Exception as exc:
                print(f"  FAILED: {prompt_name} — {exc}")
                failed.append((yaml_file.name, prompt_name, str(exc)))

    print(f"\n{'=' * 60}")
    print(f"  Registered : {len(registered)}")
    print(f"  Failed     : {len(failed)}")
    print(f"{'=' * 60}")
    if failed:
        for fname, pname, err in failed:
            print(f"    - [{fname}] {pname}: {err}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap MLflow Prompt Registry from dify-data/*.yml")
    parser.add_argument("--dry-run", action="store_true", help="Preview without calling MLflow")
    args = parser.parse_args()
    register_all(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
