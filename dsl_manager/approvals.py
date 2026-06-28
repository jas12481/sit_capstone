"""
approvals.py — MCP API integration for the DSL approval workflow.

Wraps the MCP server's /workflow-nodes and /change-approvals endpoints
so the CLI and prompt_advisor can manage the full sign-off lifecycle
without embedding HTTP calls everywhere.

Environment variables required:
    MCP_BASE_URL   default: http://localhost:8000
"""

from __future__ import annotations

import os
from typing import Any, Optional

import requests

_DEFAULT_BASE = "http://localhost:8000"


def _base() -> str:
    return os.getenv("MCP_BASE_URL", _DEFAULT_BASE).rstrip("/")


def _get(path: str, params: dict | None = None) -> Any:
    url = f"{_base()}{path}"
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def _post(path: str, body: dict) -> Any:
    url = f"{_base()}{path}"
    resp = requests.post(url, json=body, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ── workflow_nodes ────────────────────────────────────────────────────────────

def get_stored_nodes(workflow_name: str) -> list[dict]:
    """
    Fetch the latest stored node records for a workflow from the MCP server.
    Returns a list of workflow_node dicts (may be empty if workflow is new).
    """
    try:
        return _get("/workflow-nodes", params={"workflow_name": workflow_name})
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 404:
            return []
        raise


def store_node(
    workflow_name: str,
    node_type: str,
    node_name: str,
    content: str,
    content_hash: str,
    committed_by: str,
    workflow_version: str = "v1.0",
    git_commit_hash: Optional[str] = None,
) -> dict:
    """
    POST a new node record to /workflow-nodes.
    Used when initialising a workflow for the first time or after an approval.
    """
    body: dict[str, Any] = {
        "workflow_name": workflow_name,
        "workflow_version": workflow_version,
        "node_type": node_type,
        "node_name": node_name,
        "node_content": content,
        "content_hash": content_hash,
        "committed_by": committed_by,
    }
    if git_commit_hash:
        body["git_commit_hash"] = git_commit_hash
    return _post("/workflow-nodes", body)


# ── change_approvals ──────────────────────────────────────────────────────────

def submit_change(
    workflow_name: str,
    node_name: str,
    node_type: str,
    changed_by: str,
    diff_content: str,
    node_id: Optional[str] = None,
) -> dict:
    """
    Create a pending change approval request on the MCP server.
    Returns the created change_approval record.
    """
    body: dict[str, Any] = {
        "workflow_name": workflow_name,
        "node_name": node_name,
        "changed_by": changed_by,
        "diff_content": diff_content,
    }
    if node_id:
        body["node_id"] = node_id
    return _post("/change-approvals", body)


def list_pending(workflow_name: Optional[str] = None) -> list[dict]:
    """Return all pending change approvals, optionally filtered by workflow."""
    params: dict[str, Any] = {"status": "pending"}
    if workflow_name:
        params["workflow_name"] = workflow_name
    return _get("/change-approvals", params=params)


def list_all(
    workflow_name: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """Return change approvals with optional workflow/status filter."""
    params: dict[str, Any] = {"limit": limit}
    if workflow_name:
        params["workflow_name"] = workflow_name
    if status:
        params["status"] = status
    return _get("/change-approvals", params=params)


def approve_change(
    approval_id: str,
    actioned_by: str,
    reason: str,
    git_commit_hash: Optional[str] = None,
) -> dict:
    """
    Approve a pending change.  Optionally attach a git commit hash
    (filled in automatically by git_commit.commit_approved_change).
    """
    body: dict[str, Any] = {"actioned_by": actioned_by, "reason": reason}
    if git_commit_hash:
        body["git_commit_hash"] = git_commit_hash
    return _post(f"/change-approvals/{approval_id}/approve", body)


def reject_change(approval_id: str, actioned_by: str, reason: str) -> dict:
    """Reject a pending change."""
    body = {"actioned_by": actioned_by, "reason": reason}
    return _post(f"/change-approvals/{approval_id}/reject", body)
