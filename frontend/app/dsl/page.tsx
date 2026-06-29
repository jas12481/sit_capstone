'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  getChangeApprovals,
  getWorkflowNodes,
  approveChange,
  rejectChange,
  scanDslFolder,
  getDslStatus,
  type ChangeApproval,
  type WorkflowNode,
  type ScanSummary,
  type DslStatus,
} from '@/lib/mcp';

type Tab = 'pending' | 'history' | 'nodes';

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
  onDone,
}: {
  approval: ChangeApproval;
  onDone: () => void;
}) {
  const [name, setName] = useState('');
  const [reason, setReason] = useState('');
  const [acting, setActing] = useState<'approve' | 'reject' | null>(null);
  const [error, setError] = useState('');

  async function act(action: 'approve' | 'reject') {
    if (!name.trim() || !reason.trim()) {
      setError('Both name and reason are required.');
      return;
    }
    setActing(action);
    setError('');
    try {
      if (action === 'approve') {
        await approveChange(approval.approval_id, name, reason);
      } else {
        await rejectChange(approval.approval_id, name, reason);
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
        <input
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          placeholder="Your full name (required)"
          value={name}
          onChange={e => setName(e.target.value)}
        />
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
  onDone,
}: {
  approval: ChangeApproval;
  showForm: boolean;
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
            {approval.created_at ? new Date(approval.created_at).toLocaleString() : ''}
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
          {showForm && <ApprovalForm approval={approval} onDone={onDone} />}
        </div>
      )}
    </div>
  );
}

export default function DslPage() {
  const [tab, setTab] = useState<Tab>('pending');
  const [pending, setPending] = useState<ChangeApproval[]>([]);
  const [history, setHistory] = useState<ChangeApproval[]>([]);
  const [nodes, setNodes] = useState<WorkflowNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [workflowFilter, setWorkflowFilter] = useState('');

  // Scan state
  const [scanName, setScanName] = useState('');
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
    if (!scanName.trim()) {
      setScanError('Enter your name before scanning.');
      return;
    }
    setScanning(true);
    setScanResult(null);
    setScanError('');
    try {
      const result = await scanDslFolder(scanName.trim());
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
  ];

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">DSL Change Management</h1>
        <p className="text-sm text-gray-500 mt-1">Governed version control for Dify workflow configurations</p>
      </div>

      {/* Scan panel */}
      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h2 className="text-sm font-semibold text-gray-800">Scan dify-data/</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Reads all YAMLs in the folder, detects changes, and creates pending approvals automatically.
              {dslStatus && (
                <span className="ml-2 text-gray-400">
                  {dslStatus.files_in_folder.length} file{dslStatus.files_in_folder.length !== 1 ? 's' : ''} in folder
                  · {dslStatus.pending_approvals} pending
                </span>
              )}
            </p>
          </div>
        </div>

        <div className="flex gap-3 items-center">
          <input
            className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 w-56"
            placeholder="Your name (required)"
            value={scanName}
            onChange={e => setScanName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && runScan()}
          />
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
            ) : 'Scan dify-data/'}
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
              No pending approvals. Run <code className="font-mono bg-gray-100 px-1 rounded">python -m dsl_manager scan</code> to detect changes.
            </div>
          ) : (
            pending.map(a => (
              <ApprovalCard key={a.approval_id} approval={a} showForm onDone={reload} />
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
              <ApprovalCard key={a.approval_id} approval={a} showForm={false} onDone={reload} />
            ))
          )}
        </div>
      )}

      {!loading && tab === 'nodes' && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <input
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 w-64"
              placeholder="Filter by workflow name…"
              value={workflowFilter}
              onChange={e => setWorkflowFilter(e.target.value)}
            />
          </div>

          {nodes.length === 0 ? (
            <div className="text-center py-16 text-gray-400 text-sm">
              No nodes stored. Run <code className="font-mono bg-gray-100 px-1 rounded">python -m dsl_manager init</code> to baseline a workflow.
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
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
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {nodes.map(n => (
                    <tr key={n.node_id} className="hover:bg-gray-50">
                      <td className="px-4 py-2.5 text-gray-700 font-medium text-xs">{n.workflow_name}</td>
                      <td className="px-4 py-2.5 text-gray-600 text-xs">{n.node_name}</td>
                      <td className="px-4 py-2.5"><NodeTypeBadge type={n.node_type} /></td>
                      <td className="px-4 py-2.5 text-gray-500 text-xs">{n.workflow_version || '—'}</td>
                      <td className="px-4 py-2.5 font-mono text-xs text-gray-400">{n.content_hash?.slice(0, 10)}…</td>
                      <td className="px-4 py-2.5 text-gray-400 text-xs">
                        {n.committed_at ? new Date(n.committed_at).toLocaleString() : '—'}
                      </td>
                      <td className="px-4 py-2.5 text-gray-500 text-xs">{n.committed_by || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
