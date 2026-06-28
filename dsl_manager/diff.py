"""
diff.py — Generate human-readable diffs between DSL node versions.

Produces unified diffs suitable for:
  - Storing in change_approvals.diff_content
  - Displaying in the frontend DSL Management view
  - Audit trail review by approvers and auditors
"""

from __future__ import annotations

import difflib
import textwrap
from typing import Any


def compute_diff(old_content: str, new_content: str, node_name: str, node_type: str) -> str:
    """
    Return a unified diff between old and new node content.

    Returns a formatted string with a header line and the diff body.
    If the content is identical, returns an empty string.
    """
    if old_content == new_content:
        return ""

    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"{node_name} (stored)",
            tofile=f"{node_name} (new)",
            lineterm="",
        )
    )

    header = (
        f"=== CHANGE DETECTED ===\n"
        f"  node_type : {node_type}\n"
        f"  node_name : {node_name}\n"
        f"{'=' * 60}\n"
    )

    return header + "\n".join(diff_lines)


def format_diff_for_display(diff_content: str, max_width: int = 100) -> str:
    """
    Wrap long diff lines for terminal/UI display.
    Preserves +/- prefixes and indentation.
    """
    if not diff_content:
        return "(no diff)"

    lines = diff_content.splitlines()
    wrapped: list[str] = []
    for line in lines:
        if len(line) <= max_width:
            wrapped.append(line)
        else:
            prefix = line[:1] if line[:1] in ("+", "-", " ", "@", "=") else " "
            continuation = prefix + "  "
            wrapped.extend(
                textwrap.wrap(
                    line,
                    width=max_width,
                    initial_indent="",
                    subsequent_indent=continuation,
                    break_long_words=True,
                )
            )
    return "\n".join(wrapped)


def summarise_changes(nodes_with_diffs: list[dict[str, Any]]) -> str:
    """
    Produce a short human-readable summary of all changed nodes.

    nodes_with_diffs: list of dicts with keys:
        node_name, node_type, diff_content, is_new (bool)
    """
    if not nodes_with_diffs:
        return "No changes detected."

    lines = [f"{len(nodes_with_diffs)} node(s) changed:\n"]
    for item in nodes_with_diffs:
        status = "NEW" if item.get("is_new") else "MODIFIED"
        lines.append(f"  [{status}] {item['node_type'].upper()} — {item['node_name']}")
    return "\n".join(lines)
