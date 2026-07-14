"""
__main__.py — CLI entry point for the DSL Change Management System.

Usage
-----
# 1. First-time initialise — store baseline hashes (no diff, no approval needed)
python -m dsl_manager init --file Life_Assess_Claim.yml --by jaz

# 2. Scan for changes after editing a workflow in Dify and re-exporting
python -m dsl_manager scan --file Life_Assess_Claim.yml --by jaz

# 3. List pending approvals
python -m dsl_manager list-pending
python -m dsl_manager list-pending --workflow Life_Assess_Claim

# 4. Show full diff for a specific approval
python -m dsl_manager show <approval_id>

# 5. Approve a pending change (triggers GitHub commit automatically)
python -m dsl_manager approve <approval_id> --by "Sarah Tan" --reason "Tightened hallucination guard per MLflow run 42"

# 6. Reject a pending change
python -m dsl_manager reject <approval_id> --by "Sarah Tan" --reason "Need more context on rule 3 change"

# 7. List all approvals (all statuses)
python -m dsl_manager list-all
python -m dsl_manager list-all --workflow Life_Assess_Claim --status approved

# 8. Snapshot the current on-disk state of one or all workflow YAMLs to the
#    dedicated dsl-governance-history branch (full-file version history,
#    isolated from main — for auditability, independent of node-level approvals)
python -m dsl_manager snapshot --file dify-data/Life_Assess_Claim.yml --by jaz --reason "post-edit checkpoint"
python -m dsl_manager snapshot --all --by jaz --reason "baseline snapshot of all workflows"

# 9. Show snapshot history for a workflow file + a compare link between the two latest
python -m dsl_manager history --file dify-data/Life_Assess_Claim.yml
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / "mcp_server" / ".env")

from dsl_manager import approvals, git_commit
from dsl_manager.diff import compute_diff, format_diff_for_display, summarise_changes
from dsl_manager.parser import parse_workflow


# ── helpers ───────────────────────────────────────────────────────────────────

def _ok(msg: str) -> None:
    print(f"\033[92m✓\033[0m  {msg}")


def _warn(msg: str) -> None:
    print(f"\033[93m⚠\033[0m  {msg}")


def _err(msg: str) -> None:
    print(f"\033[91m✗\033[0m  {msg}", file=sys.stderr)


def _hr() -> None:
    print("─" * 60)


def _fmt_approval(a: dict, verbose: bool = False) -> None:
    status_colour = {
        "pending": "\033[93mpending\033[0m",
        "approved": "\033[92mapproved\033[0m",
        "rejected": "\033[91mrejected\033[0m",
    }.get(a.get("status", ""), a.get("status", ""))

    print(
        f"  {a.get('approval_id', '')[:8]}…  "
        f"{a.get('workflow_name', ''):<30}  "
        f"{a.get('node_name', ''):<35}  "
        f"by {a.get('changed_by', ''):<20}  "
        f"{status_colour}"
    )
    if verbose and a.get("change_reason"):
        print(f"           reason  : {a['change_reason']}")
    if verbose and a.get("approved_by"):
        print(f"           actioned: {a['approved_by']}")
    if verbose and a.get("git_commit_hash"):
        print(f"           commit  : {git_commit.get_commit_url(a['git_commit_hash'])}")


# ── sub-commands ──────────────────────────────────────────────────────────────

def cmd_init(args: argparse.Namespace) -> None:
    """
    Initialise baseline node hashes for a workflow.
    Stores every tracked node as-is; no diff, no approval.
    Safe to re-run — skips nodes already stored with the same hash.
    """
    nodes = parse_workflow(args.file)
    if not nodes:
        _warn("No trackable nodes found in this file.")
        return

    workflow_name = nodes[0]["workflow_name"]
    stored = {n["node_name"]: n for n in approvals.get_stored_nodes(workflow_name)}

    new_count = 0
    skip_count = 0

    for node in nodes:
        existing = stored.get(node["node_name"])
        if existing and existing.get("content_hash") == node["content_hash"]:
            skip_count += 1
            continue

        approvals.store_node(
            workflow_name=node["workflow_name"],
            node_type=node["node_type"],
            node_name=node["node_name"],
            content=node["content"],
            content_hash=node["content_hash"],
            committed_by=args.by,
            workflow_version=getattr(args, "version", "v1.0"),
        )
        _ok(f"Stored baseline: [{node['node_type'].upper()}] {node['node_name']}")
        new_count += 1

    _hr()
    print(f"  Init complete — {new_count} node(s) stored, {skip_count} unchanged.")


def cmd_scan(args: argparse.Namespace) -> None:
    """
    Scan an exported DSL YAML for changes vs stored baseline.
    Submits a pending change_approval for every modified or new node.
    """
    nodes = parse_workflow(args.file)
    if not nodes:
        _warn("No trackable nodes found.")
        return

    workflow_name = nodes[0]["workflow_name"]
    stored = {n["node_name"]: n for n in approvals.get_stored_nodes(workflow_name)}

    changed: list[dict] = []

    for node in nodes:
        existing = stored.get(node["node_name"])
        is_new = existing is None
        if not is_new and existing.get("content_hash") == node["content_hash"]:
            continue

        old_content = existing["node_content"] if existing else ""
        diff = compute_diff(old_content, node["content"], node["node_name"], node["node_type"])

        changed.append(
            {
                "node_name": node["node_name"],
                "node_type": node["node_type"],
                # change_approvals.node_id is a UUID FK to workflow_nodes.node_id.
                # existing["node_id"] is that real stored UUID; node["node_id"] is
                # Dify's own internal node identifier (not a UUID) and must not go
                # here. New nodes have no stored row yet, so send None.
                "node_id": existing["node_id"] if existing else None,
                "content": node["content"],
                "content_hash": node["content_hash"],
                "diff_content": diff,
                "is_new": is_new,
            }
        )

    if not changed:
        _ok(f"No changes detected in {workflow_name}.")
        return

    print(f"\n{summarise_changes(changed)}\n")

    for item in changed:
        record = approvals.submit_change(
            workflow_name=workflow_name,
            node_name=item["node_name"],
            node_type=item["node_type"],
            changed_by=args.by,
            diff_content=item["diff_content"],
            node_id=item.get("node_id"),
            new_content=item["content"],
            new_hash=item["content_hash"],
        )
        label = "NEW" if item["is_new"] else "MODIFIED"
        _ok(
            f"[{label}] {item['node_type'].upper()} — {item['node_name']}  "
            f"→ approval {record['approval_id'][:8]}… (pending)"
        )

    _hr()
    print(
        f"  {len(changed)} change(s) submitted. "
        "Use 'python -m dsl_manager list-pending' to review."
    )


def cmd_list_pending(args: argparse.Namespace) -> None:
    pending = approvals.list_pending(getattr(args, "workflow", None))
    if not pending:
        _ok("No pending approvals.")
        return

    print(f"\n  {len(pending)} pending approval(s):\n")
    _hr()
    for a in pending:
        _fmt_approval(a)
    _hr()
    print("  Use 'python -m dsl_manager show <id>' to view the full diff.")


def cmd_list_all(args: argparse.Namespace) -> None:
    records = approvals.list_all(
        workflow_name=getattr(args, "workflow", None),
        status=getattr(args, "status", None),
    )
    if not records:
        print("  No records found.")
        return

    print(f"\n  {len(records)} approval record(s):\n")
    _hr()
    for a in records:
        _fmt_approval(a, verbose=True)
    _hr()


def cmd_show(args: argparse.Namespace) -> None:
    records = approvals.list_all(limit=200)
    match = [r for r in records if r["approval_id"].startswith(args.approval_id)]
    if not match:
        _err(f"No approval found matching prefix: {args.approval_id}")
        sys.exit(1)
    if len(match) > 1:
        _err("Ambiguous ID prefix — provide more characters.")
        sys.exit(1)

    a = match[0]
    print(f"\n  Approval  : {a['approval_id']}")
    print(f"  Workflow  : {a['workflow_name']}")
    print(f"  Node      : {a['node_name']}")
    print(f"  Status    : {a['status']}")
    print(f"  Submitted : {a.get('created_at', '')}")
    print(f"  By        : {a.get('changed_by', '')}")
    if a.get("approved_by"):
        print(f"  Actioned  : {a['approved_by']}  ({a.get('approved_at', '')})")
    if a.get("change_reason"):
        print(f"  Reason    : {a['change_reason']}")
    if a.get("git_commit_hash"):
        print(f"  Commit    : {git_commit.get_commit_url(a['git_commit_hash'])}")
    print()
    _hr()
    print(format_diff_for_display(a.get("diff_content", "(no diff stored)")))
    _hr()


def cmd_approve(args: argparse.Namespace) -> None:
    records = approvals.list_all(limit=200)
    match = [r for r in records if r["approval_id"].startswith(args.approval_id)]
    if not match:
        _err(f"No approval found matching prefix: {args.approval_id}")
        sys.exit(1)
    if len(match) > 1:
        _err("Ambiguous ID prefix — provide more characters.")
        sys.exit(1)

    a = match[0]
    if a["status"] != "pending":
        _err(f"Cannot approve — status is already '{a['status']}'.")
        sys.exit(1)

    node_type = a.get("node_type") or "unknown"

    # new_content/new_hash are populated on every approval submitted after
    # this fix (both by this CLI and by the server's /dsl/scan). Fall back to
    # reconstructing from the stored diff for older pending approvals that
    # predate the field.
    new_content = a.get("new_content") or _extract_new_content_from_diff(a.get("diff_content", ""))

    commit_sha: Optional[str] = None

    # Try to commit to GitHub; continue even if credentials are missing.
    try:
        if not new_content:
            _warn("Could not determine new content — GitHub commit skipped.")
        else:
            commit_sha = git_commit.commit_approved_change(
                workflow_name=a["workflow_name"],
                node_name=a["node_name"],
                node_type=node_type,
                new_content=new_content,
                approved_by=args.by,
                reason=args.reason,
                approval_id=a["approval_id"],
            )
            _ok(f"GitHub commit: {git_commit.get_commit_url(commit_sha)}")
    except EnvironmentError as exc:
        _warn(f"GitHub commit skipped: {exc}")
    except Exception as exc:  # noqa: BLE001
        _warn(f"GitHub commit failed (approval still recorded): {exc}")

    approvals.approve_change(
        approval_id=a["approval_id"],
        actioned_by=args.by,
        reason=args.reason,
        git_commit_hash=commit_sha,
    )
    _ok(
        f"Approved: {a['workflow_name']} — {a['node_name']}  "
        f"(by {args.by})"
    )

    # Attach git_commit_hash to workflow_nodes — the server's own promotion
    # (triggered inside approve_change above when new_content/new_hash are
    # present) doesn't know the commit SHA, since committing happens here in
    # the CLI, not on the server.
    if new_content:
        from dsl_manager.parser import hash_content
        approvals.store_node(
            workflow_name=a["workflow_name"],
            node_type=node_type,
            node_name=a["node_name"],
            content=new_content,
            content_hash=a.get("new_hash") or hash_content(new_content),
            committed_by=args.by,
            git_commit_hash=commit_sha,
        )


def cmd_reject(args: argparse.Namespace) -> None:
    records = approvals.list_all(limit=200)
    match = [r for r in records if r["approval_id"].startswith(args.approval_id)]
    if not match:
        _err(f"No approval found matching prefix: {args.approval_id}")
        sys.exit(1)
    if len(match) > 1:
        _err("Ambiguous ID prefix — provide more characters.")
        sys.exit(1)

    a = match[0]
    if a["status"] != "pending":
        _err(f"Cannot reject — status is already '{a['status']}'.")
        sys.exit(1)

    approvals.reject_change(
        approval_id=a["approval_id"],
        actioned_by=args.by,
        reason=args.reason,
    )
    _ok(
        f"Rejected: {a['workflow_name']} — {a['node_name']}  "
        f"(by {args.by})"
    )


def cmd_snapshot(args: argparse.Namespace) -> None:
    """
    Commit the current on-disk content of one or all dify-data/*.yml workflow
    files to the dedicated dsl-governance-history branch. Independent of the
    node-level approval flow — this is a whole-file version checkpoint, useful
    any time (new workflow added, batch of edits done, before a demo, etc.).
    """
    if args.all:
        files = sorted(glob.glob("dify-data/*.yml"))
        if not files:
            _warn("No .yml files found under dify-data/.")
            return
    else:
        files = [args.file]

    _hr()
    for file_path in files:
        if not Path(file_path).is_file():
            _err(f"File not found, skipped: {file_path}")
            continue
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            commit_sha = git_commit.commit_workflow_snapshot(
                repo_path=git_commit._repo_relative_path(file_path),
                content=content,
                committed_by=args.by,
                reason=args.reason,
            )
            _ok(f"{Path(file_path).name}  →  {git_commit.get_commit_url(commit_sha)}")
        except EnvironmentError as exc:
            _err(f"Snapshot skipped: {exc}")
            sys.exit(1)
        except Exception as exc:  # noqa: BLE001
            _err(f"Snapshot failed for {file_path}: {exc}")
    _hr()
    print(f"  Branch: {git_commit._governance_branch()}")


def cmd_history(args: argparse.Namespace) -> None:
    """Show past snapshot commits for a workflow file, newest first."""
    commits = git_commit.list_workflow_snapshots(args.file, limit=args.limit)
    if not commits:
        _warn(f"No snapshot history found for {args.file} on branch "
              f"'{git_commit._governance_branch()}'.")
        return

    print(f"\n  Snapshot history for {args.file}  ({len(commits)} shown):\n")
    _hr()
    for c in commits:
        print(f"  {c['short_sha']}  {c['date']}  {c['author']:<20}  {c['message']}")
    _hr()

    if len(commits) >= 2:
        newest, previous = commits[0], commits[1]
        print(
            f"  Compare latest two: "
            f"{git_commit.get_compare_url(previous['sha'], newest['sha'])}"
        )


# ── utility ───────────────────────────────────────────────────────────────────

def _extract_new_content_from_diff(diff_content: str) -> str:
    """
    Reconstruct the 'new' file content from a unified diff string.
    Lines starting with '+' (excluding '+++' header) are the new content.
    Falls back to empty string if diff can't be parsed.
    """
    lines = diff_content.splitlines()
    new_lines: list[str] = []
    in_diff = False
    for line in lines:
        if line.startswith("+++"):
            in_diff = True
            continue
        if not in_diff:
            continue
        if line.startswith("@@"):
            continue
        if line.startswith("+"):
            new_lines.append(line[1:])
        elif line.startswith(" "):
            new_lines.append(line[1:])
        # lines starting with '-' are removed content, skip them
    return "\n".join(new_lines)


# ── argument parser ───────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m dsl_manager",
        description="DSL Change Management CLI — governed version control for Dify workflows.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # init
    init_p = sub.add_parser("init", help="Store baseline hashes for a workflow (first run)")
    init_p.add_argument("--file", required=True, help="Path to exported Dify DSL YAML")
    init_p.add_argument("--by", required=True, help="Your name (stored as committed_by)")
    init_p.add_argument("--version", default="v1.0", help="Workflow version label (default: v1.0)")

    # scan
    scan_p = sub.add_parser("scan", help="Detect changes and submit pending approvals")
    scan_p.add_argument("--file", required=True, help="Path to exported Dify DSL YAML")
    scan_p.add_argument("--by", required=True, help="Your name (stored as changed_by)")

    # list-pending
    lp_p = sub.add_parser("list-pending", help="List pending change approvals")
    lp_p.add_argument("--workflow", default=None, help="Filter by workflow name")

    # list-all
    la_p = sub.add_parser("list-all", help="List all change approvals")
    la_p.add_argument("--workflow", default=None, help="Filter by workflow name")
    la_p.add_argument("--status", default=None, help="Filter by status (pending/approved/rejected)")

    # show
    show_p = sub.add_parser("show", help="Show full diff for an approval")
    show_p.add_argument("approval_id", help="Approval ID (or unique prefix)")

    # approve
    app_p = sub.add_parser("approve", help="Approve a pending change (triggers GitHub commit)")
    app_p.add_argument("approval_id", help="Approval ID (or unique prefix)")
    app_p.add_argument("--by", required=True, help="Your name")
    app_p.add_argument("--reason", required=True, help="Mandatory justification for approval")

    # reject
    rej_p = sub.add_parser("reject", help="Reject a pending change")
    rej_p.add_argument("approval_id", help="Approval ID (or unique prefix)")
    rej_p.add_argument("--by", required=True, help="Your name")
    rej_p.add_argument("--reason", required=True, help="Mandatory justification for rejection")

    # snapshot
    snap_p = sub.add_parser(
        "snapshot",
        help="Commit whole-file workflow snapshot(s) to the dsl-governance-history branch",
    )
    snap_group = snap_p.add_mutually_exclusive_group(required=True)
    snap_group.add_argument("--file", help="Path to a single dify-data/*.yml file")
    snap_group.add_argument("--all", action="store_true", help="Snapshot every dify-data/*.yml file")
    snap_p.add_argument("--by", required=True, help="Your name (stored as committer in commit message)")
    snap_p.add_argument("--reason", required=True, help="Why this snapshot is being taken")

    # history
    hist_p = sub.add_parser("history", help="Show snapshot history for a workflow file")
    hist_p.add_argument("--file", required=True, help="Path to a dify-data/*.yml file")
    hist_p.add_argument("--limit", type=int, default=20, help="Max commits to show (default 20)")

    return p


_COMMANDS = {
    "init": cmd_init,
    "scan": cmd_scan,
    "list-pending": cmd_list_pending,
    "list-all": cmd_list_all,
    "show": cmd_show,
    "approve": cmd_approve,
    "reject": cmd_reject,
    "snapshot": cmd_snapshot,
    "history": cmd_history,
}


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    fn = _COMMANDS.get(args.command)
    if fn is None:
        parser.print_help()
        sys.exit(1)
    try:
        fn(args)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
    except Exception as exc:  # noqa: BLE001
        _err(str(exc))
        sys.exit(1)


if __name__ == "__main__":
    main()
