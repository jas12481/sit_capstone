"""
git_commit.py — Commit approved DSL node changes to GitHub.

Uses the GitHub Contents REST API (no local git required) to write
the approved node content to a versioned file in the repository.

File path pattern committed:
    dify-data/approved_nodes/{workflow_name}/{node_name}.txt

Commit message format:
    [APPROVED] {workflow_name} — {node_name}: {reason} | By: {approved_by}

Returns the full git commit SHA which is stored in change_approvals.git_commit_hash.

Environment variables required:
    GITHUB_TOKEN    — personal access token with repo write scope
    GITHUB_REPO     — owner/repo  e.g. "jazzhands/sit_capstone"
    GITHUB_BRANCH   — default: "main"
"""

from __future__ import annotations

import base64
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

_GH_API = "https://api.github.com"


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise EnvironmentError(
            "GITHUB_TOKEN is not set. Set it in mcp_server/.env or your shell environment."
        )
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _repo() -> str:
    repo = os.getenv("GITHUB_REPO", "")
    if not repo:
        raise EnvironmentError(
            "GITHUB_REPO is not set (expected format: owner/repo)."
        )
    return repo


def _branch() -> str:
    return os.getenv("GITHUB_BRANCH", "main")


def _file_path(workflow_name: str, node_name: str) -> str:
    """Canonical repo path for a committed node snapshot."""
    safe_workflow = workflow_name.replace(" ", "_")
    safe_node = node_name.replace(" ", "_")
    return f"dify-data/approved_nodes/{safe_workflow}/{safe_node}.txt"


def _get_current_sha(file_path: str) -> Optional[str]:
    """
    Fetch the current blob SHA for a file (required by the GitHub API
    when updating an existing file).  Returns None if the file doesn't exist.
    """
    url = f"{_GH_API}/repos/{_repo()}/contents/{file_path}"
    resp = requests.get(url, headers=_headers(), params={"ref": _branch()}, timeout=15)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json().get("sha")


def commit_approved_change(
    workflow_name: str,
    node_name: str,
    node_type: str,
    new_content: str,
    approved_by: str,
    reason: str,
    approval_id: Optional[str] = None,
) -> str:
    """
    Write the approved node content to GitHub and return the commit SHA.

    Parameters
    ----------
    workflow_name   Dify workflow name (e.g. "Life_Assess_Claim")
    node_name       Node title (e.g. "rule_by_rule_eligibility_check")
    node_type       "llm", "code", or "agent"
    new_content     The full extracted content to commit
    approved_by     Name of the approver
    reason          Mandatory justification (stored in commit message)
    approval_id     Optional change_approval UUID for cross-reference

    Returns
    -------
    git commit SHA string
    """
    file_path = _file_path(workflow_name, node_name)
    encoded = base64.b64encode(new_content.encode("utf-8")).decode("ascii")

    ref_note = f" (approval: {approval_id})" if approval_id else ""
    message = (
        f"[APPROVED] {workflow_name} — {node_name} [{node_type}]: "
        f"{reason} | By: {approved_by}{ref_note}"
    )

    current_sha = _get_current_sha(file_path)

    body: dict = {
        "message": message,
        "content": encoded,
        "branch": _branch(),
    }
    if current_sha:
        body["sha"] = current_sha

    url = f"{_GH_API}/repos/{_repo()}/contents/{file_path}"
    resp = requests.put(url, headers=_headers(), json=body, timeout=30)
    resp.raise_for_status()

    commit_sha: str = resp.json()["commit"]["sha"]
    return commit_sha


def get_commit_url(commit_sha: str) -> str:
    """Return the GitHub web URL for a commit SHA."""
    return f"https://github.com/{_repo()}/commit/{commit_sha}"
