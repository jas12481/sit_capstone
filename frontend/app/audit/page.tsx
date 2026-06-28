'use client';

import { useState, useEffect, useCallback } from 'react';
import { getAssessmentLogs, type AssessmentLog } from '@/lib/mcp';

const WORKFLOW_TYPES = ['', 'life', 'health', 'critical_illness', 'disability'];
const RECOMMENDATIONS = ['', 'APPROVE', 'REJECT', 'REFER_FOR_FURTHER_REVIEW', 'PENDING'];
const CONFIDENCE_LEVELS = ['', 'high', 'medium', 'low'];

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const colour =
    pct >= 80 ? 'bg-green-100 text-green-800' :
    pct >= 60 ? 'bg-yellow-100 text-yellow-800' :
    'bg-red-100 text-red-800';
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colour}`}>{pct}%</span>;
}

function RecommendationBadge({ rec }: { rec: string }) {
  const colour =
    rec === 'APPROVE' ? 'bg-green-100 text-green-800' :
    rec === 'REJECT' ? 'bg-red-100 text-red-800' :
    rec === 'REFER_FOR_FURTHER_REVIEW' ? 'bg-orange-100 text-orange-800' :
    'bg-gray-100 text-gray-700';
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${colour}`}>{rec || '—'}</span>;
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AssessmentLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);

  const [filters, setFilters] = useState({
    workflow_type: '',
    recommendation: '',
    confidence_level: '',
    claim_id: '',
    limit: 100,
  });

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getAssessmentLogs(filters);
      setLogs(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { load(); }, [load]);

  function toggle(id: string) {
    setExpanded(prev => prev === id ? null : id);
  }

  return (
    <div className="p-6 max-w-full">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Audit Log</h1>
        <p className="text-sm text-gray-500 mt-1">All assessment decisions with full traceability</p>
      </div>

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-5 flex flex-wrap gap-3">
        <select
          value={filters.workflow_type}
          onChange={e => setFilters(f => ({ ...f, workflow_type: e.target.value }))}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All workflow types</option>
          {WORKFLOW_TYPES.slice(1).map(t => <option key={t} value={t}>{t}</option>)}
        </select>

        <select
          value={filters.recommendation}
          onChange={e => setFilters(f => ({ ...f, recommendation: e.target.value }))}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All recommendations</option>
          {RECOMMENDATIONS.slice(1).map(r => <option key={r} value={r}>{r}</option>)}
        </select>

        <select
          value={filters.confidence_level}
          onChange={e => setFilters(f => ({ ...f, confidence_level: e.target.value }))}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All confidence levels</option>
          {CONFIDENCE_LEVELS.slice(1).map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        <input
          type="text"
          placeholder="Claim ID (e.g. CLM-0003)"
          value={filters.claim_id}
          onChange={e => setFilters(f => ({ ...f, claim_id: e.target.value }))}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 w-48"
        />

        <button
          onClick={load}
          className="bg-brand-500 text-white rounded-lg px-4 py-2 text-sm font-medium hover:bg-brand-600 transition"
        >
          Apply filters
        </button>
      </div>

      {/* Stats strip */}
      {!loading && logs.length > 0 && (
        <div className="grid grid-cols-4 gap-3 mb-5">
          {[
            { label: 'Total', value: logs.length },
            { label: 'Approved', value: logs.filter(l => l.recommendation === 'APPROVE').length },
            { label: 'Rejected', value: logs.filter(l => l.recommendation === 'REJECT').length },
            {
              label: 'Avg Judge Score',
              value: (logs.reduce((s, l) => s + (l.judge_overall_score ?? 0), 0) / logs.length * 100).toFixed(0) + '%',
            },
          ].map(stat => (
            <div key={stat.label} className="bg-white border border-gray-200 rounded-xl p-4">
              <p className="text-xs text-gray-500">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Table */}
      {loading && (
        <div className="text-center py-20 text-gray-400 text-sm">Loading…</div>
      )}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">{error}</div>
      )}
      {!loading && !error && logs.length === 0 && (
        <div className="text-center py-20 text-gray-400 text-sm">No records found. Run an assessment in the Chat view first.</div>
      )}

      {!loading && logs.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Claim</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Workflow</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Verdict</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Confidence</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Judge Score</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Assessed</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map(log => (
                <>
                  <tr
                    key={log.id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => toggle(log.id)}
                  >
                    <td className="px-4 py-3 font-mono text-xs text-gray-700">{log.claim_id || '—'}</td>
                    <td className="px-4 py-3 text-gray-600 capitalize">{log.workflow_type}</td>
                    <td className="px-4 py-3"><RecommendationBadge rec={log.recommendation} /></td>
                    <td className="px-4 py-3 capitalize text-gray-600">{log.confidence_level || '—'}</td>
                    <td className="px-4 py-3">
                      {log.judge_overall_score != null
                        ? <ScoreBadge score={log.judge_overall_score} />
                        : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {log.assessed_at ? new Date(log.assessed_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      <svg className={`w-4 h-4 transition-transform ${expanded === log.id ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </td>
                  </tr>
                  {expanded === log.id && (
                    <tr key={`${log.id}-exp`} className="bg-gray-50">
                      <td colSpan={7} className="px-6 py-4">
                        <div className="grid grid-cols-2 gap-6 text-xs">
                          <div className="space-y-2">
                            <h4 className="font-semibold text-gray-700 text-sm">Assessment Details</h4>
                            <p><span className="text-gray-500">Rules passed:</span> {log.total_rules_passed ?? '—'}</p>
                            <p><span className="text-gray-500">Mandatory failed:</span> {log.mandatory_rules_failed ?? '—'}</p>
                            <p><span className="text-gray-500">Coverage:</span> {log.coverage_conclusion || '—'}</p>
                            <p><span className="text-gray-500">Model:</span> {log.model_version || '—'}</p>
                            <p><span className="text-gray-500">Prompt version:</span> {log.prompt_version || '—'}</p>
                          </div>
                          <div className="space-y-2">
                            <h4 className="font-semibold text-gray-700 text-sm">LLM-as-Judge Scores</h4>
                            <div className="space-y-1.5">
                              {[
                                ['Completeness', log.judge_completeness_score],
                                ['Consistency', log.judge_consistency_score],
                                ['Hallucination risk', log.judge_hallucination_risk_score],
                                ['Clarity', log.judge_clarity_score],
                                ['Overall', log.judge_overall_score],
                              ].map(([label, val]) => (
                                <div key={label as string} className="flex items-center justify-between">
                                  <span className="text-gray-500">{label}</span>
                                  {val != null ? <ScoreBadge score={val as number} /> : <span className="text-gray-300">—</span>}
                                </div>
                              ))}
                            </div>
                            {log.mlflow_run_id && (
                              <p className="pt-1">
                                <span className="text-gray-500">MLflow run: </span>
                                <span className="font-mono text-xs text-brand-600">{log.mlflow_run_id}</span>
                              </p>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
