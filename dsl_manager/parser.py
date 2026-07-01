"""
parser.py — Parse a Dify DSL YAML and extract trackable nodes.

Extracts LLM, code, and agent nodes from workflow.graph.nodes.
Each extracted node gets a SHA256 hash of its content so changes
can be detected by comparing against the stored hash in workflow_nodes.

Node content extracted per type:
  llm   → all prompt_template messages joined (system + user text)
  code  → the raw code string
  agent → JSON-serialised list of tool names bound to the agent

Usage (CLI):
  python -m dsl_manager.parser --file Life_Assess_Claim.yml
  python -m dsl_manager.parser --file Life_Assess_Claim.yml --json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import yaml


TRACKED_TYPES = {"llm", "code", "agent"}


# ── content extraction ────────────────────────────────────────────────────────

def extract_llm_content(data: dict) -> str:
    """
    Concatenate system + user prompt texts from prompt_template.
    Includes model name so a model swap is also detected as a change.
    """
    parts: list[str] = []
    model = data.get("model", {})
    parts.append(f"[model] {model.get('name', '')} / {model.get('provider', '')}")

    for msg in data.get("prompt_template", []):
        role = msg.get("role", "")
        text = (msg.get("text") or "").strip()
        if text:
            parts.append(f"[{role}]\n{text}")

    structured = data.get("structured_output", {})
    if data.get("structured_output_enabled") and structured:
        parts.append(f"[schema]\n{json.dumps(structured, ensure_ascii=False, sort_keys=True)}")

    return "\n\n".join(parts)


def extract_code_content(data: dict) -> str:
    return (data.get("code") or "").strip()


def extract_agent_content(data: dict) -> str:
    """
    Serialise the strategy, model, instruction, query, and tools bound to
    the agent node. Dify stores these inside agent_parameters; fall back to
    top-level `tools` for older exports that don't nest them.
    """
    params = data.get("agent_parameters", {})
    instruction = params.get("instruction", {}).get("value", "")
    query_tpl = params.get("query", {}).get("value", "")
    tools_raw = params.get("tools", {}).get("value", []) or data.get("tools", [])
    simplified = [
        {
            "tool_name": t.get("tool_name") or t.get("provider_show_name") or t.get("tool_label", ""),
            "provider": t.get("provider_name", ""),
            "enabled": t.get("enabled", True),
        }
        for t in tools_raw
    ]
    model_val = params.get("model", {}).get("value", {})
    model_name = model_val.get("model", "") if isinstance(model_val, dict) else ""
    strategy = data.get("agent_strategy_name", "")
    return json.dumps(
        {
            "strategy": strategy,
            "model": model_name,
            "instruction": instruction,
            "query": query_tpl,
            "tools": simplified,
        },
        indent=2,
        ensure_ascii=False,
    )


_EXTRACTORS = {
    "llm": extract_llm_content,
    "code": extract_code_content,
    "agent": extract_agent_content,
}


# ── hashing ───────────────────────────────────────────────────────────────────

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ── main parse logic ──────────────────────────────────────────────────────────

def parse_workflow(file_path: str | Path) -> list[dict[str, Any]]:
    """
    Parse a Dify DSL YAML file and return a list of extracted node records.

    Each record is a dict with:
        workflow_name  — from app.name in the YAML
        node_type      — 'llm', 'code', or 'agent'
        node_name      — data.title of the node
        node_id        — internal Dify node ID
        content        — extracted text content
        content_hash   — SHA256 of content
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    workflow_name: str = raw.get("app", {}).get("name", path.stem)
    nodes: list[dict] = raw.get("workflow", {}).get("graph", {}).get("nodes", [])

    extracted: list[dict[str, Any]] = []

    for node in nodes:
        data = node.get("data", {})
        node_type: str = data.get("type", "")

        if node_type not in TRACKED_TYPES:
            continue

        extractor = _EXTRACTORS[node_type]
        content = extractor(data)

        if not content:
            continue

        title: str = data.get("title", node.get("id", "unnamed"))
        node_id: str = node.get("id", "")

        extracted.append(
            {
                "workflow_name": workflow_name,
                "node_type": node_type,
                "node_name": title,
                "node_id": node_id,
                "content": content,
                "content_hash": hash_content(content),
            }
        )

    return extracted


# ── CLI ───────────────────────────────────────────────────────────────────────

def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Parse a Dify DSL YAML and list trackable nodes with SHA256 hashes."
    )
    parser.add_argument("--file", required=True, help="Path to the Dify DSL YAML file")
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output raw JSON instead of the human-readable summary",
    )
    args = parser.parse_args()

    nodes = parse_workflow(args.file)

    if args.as_json:
        print(json.dumps(nodes, indent=2, ensure_ascii=False))
        return

    workflow_name = nodes[0]["workflow_name"] if nodes else Path(args.file).stem
    print(f"\n{'='*60}")
    print(f"  Workflow : {workflow_name}")
    print(f"  File     : {args.file}")
    print(f"  Nodes    : {len(nodes)} trackable")
    print(f"{'='*60}\n")

    by_type: dict[str, list] = {}
    for n in nodes:
        by_type.setdefault(n["node_type"], []).append(n)

    for ntype in ("llm", "code", "agent"):
        group = by_type.get(ntype, [])
        if not group:
            continue
        print(f"  [{ntype.upper()}] ({len(group)} nodes)")
        for n in group:
            print(f"    • {n['node_name']:<45}  {n['content_hash'][:12]}…")
        print()


if __name__ == "__main__":
    _cli()
