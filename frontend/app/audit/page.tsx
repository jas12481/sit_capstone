'use client';

import { useState, useEffect, useMemo } from 'react';
import { getAssessmentLogs, getFraudRiskChecks, runFraudRiskCheck, createFraudRiskCheck, type AssessmentLog, type FraudRiskCheck } from '@/lib/mcp';
import { fmtDateTime } from '@/lib/fmt';

const RECOMMENDATIONS = ['APPROVE', 'REJECT', 'REFER_FOR_FURTHER_REVIEW', 'PENDING'];
const CONFIDENCE_LEVELS = ['high', 'medium', 'low'];

/**
 * Normalize a judge score to 0-100 regardless of storage scale.
 * Scores may be stored on a 0-1 or 0-5 scale depending on LLM output.
 */
function toPercent(score: number): number {
  if (score <= 1) return Math.round(score * 100);
  if (score <= 5) return Math.round((score / 5) * 100);
  return Math.min(100, Math.round(score));
}

function ScoreBadge({ score }: { score: number }) {
  const pct = toPercent(score);
  const colour =
    pct >= 80 ? 'bg-green-100 text-green-800' :
    pct >= 60 ? 'bg-yellow-100 text-yellow-800' :
    'bg-red-100 text-red-800';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colour}`}>
      {pct}%
    </span>
  );
}

function RiskBadge({ level }: { level: string }) {
  const colour =
    level === 'HIGH' ? 'bg-red-100 text-red-800' :
    level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
    'bg-green-100 text-green-800';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${colour}`}>
      {level}
    </span>
  );
}

