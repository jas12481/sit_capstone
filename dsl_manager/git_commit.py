"""
git_commit.py — Commit approved DSL node changes to GitHub.

Uses the GitHub Contents REST API (no local git required) to write
the approved node content to a versioned file in the repository.

File path pattern committed:
    dify-data/approved_nodes/{workflow_name}/{node_name}.txt

Commit message format:
    [APPROVED] {workflow_name} — {node_name}: {reason} | By: {approved_by}

Returns the full git commit SHA which is stored in change_approvals.git_commit_hash.

Also supports whole-workflow-file snapshots to a dedicated, isolated branch
(see commit_workflow_snapshot below) — a full version history of every
dify-data/*.yml file, kept off main so governance/audit commits never mix
with regular app-code commits.

Environment variables required:
    GITHUB_TOKEN    — personal access token with repo write scope
    GITHUB_REPO     — owner/repo  e.g. "jazzhands/sit_capstone"
    GITHUB_BRANCH   — default: "main"

Environment variables (optional, for whole-file snapshots):
    GITHUB_GOVERNANCE_BRANCH  — default: "dsl-governance-history"
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
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


def _governance_branch() -> str:
    return os.getenv("GITHUB_GOVERNANCE_BRANCH", "dsl-governance-history")


# dsl_manager/ sits directly under the repo root — used to resolve any given
# file_path to its repo-relative form regardless of the caller's cwd (the CLI
# runs from repo root, but the MCP server runs from mcp_server/, so relying on
# os.path.relpath()'s cwd-relative default would silently break there).
_REPO_ROOT = Path(__file__).resolve().parent.parent


def _repo_relative_path(file_path: str) -> str:
    abs_path = Path(file_path).resolve()
    try:
        return abs_path.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return Path(file_path).as_posix()


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


# ── whole-workflow-file snapshots (dedicated governance branch) ────────────────

def ensure_governance_branch(base_branch: Optional[str] = None) -> bool:
    """
    Make sure the dedicated governance-history branch exists on GitHub,
    creating it (pointed at the tip of `base_branch`, default "main") if not.

    Returns True if the branch was just created, False if it already existed.
    """
    branch = _governance_branch()
    base = base_branch or _branch()

    ref_url = f"{_GH_API}/repos/{_repo()}/git/ref/heads/{branch}"
    resp = requests.get(ref_url, headers=_headers(), timeout=15)
    if resp.status_code == 200:
        return False
    if resp.status_code != 404:
        resp.raise_for_status()

    base_ref_url = f"{_GH_API}/repos/{_repo()}/git/ref/heads/{base}"
    base_resp = requests.get(base_ref_url, headers=_headers(), timeout=15)
    base_resp.raise_for_status()
    base_sha = base_resp.json()["object"]["sha"]

    create_url = f"{_GH_API}/repos/{_repo()}/git/refs"
    create_resp = requests.post(
        create_url,
        headers=_headers(),
        json={"ref": f"refs/heads/{branch}", "sha": base_sha},
        timeout=15,
    )
    create_resp.raise_for_status()
    return True


def commit_workflow_snapshot(
    repo_path: str,
    content: bytes,
    committed_by: str,
    reason: str,
) -> str:
    """
    Commit raw file content to the dedicated governance-history branch, at
    the given repo-relative path (e.g. "dify-data/Life_Assess_Claim.yml").
    Creates the branch first if it doesn't exist yet.

    Deliberately takes content as bytes rather than reading a local file
    itself — the caller is responsible for sourcing it, whether that's a
    local file (the CLI) or a Supabase Storage download (the MCP server).
    This function has no opinion on where content comes from, only where
    it's committed to.

    Unlike commit_approved_change (which writes an extracted node snippet to
    main), this writes the WHOLE file as-is — every call is a full point-in-time
    version of that workflow, so `git log`/GitHub's compare view against this
    branch gives a complete, diffable history per workflow file.

    Returns the git commit SHA.
    """
    ensure_governance_branch()
    branch = _governance_branch()

    encoded = base64.b64encode(content).decode("ascii")

    message = f"[SNAPSHOT] {os.path.basename(repo_path)}: {reason} | By: {committed_by}"

    current_sha = _get_current_sha_on_branch(repo_path, branch)

    body: dict = {
        "message": message,
        "content": encoded,
        "branch": branch,
    }
    if current_sha:
        body["sha"] = current_sha

    url = f"{_GH_API}/repos/{_repo()}/contents/{repo_path}"
    resp = requests.put(url, headers=_headers(), json=body, timeout=30)
    resp.raise_for_status()

    return resp.json()["commit"]["sha"]


def _get_current_sha_on_branch(repo_path: str, branch: str) -> Optional[str]:
    url = f"{_GH_API}/repos/{_repo()}/contents/{repo_path}"
    resp = requests.get(url, headers=_headers(), params={"ref": branch}, timeout=15)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json().get("sha")


def list_workflow_snapshots(file_path: str, limit: int = 20) -> list[dict]:
    """
    Return past snapshot commits for a given workflow file on the governance
    branch, newest first. Each item: {sha, short_sha, message, date, author}.

    Deliberately does NOT use GitHub's ?path= commit filter: that filter is
    based on whether the file's git tree entry actually changed in that
    commit. A snapshot whose content happens to be byte-identical to its
    parent (guaranteed for the very first baseline snapshot taken right after
    the branch forks off main) produces a real commit that GitHub's path
    filter silently excludes, even though it exists and is reachable.
    Matching on our own "[SNAPSHOT] {filename}:" commit-message prefix finds
    every snapshot ever taken for this file regardless of whether content
    actually changed.
    """
    repo_path = _repo_relative_path(file_path)
    marker = f"[SNAPSHOT] {os.path.basename(repo_path)}:"

    matches: list[dict] = []
    page = 1
    while len(matches) < limit and page <= 5:  # hard cap: 500 commits scanned
        url = f"{_GH_API}/repos/{_repo()}/commits"
        resp = requests.get(
            url,
            headers=_headers(),
            params={"sha": _governance_branch(), "per_page": 100, "page": page},
            timeout=15,
        )
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        items = resp.json()
        if not items:
            break

        for item in items:
            commit = item["commit"]
            if not commit["message"].startswith(marker):
                continue
            matches.append(
                {
                    "sha": item["sha"],
                    "short_sha": item["sha"][:8],
                    "message": commit["message"],
                    "date": commit["author"]["date"],
                    "author": commit["author"]["name"],
                }
            )
            if len(matches) >= limit:
                break
        page += 1

    return matches


def get_compare_url(base_sha: str, head_sha: str) -> str:
    """Return the GitHub web URL for a diff/comparison between two commits."""
    return f"https://github.com/{_repo()}/compare/{base_sha}...{head_sha}"


def get_file_content_at_ref(repo_path: str, ref: str) -> bytes:
    """
    Fetch raw file content from GitHub at the given ref (branch name, tag, or
    commit SHA) — used to read a specific past snapshot's actual content, not
    just its commit metadata (which is all list_workflow_snapshots returns).
    """
    url = f"{_GH_API}/repos/{_repo()}/contents/{repo_path}"
    resp = requests.get(url, headers=_headers(), params={"ref": ref}, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return base64.b64decode(data["content"])
