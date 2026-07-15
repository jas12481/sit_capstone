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

export type RuleCheck = {
  rule_id: string;
  rule_name: string;
  result: 'PASS' | 'FAIL' | 'UNKNOWN' | 'NOT_APPLICABLE';
  is_mandatory: string | boolean;
  reason: string;
  evidence_fields?: string[];
};

export type AssessmentLog = {
  log_id: string;
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
  rule_checks?: RuleCheck[];
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

// ── Fraud Risk Checks ────────────────────────────────────────────────────────

export type FraudFlag = { signal: string; explanation: string };

export type FraudRiskCheck = {
  id: string;
  claim_id: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  flags: FraudFlag[];
  recommended_action: 'proceed_normally' | 'flag_for_investigation';
  checked_by: string;
  checked_at: string;
};

export function getFraudRiskChecks(filters?: { claim_id?: string; risk_level?: string; limit?: number }) {
  return get<FraudRiskCheck[]>('/fraud-risk-checks', filters as Record<string, string>);
}

export function createFraudRiskCheck(check: {
  claim_id: string;
  risk_level: string;
  flags?: FraudFlag[];
  recommended_action?: string;
  checked_by?: string;
}) {
  return post<FraudRiskCheck>('/fraud-risk-checks', check);
}

// Calls the Dify Fraud/Anomaly Risk Signals workflow directly (not the MCP
// proxy — this hits /api/dify/fraud, a separate server-side Dify proxy).
export async function runFraudRiskCheck(claim_id: string): Promise<{
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  flags: FraudFlag[];
  recommended_action: 'proceed_normally' | 'flag_for_investigation';
}> {
  const res = await fetch('/api/dify/fraud', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ claim_id }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `Fraud check failed (${res.status})`);
  return json;
}

// ── Assessment Explanations ─────────────────────────────────────────────────
// Keyed by log_id, not claim_id (unlike Fraud) — a claim can have multiple
// assessment_logs rows, and an explanation is tied to one specific verdict.

export type AssessmentExplanation = {
  id: string;
  log_id: string;
  claim_id: string;
  explanation_text: string;
  generated_by: string;
  generated_at: string;
};

export function getAssessmentExplanations(filters?: { log_id?: string; claim_id?: string; limit?: number }) {
  return get<AssessmentExplanation[]>('/explanations', filters as Record<string, string>);
}

export function createAssessmentExplanation(explanation: {
  log_id: string;
  claim_id: string;
  explanation_text: string;
  generated_by?: string;
}) {
  return post<AssessmentExplanation>('/explanations', explanation);
}

// Calls the Dify Explain_Assessment_Reasoning workflow directly (not the MCP
// proxy — this hits /api/dify/explain, a separate server-side Dify proxy).
export async function runAssessmentExplanation(claim_id: string, log_id: string): Promise<{
  explanation_text: string;
}> {
  const res = await fetch('/api/dify/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ claim_id, log_id }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `Explanation failed (${res.status})`);
  return json;
}

// ── Missing Documentation Checks ────────────────────────────────────────────
// Keyed by claim_id, like Fraud — reflects the claim's current state, not
// tied to one specific assessment_logs row.

export type MissingDocument = { document_type: string; linked_rule_id: string; reason: string };

export type MissingDocumentationCheck = {
  id: string;
  claim_id: string;
  all_requirements_met: boolean;
  missing_documents: MissingDocument[];
  submitted_documents_summary: string;
  checked_by: string;
  checked_at: string;
};

export function getMissingDocumentationChecks(filters?: { claim_id?: string; limit?: number }) {
  return get<MissingDocumentationCheck[]>('/missing-documentation-checks', filters as Record<string, string>);
}

export function createMissingDocumentationCheck(check: {
  claim_id: string;
  all_requirements_met: boolean;
  missing_documents?: MissingDocument[];
  submitted_documents_summary?: string;
  checked_by?: string;
}) {
  return post<MissingDocumentationCheck>('/missing-documentation-checks', check);
}

// Calls the Dify Missing_Documentation_Advisor workflow directly (not the MCP
// proxy — this hits /api/dify/missing-docs, a separate server-side Dify proxy).
export async function runMissingDocumentationCheck(claim_id: string): Promise<{
  all_requirements_met: boolean;
  missing_documents: MissingDocument[];
  submitted_documents_summary: string;
}> {
  const res = await fetch('/api/dify/missing-docs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ claim_id }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `Missing documentation check failed (${res.status})`);
  return json;
}

// ── DSL Scan ─────────────────────────────────────────────────────────────────

export type ScanSummary = {
  scanned_files: string[];
  new_nodes: { workflow: string; node: string; type: string }[];
  changed_nodes: { workflow: string; node: string; type: string }[];
  already_pending: { workflow: string; node: string }[];
  unchanged_nodes: { workflow: string; node: string }[];
  errors: { file: string; error: string }[];
  totals: {
    files: number;
    new: number;
    changed: number;
    already_pending: number;
    unchanged: number;
    errors: number;
  };
};

export type DslStatus = {
  storage_bucket: string;
  files_in_folder: string[];
  stored_workflows: Record<string, number>;
  pending_approvals: number;
};

export function getDslStatus() {
  return get<DslStatus>('/dsl/status');
}

export function scanDslFolder(submitted_by: string) {
  return post<ScanSummary>(`/dsl/scan?submitted_by=${encodeURIComponent(submitted_by)}`, {});
}

// ── Workflow Snapshots (whole-file version history, dsl-governance-history branch) ─

export type SnapshotCommit = {
  sha: string;
  short_sha: string;
  message: string;
  date: string;
  author: string;
};

export type SnapshotHistory = {
  file: string;
  branch: string;
  commits: SnapshotCommit[];
  compare_url: string | null;
};

export type SnapshotResult = {
  file: string;
  status: 'ok' | 'error';
  commit_sha?: string;
  commit_url?: string;
  detail?: string;
};

export type SnapshotRunResult = {
  branch: string;
  results: SnapshotResult[];
};

export function getSnapshotFiles() {
  return get<{ files: string[] }>('/dsl/snapshot-files');
}

export function getWorkflowSnapshots(file: string, limit?: number) {
  return get<SnapshotHistory>('/dsl/snapshots', { file, limit });
}

export function takeWorkflowSnapshot(files: string[] | null, by: string, reason: string) {
  return post<SnapshotRunResult>('/dsl/snapshots', { files, by, reason });
}

// ── Snapshot Node Diff (latest snapshot vs. current, node-level only) ──────────

export type ChangedNode = {
  node_name: string;
  node_type: 'llm' | 'code' | 'agent';
  status: 'changed' | 'added' | 'removed';
  diff_content: string;
};

export type SnapshotNodeDiff = {
  file: string;
  snapshot_sha: string;
  snapshot_short_sha: string;
  snapshot_date: string;
  snapshot_message: string;
  changed_nodes: ChangedNode[];
  unchanged_count: number;
};

export function getSnapshotNodeDiff(file: string) {
  return get<SnapshotNodeDiff>('/dsl/snapshots/node-diff', { file });
}

// ── Upload Workflow (lands directly in the dify-workflows Storage bucket) ──────

export type UploadResult = {
  filename: string;
  size: number;
  node_count: number;
  workflow_name: string;
  uploaded_by: string;
};

export async function uploadWorkflowFile(file: File, uploaded_by: string): Promise<UploadResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('uploaded_by', uploaded_by);
  const res = await fetch(`${BASE}/dsl/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `MCP POST /dsl/upload → ${res.status}`);
  }
  return res.json();
}