function RecommendationBadge({ rec }: { rec: string }) {
  const colour =
    rec === 'APPROVE' ? 'bg-green-100 text-green-800' :
    rec === 'REJECT' ? 'bg-red-100 text-red-800' :
    rec === 'REFER_FOR_FURTHER_REVIEW' ? 'bg-orange-100 text-orange-800' :
    'bg-gray-100 text-gray-700';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${colour}`}>
      {rec || '—'}
    </span>
  );
}

export default function AuditPage() {
  const [allLogs, setAllLogs] = useState<AssessmentLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState<string | null>(null);

  // Filter state — all filtering is done client-side
  const [workflowFilter, setWorkflowFilter] = useState('');
  const [recFilter, setRecFilter] = useState('');
  const [confFilter, setConfFilter] = useState('');
  const [claimFilter, setClaimFilter] = useState('');

  // Fraud/Anomaly Risk Signals — on-demand per-row check, persisted so a
  // claim only needs to be checked once (latest result wins if re-checked).
  const [fraudChecks, setFraudChecks] = useState<Record<string, FraudRiskCheck>>({});
  const [checkingClaimId, setCheckingClaimId] = useState<string | null>(null);
  const [fraudError, setFraudError] = useState<string | null>(null);

  function loadFraudChecks() {
    getFraudRiskChecks({ limit: 500 })
      .then(checks => {
        // Results are ordered latest-first — keep only the first (most recent) per claim
        const byClaimId: Record<string, FraudRiskCheck> = {};
        for (const c of checks) {
          if (!byClaimId[c.claim_id]) byClaimId[c.claim_id] = c;
        }
        setFraudChecks(byClaimId);
      })
      .catch(() => {}); // non-critical — badges just won't show until this loads
  }

  async function handleFraudCheck(claimId: string) {
    setCheckingClaimId(claimId);
    setFraudError(null);
    try {
      const result = await runFraudRiskCheck(claimId);
      const saved = await createFraudRiskCheck({
        claim_id: claimId,
        risk_level: result.risk_level,
        flags: result.flags,
        recommended_action: result.recommended_action,
        checked_by: 'audit_log_ui',
      });
      setFraudChecks(prev => ({ ...prev, [claimId]: saved }));
    } catch (e) {
      setFraudError(e instanceof Error ? e.message : 'Fraud check failed');
    } finally {
      setCheckingClaimId(null);
    }
  }

  // Fetch everything once (server handles pagination via limit)
  useEffect(() => {
    setLoading(true);
    setError('');
    getAssessmentLogs({ limit: 500 })
      .then(setAllLogs)
      .catch(e => setError(e instanceof Error ? e.message : 'Failed to load'))
      .finally(() => setLoading(false));
    loadFraudChecks();
  }, []);

  // Derive unique workflow types from actual data
  const workflowTypes = useMemo(() => {
    const seen: Record<string, true> = {};
    const types = allLogs.map(l => l.workflow_type).filter((t): t is string => !!t).filter(t => {
      if (seen[t]) return false;
      seen[t] = true;
      return true;
    });
    return types.sort();
  }, [allLogs]);

  // Client-side filtering
  const logs = useMemo(() => {
    return allLogs.filter(l => {
      if (workflowFilter && !l.workflow_type?.toLowerCase().includes(workflowFilter.toLowerCase())) return false;
      if (recFilter && l.recommendation !== recFilter) return false;
      if (confFilter && l.confidence_level?.toLowerCase() !== confFilter.toLowerCase()) return false;
      if (claimFilter && !l.claim_id?.toLowerCase().includes(claimFilter.toLowerCase())) return false;
      return true;
    });
  }, [allLogs, workflowFilter, recFilter, confFilter, claimFilter]);

  // Stats from filtered view
  const stats = useMemo(() => {
    const scored = logs.filter(l => l.judge_overall_score != null);
    return {
      total: logs.length,
      approved: logs.filter(l => l.recommendation === 'APPROVE').length,
      rejected: logs.filter(l => l.recommendation === 'REJECT').length,
      avgJudge: scored.length > 0
        ? toPercent(scored.reduce((s, l) => s + l.judge_overall_score, 0) / scored.length)
        : null,
    };
  }, [logs]);

  function toggle(id: string) {
    setExpanded(prev => prev === id ? null : id);
  }

  function clearFilters() {
    setWorkflowFilter('');
    setRecFilter('');
    setConfFilter('');
    setClaimFilter('');
  }

  const hasActiveFilter = workflowFilter || recFilter || confFilter || claimFilter;

  return (
    <div className="p-6 max-w-full">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Audit Log</h1>
          <p className="text-sm text-gray-500 mt-1">All assessment decisions with full traceability</p>
        </div>
        {!loading && (
          <span className="text-xs text-gray-400 mt-1">{allLogs.length} total records loaded</span>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-5 flex flex-wrap gap-3 items-center">
        {/* Workflow type — derived from actual data */}
        <select
          value={workflowFilter}
          onChange={e => setWorkflowFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All workflow types</option>
          {workflowTypes.map(t => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>

        <select
          value={recFilter}
          onChange={e => setRecFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All recommendations</option>
          {RECOMMENDATIONS.map(r => <option key={r} value={r}>{r}</option>)}
        </select>

        <select
          value={confFilter}
          onChange={e => setConfFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          <option value="">All confidence levels</option>
          {CONFIDENCE_LEVELS.map(c => <option key={c} value={c}>{c}</option>)}
        </select>

        <input
          type="text"
          placeholder="Claim ID (e.g. CLM-0003)"
          value={claimFilter}
          onChange={e => setClaimFilter(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 w-48"
        />

        {hasActiveFilter && (
          <button
            onClick={clearFilters}
            className="text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg border border-gray-200 hover:border-gray-300 transition"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Stats strip */}
      {!loading && allLogs.length > 0 && (
        <div className="grid grid-cols-4 gap-3 mb-5">
          {[
            { label: hasActiveFilter ? 'Filtered' : 'Total', value: stats.total },
            { label: 'Approved', value: stats.approved },
            { label: 'Rejected', value: stats.rejected },
            {
              label: 'Avg Judge Score',
              value: stats.avgJudge != null ? `${stats.avgJudge}%` : '—',
            },
          ].map(stat => (
            <div key={stat.label} className="bg-white border border-gray-200 rounded-xl p-4">
              <p className="text-xs text-gray-500">{stat.label}</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stat.value}</p>
            </div>
          ))}
        </div>
      )}

      {loading && <div className="text-center py-20 text-gray-400 text-sm">Loading…</div>}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">{error}</div>
      )}
      {fraudError && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3 mb-4 flex items-center justify-between">
          <span>Fraud check failed: {fraudError}</span>
          <button onClick={() => setFraudError(null)} className="text-red-400 hover:text-red-600 ml-4">✕</button>
        </div>
      )}
      {!loading && !error && logs.length === 0 && (
        <div className="text-center py-20 text-gray-400 text-sm">
          {hasActiveFilter
            ? `No records match these filters. ${allLogs.length} total records available.`
            : 'No records found. Run an assessment in the Chat view first.'}
        </div>
      )}

      {!loading && logs.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              Showing {logs.length}{hasActiveFilter ? ` of ${allLogs.length}` : ''} record{logs.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50">
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Claim</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Workflow</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Verdict</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Confidence</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Judge Score</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Assessed</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Fraud Risk</th>
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
                    <td className="px-4 py-3 text-gray-600">{log.workflow_type}</td>
                    <td className="px-4 py-3"><RecommendationBadge rec={log.recommendation} /></td>
                    <td className="px-4 py-3 capitalize text-gray-600">{log.confidence_level || '—'}</td>
                    <td className="px-4 py-3">
                      {log.judge_overall_score != null
                        ? <ScoreBadge score={log.judge_overall_score} />
                        : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {fmtDateTime(log.assessed_at)}
                    </td>
                    <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                      {!log.claim_id ? (
                        <span className="text-gray-300">—</span>
                      ) : fraudChecks[log.claim_id] ? (
                        <RiskBadge level={fraudChecks[log.claim_id].risk_level} />
                      ) : checkingClaimId === log.claim_id ? (
                        <span className="text-xs text-gray-400">Checking…</span>
                      ) : (
                        <button
                          onClick={() => handleFraudCheck(log.claim_id)}
                          className="text-xs text-brand-600 hover:text-brand-700 border border-brand-200 hover:border-brand-300 rounded-lg px-2 py-1 transition"
                        >
                          Check for fraud signals
                        </button>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      <svg
                        className={`w-4 h-4 transition-transform ${expanded === log.id ? 'rotate-180' : ''}`}
                        fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </td>
                  </tr>
                  {expanded === log.id && (
                    <tr key={`${log.id}-exp`} className="bg-gray-50">
                      <td colSpan={8} className="px-6 py-4">
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
                                  {val != null
                                    ? <ScoreBadge score={val as number} />
                                    : <span className="text-gray-300">—</span>}
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
                          {log.claim_id && fraudChecks[log.claim_id] && (
                            <div className="space-y-2 col-span-2 pt-2 border-t border-gray-200">
                              <h4 className="font-semibold text-gray-700 text-sm flex items-center gap-2">
                                Fraud/Anomaly Risk Signals
                                <RiskBadge level={fraudChecks[log.claim_id].risk_level} />
                              </h4>
                              <p>
                                <span className="text-gray-500">Recommended action:</span>{' '}
                                {fraudChecks[log.claim_id].recommended_action?.replace(/_/g, ' ') || '—'}
                              </p>
                              {fraudChecks[log.claim_id].flags?.length > 0 ? (
                                <ul className="list-disc list-inside space-y-1">
                                  {fraudChecks[log.claim_id].flags.map((f, i) => (
                                    <li key={i}><span className="font-medium">{f.signal}:</span> {f.explanation}</li>
                                  ))}
                                </ul>
                              ) : (
                                <p className="text-gray-400">No specific flags raised.</p>
                              )}
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </div>
  );
}
