/**
 * MCP API client — all server-side and client-side calls go through here.
 * Uses the /api/mcp/* proxy defined in next.config.js so the MCP URL
 * is never exposed to the browser directly.
 */

const BASE = '/api/mcp';

async function get<T>(path: string, params?: Record<string, string | number | undefined>): Promise<T> {
  const url = new URL(`${BASE}${path}`, 'http://localhost');
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') url.searchParams.set(k, String(v));
    });
  }
  const res = await fetch(url.pathname + url.search, { cache: 'no-store' });
  if (!res.ok) throw new Error(`MCP ${path} → ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `MCP POST ${path} → ${res.status}`);
  }
  return res.json();
}

// ── Assessment Logs ──────────────────────────────────────────────────────────

export type AssessmentLog = {
  id: string;
  claim_id: string;
  workflow_type: string;
  recommendation: string;
  confidence_level: string;
  mandatory_rules_failed: number;
  total_rules_passed: number;
  coverage_conclusion: string;
  model_version: string;
  prompt_version: string;
  mlflow_run_id: string;
  judge_completeness_score: number;
  judge_consistency_score: number;
  judge_hallucination_risk_score: number;
  judge_clarity_score: number;
  judge_overall_score: number;
  assessed_at: string;
};

export function getAssessmentLogs(filters?: {
  workflow_type?: string;
  recommendation?: string;
  confidence_level?: string;
  claim_id?: string;
  limit?: number;
}) {
  return get<AssessmentLog[]>('/assessment-logs', filters as Record<string, string>);
}

// ── Workflow Nodes ───────────────────────────────────────────────────────────

export type WorkflowNode = {
  node_id: string;
  workflow_name: string;
  workflow_version: string;
  node_type: string;
  node_name: string;
  node_content: string;
  content_hash: string;
  committed_at: string;
  committed_by: string;
  git_commit_hash: string;
};

export function getWorkflowNodes(workflow_name?: string) {
  return get<WorkflowNode[]>('/workflow-nodes', workflow_name ? { workflow_name } : undefined);
}

// ── Change Approvals ─────────────────────────────────────────────────────────

export type ChangeApproval = {
  approval_id: string;
  node_id: string;
  workflow_name: string;
  node_name: string;
  changed_by: string;
  approved_by: string;
  change_reason: string;
  diff_content: string;
  status: 'pending' | 'approved' | 'rejected';
  approved_at: string;
  git_commit_hash: string;
  created_at: string;
};

export function getChangeApprovals(filters?: {
  status?: string;
  workflow_name?: string;
  limit?: number;
}) {
  return get<ChangeApproval[]>('/change-approvals', filters as Record<string, string>);
}

export function approveChange(approval_id: string, actioned_by: string, reason: string) {
  return post<ChangeApproval>(`/change-approvals/${approval_id}/approve`, {
    actioned_by,
    reason,
  });
}

export function rejectChange(approval_id: string, actioned_by: string, reason: string) {
  return post<ChangeApproval>(`/change-approvals/${approval_id}/reject`, {
    actioned_by,
    reason,
  });
}
