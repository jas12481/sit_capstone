'use client';

import { useState, useEffect, useCallback } from 'react';
import { useSession, signOut } from 'next-auth/react';
import {
  getChangeApprovals,
  getWorkflowNodes,
  approveChange,
  rejectChange,
  scanDslFolder,
  getDslStatus,
  getSnapshotFiles,
  getWorkflowSnapshots,
  takeWorkflowSnapshot,
  getSnapshotNodeDiff,
  uploadWorkflowFile,
  checkUploadDuplicate,
  type ChangeApproval,
  type WorkflowNode,
  type ScanSummary,
  type DslStatus,
  type SnapshotHistory,
  type SnapshotRunResult,
  type SnapshotNodeDiff,
  type ChangedNode,
  type UploadResult,
  type UploadDuplicateCheck,
} from '@/lib/mcp';
import { fmtDateTime } from '@/lib/fmt';

type Tab = 'pending' | 'history' | 'nodes' | 'snapshots';

// ── Node content parser & viewer ─────────────────────────────────────────────

function parseLlmContent(content: string) {
  const sections: Record<string, string> = {};
  // Split on [tag] markers at line start
  const parts = content.split(/\n(?=\[(?:model|system|user|schema)\])/);
  for (const part of parts) {
    const m = part.match(/^\[(\w+)\]\n?([\s\S]*)/);
    if (m) sections[m[1]] = m[2].trim();
  }
  return sections;
}

function NodeContentViewer({ node }: { node: WorkflowNode }) {
  const { node_type, node_content } = node;

  if (node_type === 'code') {
    return (
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Python Code</p>
        <pre className="bg-gray-950 text-green-300 text-xs font-mono rounded-lg p-4 overflow-x-auto max-h-80 overflow-y-auto leading-5 whitespace-pre">
          {node_content}
        </pre>
      </div>
    );
  }

  if (node_type === 'llm') {
    const sections = parseLlmContent(node_content);
    return (
      <div className="space-y-3">
        {sections.model && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Model</p>
            <p className="text-xs font-mono text-gray-600 bg-gray-50 rounded px-3 py-1.5">{sections.model}</p>
          </div>
        )}
        {sections.system && (
          <div>
            <p className="text-xs font-semibold text-purple-600 uppercase tracking-wide mb-1">System Prompt</p>
            <pre className="bg-purple-50 border border-purple-100 text-xs text-gray-800 rounded-lg px-3 py-2.5 whitespace-pre-wrap max-h-60 overflow-y-auto leading-5">{sections.system}</pre>
          </div>
        )}
        {sections.user && (
          <div>
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">Query</p>
            <pre className="bg-blue-50 border border-blue-100 text-xs text-gray-800 rounded-lg px-3 py-2.5 whitespace-pre-wrap max-h-48 overflow-y-auto leading-5">{sections.user}</pre>
          </div>
        )}
        {sections.schema && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Output Schema</p>
            <pre className="bg-gray-50 border border-gray-200 text-xs font-mono text-gray-600 rounded-lg px-3 py-2.5 whitespace-pre overflow-x-auto max-h-60 overflow-y-auto leading-5">
              {(() => { try { return JSON.stringify(JSON.parse(sections.schema), null, 2); } catch { return sections.schema; } })()}
            </pre>
          </div>
        )}
      </div>
    );
  }

  if (node_type === 'agent') {
    let parsed: {
      strategy?: string;
      model?: string;
      instruction?: string;
      query?: string;
      tools?: { tool_name: string; provider: string; enabled: boolean }[];
    } = {};
    try { parsed = JSON.parse(node_content); } catch { /* raw fallback */ }
    return (
      <div className="space-y-3">
        <div className="flex items-center gap-4 text-xs text-gray-500">
          {parsed.strategy && <span><span className="font-semibold">Strategy:</span> {parsed.strategy}</span>}
          {parsed.model && <span><span className="font-semibold">Model:</span> {parsed.model}</span>}
        </div>
        {parsed.instruction && (
          <div>
            <p className="text-xs font-semibold text-orange-600 uppercase tracking-wide mb-1">Instruction</p>
            <pre className="bg-orange-50 border border-orange-100 text-xs text-gray-800 rounded-lg px-3 py-2.5 whitespace-pre-wrap max-h-60 overflow-y-auto leading-5">{parsed.instruction}</pre>
          </div>
        )}
        {parsed.query && (
          <div>
            <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-1">Query</p>
            <pre className="bg-blue-50 border border-blue-100 text-xs text-gray-800 rounded-lg px-3 py-2.5 whitespace-pre-wrap max-h-40 overflow-y-auto leading-5">{parsed.query}</pre>
          </div>
        )}
        {parsed.tools && parsed.tools.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Tools ({parsed.tools.length})</p>
            <div className="space-y-1.5">
              {parsed.tools.map((t, i) => (
                <div key={i} className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
                  <span className="text-xs font-medium text-gray-800">{t.tool_name}</span>
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-400 font-mono truncate max-w-[180px]">{t.provider}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${t.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-400'}`}>
                      {t.enabled ? 'enabled' : 'disabled'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        {!parsed.strategy && !parsed.instruction && (
          <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap">{node_content}</pre>
        )}
      </div>
    );
  }

  return <pre className="text-xs text-gray-600 bg-gray-50 rounded-lg p-3 whitespace-pre-wrap max-h-60 overflow-y-auto">{node_content}</pre>;
}

function StatusBadge({ status }: { status: string }) {
  const s = {
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
  }[status] ?? 'bg-gray-100 text-gray-700';
  return <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold ${s}`}>{status}</span>;
}

function NodeTypeBadge({ type }: { type: string }) {
  const s = { llm: 'bg-purple-100 text-purple-800', code: 'bg-blue-100 text-blue-800', agent: 'bg-orange-100 text-orange-800' }[type] ?? 'bg-gray-100 text-gray-700';
  return <span className={`inline-flex px-2 py-0.5 rounded text-xs font-mono font-semibold ${s}`}>{type}</span>;
}

function DiffViewer({ diff }: { diff: string }) {
  if (!diff) return <p className="text-gray-400 text-sm italic">No diff stored.</p>;
  const lines = diff.split('\n');
  return (
    <pre className="text-xs font-mono overflow-x-auto max-h-96 overflow-y-auto leading-5 rounded-lg bg-gray-950 text-gray-100 p-4">
      {lines.map((line, i) => {
        const colour =
          line.startsWith('+') && !line.startsWith('+++') ? 'text-green-400' :
          line.startsWith('-') && !line.startsWith('---') ? 'text-red-400' :
          line.startsWith('@@') ? 'text-blue-300' :
          line.startsWith('===') ? 'text-yellow-300' :
          'text-gray-300';
        return <span key={i} className={`block ${colour}`}>{line}</span>;
      })}
    </pre>
  );
}

function ApprovalForm({
  approval,
  verifiedName,
  onDone,
}: {
  approval: ChangeApproval;
  verifiedName: string;
  onDone: () => void;
}) {
  const [reason, setReason] = useState('');
  const [acting, setActing] = useState<'approve' | 'reject' | null>(null);
  const [error, setError] = useState('');

  async function act(action: 'approve' | 'reject') {
    if (!verifiedName.trim() || !reason.trim()) {
      setError(!verifiedName.trim() ? 'Your Okta identity could not be verified.' : 'A justification is required.');
      return;
    }
    setActing(action);
    setError('');
    try {
      if (action === 'approve') {
        await approveChange(approval.approval_id, verifiedName, reason);
      } else {
        await rejectChange(approval.approval_id, verifiedName, reason);
      }
      onDone();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Action failed');
    } finally {
      setActing(null);
    }
  }

  return (
    <div className="mt-4 border-t border-gray-100 pt-4 space-y-3">
      <h4 className="text-xs font-semibold text-gray-600 uppercase tracking-wide">Sign off</h4>
      <div className="flex gap-3">
        <div className="flex-1 border border-gray-200 bg-gray-50 rounded-lg px-3 py-2 text-sm text-gray-700 flex items-center gap-2">
          <svg className="w-3.5 h-3.5 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {verifiedName || 'Not signed in'}
        </div>
        <input
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="Justification (required)"
          value={reason}
          onChange={e => setReason(e.target.value)}
        />
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={() => act('approve')}
          disabled={!!acting}
          className="bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
        >
          {acting === 'approve' ? 'Approving…' : 'Approve'}
        </button>
        <button
          onClick={() => act('reject')}
          disabled={!!acting}
          className="bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
        >
          {acting === 'reject' ? 'Rejecting…' : 'Reject'}
        </button>
      </div>
    </div>
  );
}

function ApprovalCard({
  approval,
  showForm,
  verifiedName,
  onDone,
}: {
  approval: ChangeApproval;
  showForm: boolean;
  verifiedName: string;
  onDone: () => void;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition text-left"
      >
        <div className="flex items-center gap-3 min-w-0">
          <StatusBadge status={approval.status} />
          <span className="font-medium text-gray-900 text-sm truncate">{approval.workflow_name}</span>
          <span className="text-gray-400 text-sm">—</span>
          <span className="text-gray-600 text-sm truncate">{approval.node_name}</span>
        </div>
        <div className="flex items-center gap-4 flex-shrink-0">
          <span className="text-xs text-gray-400">{approval.changed_by}</span>
          <span className="text-xs text-gray-400">
            {fmtDateTime(approval.created_at)}
          </span>
          <svg className={`w-4 h-4 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-gray-100">
          <div className="mt-4 space-y-2 text-sm">
            {approval.approved_by && (
              <p><span className="text-gray-500">Actioned by:</span> {approval.approved_by}</p>
            )}
            {approval.change_reason && (
              <p><span className="text-gray-500">Reason:</span> {approval.change_reason}</p>
            )}
            {approval.git_commit_hash && (
              <p>
                <span className="text-gray-500">Git commit: </span>
                <a
                  href={`https://github.com/${process.env.NEXT_PUBLIC_GITHUB_REPO}/commit/${approval.git_commit_hash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-mono text-xs text-brand-600 hover:underline"
                >
                  {approval.git_commit_hash.slice(0, 12)}…
                </a>
              </p>
            )}
          </div>
          <div className="mt-4">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Diff</h4>
            <DiffViewer diff={approval.diff_content} />
          </div>
          {showForm && <ApprovalForm approval={approval} verifiedName={verifiedName} onDone={onDone} />}
        </div>
      )}
    </div>
  );
}

function NodeTable({ nodes }: { nodes: WorkflowNode[] }) {
  const [expanded, setExpanded] = useState<string | null>(null);

  function toggle(id: string) {
    setExpanded(prev => prev === id ? null : id);
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 bg-gray-50">
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Workflow</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Node</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Type</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Version</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Hash</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Committed</th>
            <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">By</th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {nodes.map(n => (
            <>
              <tr
                key={n.node_id}
                className="hover:bg-gray-50 cursor-pointer transition-colors"
                onClick={() => toggle(n.node_id)}
              >
                <td className="px-4 py-2.5 text-gray-700 font-medium text-xs">{n.workflow_name}</td>
                <td className="px-4 py-2.5 text-gray-800 text-xs font-medium">{n.node_name}</td>
                <td className="px-4 py-2.5"><NodeTypeBadge type={n.node_type} /></td>
                <td className="px-4 py-2.5 text-gray-500 text-xs">{n.workflow_version || '—'}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-gray-400">{n.content_hash?.slice(0, 10)}…</td>
                <td className="px-4 py-2.5 text-gray-400 text-xs">
                  {fmtDateTime(n.committed_at)}
                </td>
                <td className="px-4 py-2.5 text-gray-500 text-xs">{n.committed_by || '—'}</td>
                <td className="px-4 py-2.5 text-gray-400">
                  <svg
                    className={`w-4 h-4 transition-transform ${expanded === n.node_id ? 'rotate-180' : ''}`}
                    fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </td>
              </tr>
              {expanded === n.node_id && (
                <tr key={`${n.node_id}-exp`} className="bg-gray-50">
                  <td colSpan={8} className="px-6 py-4">
                    <NodeContentViewer node={n} />
                  </td>
                </tr>
              )}
            </>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
}

function NodeDiffStatusBadge({ status }: { status: ChangedNode['status'] }) {
  const s = {
    changed: 'bg-orange-100 text-orange-800',
    added: 'bg-blue-100 text-blue-800',
    removed: 'bg-red-100 text-red-800',
  }[status];
  return <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold ${s}`}>{status}</span>;
}

// The backend's snapshot endpoints (list/history/diff/take) all key on "dify-data/{name}"
// strings for continuity with existing GitHub governance-branch commit paths — that's an
// internal implementation detail, not where the content actually lives (it's the
// dify-workflows Storage bucket). Strip the prefix for anything shown to a user.
function displayName(path: string): string {
  return path.replace(/^dify-data\//, '');
}

function SnapshotPanel({ verifiedName }: { verifiedName: string }) {
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [history, setHistory] = useState<SnapshotHistory | null>(null);
  const [histLoading, setHistLoading] = useState(false);
  const [histError, setHistError] = useState('');

  const [nodeDiff, setNodeDiff] = useState<SnapshotNodeDiff | null>(null);
  const [nodeDiffLoading, setNodeDiffLoading] = useState(false);
  const [nodeDiffError, setNodeDiffError] = useState('');
  const [expandedNode, setExpandedNode] = useState<string | null>(null);

  const [reason, setReason] = useState('');
  const [taking, setTaking] = useState<'selected' | 'all' | null>(null);
  const [takeError, setTakeError] = useState('');
  const [takeResult, setTakeResult] = useState<SnapshotRunResult | null>(null);

  const [uploadFileObj, setUploadFileObj] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [duplicateCheck, setDuplicateCheck] = useState<UploadDuplicateCheck | null>(null);
  const [checkingDuplicate, setCheckingDuplicate] = useState(false);

  const loadFiles = useCallback(async (selectName?: string) => {
    try {
      const r = await getSnapshotFiles();
      setFiles(r.files);
      if (selectName) {
        setSelectedFile(`dify-data/${selectName}`);
      } else if (r.files.length > 0 && !selectedFile) {
        setSelectedFile(r.files[0]);
      }
    } catch {
      setHistError('Could not load workflow file list.');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => { loadFiles(); }, [loadFiles]);

  const existingFileNames = files.map(f => f.split('/').pop());
  const uploadWouldOverwrite = uploadFileObj && existingFileNames.includes(uploadFileObj.name);

  async function handleFileSelect(f: File | null) {
    setUploadFileObj(f);
    setUploadError('');
    setUploadResult(null);
    setDuplicateCheck(null);
    if (!f) return;
    setCheckingDuplicate(true);
    try {
      const check = await checkUploadDuplicate(f);
      setDuplicateCheck(check);
    } catch {
      // Non-blocking pre-check — a failure here shouldn't stop the user from
      // uploading, so just skip showing a duplicate warning.
    } finally {
      setCheckingDuplicate(false);
    }
  }

  async function handleUpload() {
    if (!uploadFileObj) return;
    if (!verifiedName) {
      setUploadError('Your Okta identity could not be verified — try signing in again.');
      return;
    }
    setUploading(true);
    setUploadError('');
    setUploadResult(null);
    try {
      const result = await uploadWorkflowFile(uploadFileObj, verifiedName);
      setUploadResult(result);
      setUploadFileObj(null);
      setDuplicateCheck(null);
      await loadFiles(result.filename);
    } catch (e: unknown) {
      setUploadError(e instanceof Error ? e.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  const loadHistory = useCallback(async (file: string) => {
    if (!file) return;
    setHistLoading(true);
    setHistError('');
    try {
      const h = await getWorkflowSnapshots(file);
      setHistory(h);
    } catch (e: unknown) {
      setHistError(e instanceof Error ? e.message : 'Failed to load snapshot history — has the dsl-governance-history branch been created yet?');
      setHistory(null);
    } finally {
      setHistLoading(false);
    }
  }, []);

  useEffect(() => { loadHistory(selectedFile); }, [selectedFile, loadHistory]);

  const loadNodeDiff = useCallback(async (file: string) => {
    if (!file) return;
    setNodeDiffLoading(true);
    setNodeDiffError('');
    try {
      const d = await getSnapshotNodeDiff(file);
      setNodeDiff(d);
    } catch (e: unknown) {
      // A 404 here just means no snapshot exists yet — not a real error.
      setNodeDiffError(e instanceof Error ? e.message : 'Failed to load node-level diff');
      setNodeDiff(null);
    } finally {
      setNodeDiffLoading(false);
    }
  }, []);

  useEffect(() => { loadNodeDiff(selectedFile); setExpandedNode(null); }, [selectedFile, loadNodeDiff]);

  async function take(scope: 'selected' | 'all') {
    if (!verifiedName) {
      setTakeError('Your Okta identity could not be verified — try signing in again.');
      return;
    }
    if (!reason.trim()) {
      setTakeError('A reason for this snapshot is required.');
      return;
    }
    setTaking(scope);
    setTakeError('');
    setTakeResult(null);
    try {
      const result = await takeWorkflowSnapshot(scope === 'all' ? null : [selectedFile], verifiedName, reason);
      setTakeResult(result);
      if (selectedFile) {
        await loadHistory(selectedFile);
        await loadNodeDiff(selectedFile);
      }
    } catch (e: unknown) {
      setTakeError(e instanceof Error ? e.message : 'Snapshot failed');
    } finally {
      setTaking(null);
    }
  }

  const githubRepo = process.env.NEXT_PUBLIC_GITHUB_REPO;

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-gray-800">Upload Workflow</h2>
        <p className="text-xs text-gray-500 mt-0.5 mb-4">
          Upload an exported Dify DSL YAML directly — lands in Storage immediately, becomes
          &quot;current&quot; for scanning/snapshotting/comparison. No manual file placement or
          backend access needed.
        </p>

        <div className="flex flex-wrap gap-3 items-center">
          <input
            type="file"
            accept=".yml,.yaml"
            onChange={e => handleFileSelect(e.target.files?.[0] ?? null)}
            className="text-sm text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-gray-100 file:text-gray-700 hover:file:bg-gray-200"
          />
          <button
            onClick={handleUpload}
            disabled={!uploadFileObj || uploading}
            className="bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-lg transition"
          >
            {uploading ? 'Uploading…' : 'Upload'}
          </button>
        </div>

        {uploadWouldOverwrite && !uploading && (
          <p className="mt-3 text-xs text-orange-600">
            &quot;{uploadFileObj?.name}&quot; already exists in the bucket — uploading will overwrite
            the current version. Take a snapshot first if you want to preserve what&apos;s there now.
          </p>
        )}

        {checkingDuplicate && (
          <p className="mt-3 text-xs text-gray-400">Checking for duplicate content…</p>
        )}

        {!checkingDuplicate && duplicateCheck?.duplicate_of && !uploading && (
          <p className="mt-3 text-xs text-orange-600">
            ⚠ This file&apos;s tracked node content (LLM/code/agent nodes) is identical to &quot;
            {duplicateCheck.duplicate_of}&quot;, already in Storage. If this really is the same
            workflow, consider re-uploading it as &quot;{duplicateCheck.duplicate_of}&quot; instead
            to avoid a duplicate entry. If it differs in ways outside tracked nodes (layout, other
            node types, workflow settings), this separate file is fine to keep.
          </p>
        )}

        {uploadError && <p className="mt-3 text-xs text-red-600">{uploadError}</p>}

        {uploadResult && (
          <p className="mt-3 text-xs text-green-600">
            ✓ Uploaded {uploadResult.filename} — {uploadResult.node_count} trackable node(s) found
            in workflow &quot;{uploadResult.workflow_name}&quot;.
          </p>
        )}
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h2 className="text-sm font-semibold text-gray-800">Workflow Snapshots</h2>
        <p className="text-xs text-gray-500 mt-0.5 mb-4">
          Full whole-file version history of every workflow YAML in the dify-workflows Storage
          bucket, committed to a dedicated
          <code className="font-mono bg-gray-100 px-1 rounded mx-1">dsl-governance-history</code>
          branch — kept separate from regular app-code commits on main.
        </p>

        <div className="flex flex-wrap gap-3 items-center">
          <select
            value={selectedFile}
            onChange={e => setSelectedFile(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 w-72"
          >
            {files.length === 0 && <option value="">No workflow files found</option>}
            {files.map(f => (
              <option key={f} value={f}>{displayName(f)}</option>
            ))}
          </select>
          <input
            className="flex-1 min-w-[240px] border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            placeholder="Reason for this snapshot (required)"
            value={reason}
            onChange={e => setReason(e.target.value)}
          />
          <button
            onClick={() => take('selected')}
            disabled={!!taking || !selectedFile}
            className="bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-lg transition"
          >
            {taking === 'selected' ? 'Snapshotting…' : 'Snapshot This File'}
          </button>
          <button
            onClick={() => take('all')}
            disabled={!!taking || files.length === 0}
            className="bg-gray-700 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-lg transition"
          >
            {taking === 'all' ? 'Snapshotting…' : `Snapshot All (${files.length})`}
          </button>
        </div>

        {takeError && <p className="mt-3 text-xs text-red-600">{takeError}</p>}

        {takeResult && (
          <div className="mt-4 space-y-1">
            {takeResult.results.map((r, i) => (
              <p key={i} className="text-xs">
                {r.status === 'ok' ? (
                  <span className="text-green-600">✓ {displayName(r.file)}</span>
                ) : (
                  <span className="text-red-600">✗ {displayName(r.file)}: {r.detail}</span>
                )}
              </p>
            ))}
          </div>
        )}
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">
          Changes Since Last Snapshot — {selectedFile ? displayName(selectedFile) : '(no file selected)'}
        </h3>
        <p className="text-xs text-gray-400 mb-3">
          Node-level comparison: latest snapshot vs. current version — only nodes that actually
          differ are shown, not a raw whole-file diff.
        </p>

        {nodeDiffLoading && <p className="text-sm text-gray-400">Loading…</p>}

        {!nodeDiffLoading && nodeDiffError && (
          <p className="text-xs text-gray-400">
            No snapshot exists yet for this file — take one above to enable comparison.
          </p>
        )}

        {!nodeDiffLoading && !nodeDiffError && nodeDiff && (
          <div>
            <p className="text-xs text-gray-400 mb-3">
              Comparing against <span className="font-mono text-gray-600">{nodeDiff.snapshot_short_sha}</span>
              {' '}({fmtDateTime(nodeDiff.snapshot_date)}) — {nodeDiff.unchanged_count} node(s) unchanged.
            </p>

            {nodeDiff.changed_nodes.length === 0 ? (
              <p className="text-xs text-green-600 font-medium">
                ✓ No changes since the last snapshot.
              </p>
            ) : (
              <div className="space-y-2">
                {nodeDiff.changed_nodes.map(n => (
                  <div key={n.node_name} className="border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      onClick={() => setExpandedNode(prev => prev === n.node_name ? null : n.node_name)}
                      className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-gray-50 transition text-left"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <NodeDiffStatusBadge status={n.status} />
                        <NodeTypeBadge type={n.node_type} />
                        <span className="text-sm text-gray-800 truncate">{n.node_name}</span>
                      </div>
                      <svg
                        className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${expandedNode === n.node_name ? 'rotate-180' : ''}`}
                        fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {expandedNode === n.node_name && (
                      <div className="px-4 pb-4">
                        <DiffViewer diff={n.diff_content} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h3 className="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-3">
          History — {selectedFile ? displayName(selectedFile) : '(no file selected)'}
        </h3>

        {histLoading && <p className="text-sm text-gray-400">Loading…</p>}
        {histError && (
          <p className="text-xs text-orange-600">{histError}</p>
        )}

        {!histLoading && !histError && history && (
          history.commits.length === 0 ? (
            <p className="text-sm text-gray-400">
              No snapshots yet for this file. Click <strong>Snapshot This File</strong> above to create the first one.
            </p>
          ) : (
            <div className="space-y-2">
              {history.compare_url && (
                <a
                  href={history.compare_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-block text-xs text-brand-600 hover:underline mb-2"
                >
                  Compare latest two versions →
                </a>
              )}
              {history.commits.map(c => (
                <div key={c.sha} className="flex items-center justify-between border border-gray-100 rounded-lg px-3 py-2 text-xs">
                  <div className="flex items-center gap-3 min-w-0">
                    <a
                      href={githubRepo ? `https://github.com/${githubRepo}/commit/${c.sha}` : '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-mono text-brand-600 hover:underline flex-shrink-0"
                    >
                      {c.short_sha}
                    </a>
                    <span className="text-gray-600 truncate">{c.message}</span>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0 text-gray-400">
                    <span>{c.author}</span>
                    <span>{fmtDateTime(c.date)}</span>
                  </div>
                </div>
              ))}
            </div>
          )
        )}
      </div>
    </div>
  );
}

export default function DslPage() {
  const { data: session } = useSession();
  const verifiedName = session?.user?.name || session?.user?.email || '';

  const [tab, setTab] = useState<Tab>('pending');
  const [pending, setPending] = useState<ChangeApproval[]>([]);
  const [history, setHistory] = useState<ChangeApproval[]>([]);
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [workflowFilter, setWorkflowFilter] = useState('');

  // Scan state
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<ScanSummary | null>(null);
  const [scanError, setScanError] = useState('');
  const [dslStatus, setDslStatus] = useState<DslStatus | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [p, h, n, status] = await Promise.all([
        getChangeApprovals({ status: 'pending', limit: 100 }),
        getChangeApprovals({ limit: 100 }),
        getWorkflowNodes(workflowFilter || undefined),
        getDslStatus().catch(() => null),
      ]);
      setPending(p);
      setHistory(h.filter(a => a.status !== 'pending'));
      setNodes(n);
      setDslStatus(status);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [workflowFilter]);

  useEffect(() => { reload(); }, [reload]);

  async function runScan() {
    if (!verifiedName) {
      setScanError('Your Okta identity could not be verified — try signing in again.');
      return;
    }
    setScanning(true);
    setScanResult(null);
    setScanError('');
    try {
      const result = await scanDslFolder(verifiedName);
      setScanResult(result);
      // Refresh pending list if new approvals were created
      if (result.totals.changed > 0) await reload();
    } catch (e: unknown) {
      setScanError(e instanceof Error ? e.message : 'Scan failed');
    } finally {
      setScanning(false);
    }
  }

  const TABS: { id: Tab; label: string; count?: number }[] = [
    { id: 'pending', label: 'Pending Approvals', count: pending.length },
    { id: 'history', label: 'History' },
    { id: 'nodes', label: 'Stored Nodes' },
    { id: 'snapshots', label: 'Workflow Snapshots' },
  ];

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">DSL Change Management</h1>
          <p className="text-sm text-gray-500 mt-1">Governed version control for Dify workflow configurations</p>
        </div>
        {verifiedName && (
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 text-green-600" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Signed in as <span className="font-medium text-gray-700">{verifiedName}</span> (Okta)
            </span>
            <button onClick={() => signOut()} className="text-gray-400 hover:text-gray-600 underline">
              Sign out
            </button>
          </div>
        )}
      </div>

      {/* Scan panel */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">Scan Workflow Storage</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Reads all YAMLs in the dify-workflows Storage bucket, detects changes, and creates pending approvals automatically.
              {dslStatus && (
                <span className="ml-2 text-gray-400">
                  {dslStatus.files_in_folder.length} file{dslStatus.files_in_folder.length !== 1 ? 's' : ''} in bucket
                  · {dslStatus.pending_approvals} pending
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex gap-3 items-center">
          <button
            onClick={runScan}
            disabled={scanning}
            className="bg-brand-500 hover:bg-brand-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium px-5 py-2 rounded-lg transition flex items-center gap-2"
          >
            {scanning ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Scanning…
              </>
            ) : 'Scan for Pending Changes'}
          </button>
        </div>

        {scanError && (
          <p className="mt-3 text-xs text-red-600">{scanError}</p>
        )}

        {/* Scan results */}
        {scanResult && (
          <div className="mt-4 space-y-3">
            <div className="grid grid-cols-5 gap-2">
              {[
                { label: 'Files scanned', value: scanResult.totals.files, colour: 'text-gray-700' },
                { label: 'New (baselined)', value: scanResult.totals.new, colour: 'text-blue-600' },
                { label: 'Changed', value: scanResult.totals.changed, colour: scanResult.totals.changed > 0 ? 'text-orange-600' : 'text-gray-400' },
                { label: 'Unchanged', value: scanResult.totals.unchanged, colour: 'text-green-600' },
                { label: 'Errors', value: scanResult.totals.errors, colour: scanResult.totals.errors > 0 ? 'text-red-600' : 'text-gray-400' },
              ].map(s => (
                <div key={s.label} className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className={`text-xl font-bold ${s.colour}`}>{s.value}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>

            {scanResult.totals.changed > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 text-xs text-orange-800">
                <p className="font-semibold mb-1">{scanResult.totals.changed} node(s) changed — pending approvals created:</p>
                <ul className="space-y-0.5">
                  {scanResult.changed_nodes.map((n, i) => (
                    <li key={i}>• [{n.type.toUpperCase()}] {n.workflow} — {n.node}</li>
                  ))}
                </ul>
              </div>
            )}

            {scanResult.totals.new > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-xs text-blue-800">
                <p className="font-semibold mb-1">{scanResult.totals.new} new node(s) baselined:</p>
                <ul className="space-y-0.5">
                  {scanResult.new_nodes.map((n, i) => (
                    <li key={i}>• [{n.type.toUpperCase()}] {n.workflow} — {n.node}</li>
                  ))}
                </ul>
              </div>
            )}

            {scanResult.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-xs text-red-800">
                {scanResult.errors.map((e, i) => (
                  <p key={i}><span className="font-semibold">{e.file}:</span> {e.error}</p>
                ))}
              </div>
            )}

            {scanResult.totals.changed === 0 && scanResult.totals.new === 0 && scanResult.totals.errors === 0 && (
              <p className="text-xs text-green-600 font-medium">✓ All nodes are up to date — no changes detected.</p>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">{error}</div>
      )}

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-gray-200">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition -mb-px flex items-center gap-2 ${
              tab === t.id
                ? 'border-brand-500 text-brand-700'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {t.label}
            {t.count != null && t.count > 0 && (
              <span className="bg-brand-500 text-white text-xs rounded-full px-1.5 py-0.5 leading-none">
                {t.count}
              </span>
            )}
          </button>
        ))}
        <div className="ml-auto pb-1">
          <button
            onClick={reload}
            className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5 rounded-md border border-gray-200 hover:border-gray-300 transition"
          >
            Refresh
          </button>
        </div>
      </div>

      {loading && <div className="text-center py-16 text-gray-400 text-sm">Loading…</div>}

      {!loading && tab === 'pending' && (
        <div className="space-y-3">
          {pending.length === 0 ? (
            <div className="text-center py-16 text-gray-400 text-sm">
              No pending approvals. Click <strong>Scan Workflow Storage</strong> above to detect changes.
            </div>
          ) : (
            pending.map(a => (
              <ApprovalCard key={a.approval_id} approval={a} showForm verifiedName={verifiedName} onDone={reload} />
            ))
          )}
        </div>
      )}

      {!loading && tab === 'history' && (
        <div className="space-y-3">
          {history.length === 0 ? (
            <div className="text-center py-16 text-gray-400 text-sm">No approved or rejected changes yet.</div>
          ) : (
            history.map(a => (
              <ApprovalCard key={a.approval_id} approval={a} showForm={false} verifiedName={verifiedName} onDone={reload} />
            ))
          )}
        </div>
      )}

      {!loading && tab === 'nodes' && (() => {
        // Derive unique workflow names for dropdown
        const workflowNames = nodes
          .map(n => n.workflow_name)
          .filter((v, i, a) => a.indexOf(v) === i)
          .sort();

        const filtered = workflowFilter
          ? nodes.filter(n => n.workflow_name === workflowFilter)
          : nodes;

        return (
          <div className="space-y-4">
            <div className="flex gap-3 items-center">
              <select
                value={workflowFilter}
                onChange={e => setWorkflowFilter(e.target.value)}
                className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 w-72"
              >
                <option value="">All workflows ({nodes.length} nodes)</option>
                {workflowNames.map(wf => (
                  <option key={wf} value={wf}>
                    {wf} ({nodes.filter(n => n.workflow_name === wf).length} nodes)
                  </option>
                ))}
              </select>
              {workflowFilter && (
                <button
                  onClick={() => setWorkflowFilter('')}
                  className="text-xs text-gray-500 hover:text-gray-700 underline"
                >
                  Clear
                </button>
              )}
            </div>

            {filtered.length === 0 ? (
              <div className="text-center py-16 text-gray-400 text-sm">
                No nodes stored. Click <strong>Scan Workflow Storage</strong> above to baseline all workflows.
              </div>
            ) : (
              <NodeTable nodes={filtered} />
            )}
          </div>
        );
      })()}

      {!loading && tab === 'snapshots' && <SnapshotPanel verifiedName={verifiedName} />}
    </div>
  );
}
