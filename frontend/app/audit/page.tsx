'use client';

import { useState, useEffect, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  getAssessmentLogs,
  getFraudRiskChecks, runFraudRiskCheck, createFraudRiskCheck,
  getAssessmentExplanations, runAssessmentExplanation, createAssessmentExplanation,
  getMissingDocumentationChecks, runMissingDocumentationCheck, createMissingDocumentationCheck,
  type AssessmentLog, type FraudRiskCheck, type AssessmentExplanation, type MissingDocumentationCheck,
} from '@/lib/mcp';
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
  // Sub-sections within an expanded row, collapsed by default — keeps a row
  // with both a long explanation and fraud signals from taking over the
  // screen. Keyed by log_id (per-row), independent for each section.
  const [explanationSectionOpen, setExplanationSectionOpen] = useState<Record<string, boolean>>({});
  const [fraudSectionOpen, setFraudSectionOpen] = useState<Record<string, boolean>>({});
  const [missingDocsSectionOpen, setMissingDocsSectionOpen] = useState<Record<string, boolean>>({});
  // Consolidated "AI Insights" trigger — one dropdown per row instead of three
  // separate always-visible columns. Only one row's menu open at a time.
  const [insightsMenuOpen, setInsightsMenuOpen] = useState<string | null>(null);

  function viewSection(logId: string, section: 'explanation' | 'missingDocs' | 'fraud') {
    setInsightsMenuOpen(null);
    setExpanded(logId);
    if (section === 'explanation') setExplanationSectionOpen(prev => ({ ...prev, [logId]: true }));
    if (section === 'missingDocs') setMissingDocsSectionOpen(prev => ({ ...prev, [logId]: true }));
    if (section === 'fraud') setFraudSectionOpen(prev => ({ ...prev, [logId]: true }));
  }

  // Filter state — all filtering is done client-side
  const [workflowFilter, setWorkflowFilter] = useState('');
  const [recFilter, setRecFilter] = useState('');
  const [confFilter, setConfFilter] = useState('');
  const [claimFilter, setClaimFilter] = useState('');

  // Fraud/Anomaly Risk Signals — on-demand per-row check, persisted so a
  // claim only needs to be checked once (latest result wins if re-checked).
  const [fraudChecks, setFraudChecks] = useState<Record<string, FraudRiskCheck>>({});
  const [checkingClaimId, setCheckingClaimId] = useState<string | null>(null);
  // Per-claim, not a single global error — a failed recheck on one row
  // shouldn't be ambiguous about which claim it belongs to.
  const [fraudErrors, setFraudErrors] = useState<Record<string, string>>({});
  const [justCheckedClaimId, setJustCheckedClaimId] = useState<string | null>(null);

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

  async function handleFraudCheck(claimId: string, logId: string) {
    setCheckingClaimId(claimId);
    setFraudErrors(prev => { const next = { ...prev }; delete next[claimId]; return next; });
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
      setJustCheckedClaimId(claimId);
      setTimeout(() => setJustCheckedClaimId(prev => prev === claimId ? null : prev), 3000);
      setExpanded(logId); // auto-expand so the result is immediately visible (same as Explain)
      setFraudSectionOpen(prev => ({ ...prev, [logId]: true }));
    } catch (e) {
      setFraudErrors(prev => ({ ...prev, [claimId]: e instanceof Error ? e.message : 'Fraud check failed' }));
    } finally {
      setCheckingClaimId(null);
    }
  }

  // Explanations — keyed by log_id, not claim_id (unlike Fraud): a claim can
  // have multiple assessment_logs rows, and an explanation is tied to one
  // specific verdict, not "whatever's currently newest" for that claim.
  const [explanations, setExplanations] = useState<Record<string, AssessmentExplanation>>({});
  const [explainingLogId, setExplainingLogId] = useState<string | null>(null);
  const [explainErrors, setExplainErrors] = useState<Record<string, string>>({});
  const [justExplainedLogId, setJustExplainedLogId] = useState<string | null>(null);

  function loadExplanations() {
    getAssessmentExplanations({ limit: 500 })
      .then(items => {
        // Results are ordered latest-first — keep only the first (most recent) per log_id
        const byLogId: Record<string, AssessmentExplanation> = {};
        for (const e of items) {
          if (!byLogId[e.log_id]) byLogId[e.log_id] = e;
        }
        setExplanations(byLogId);
      })
      .catch(() => {}); // non-critical — indicators just won't show until this loads
  }

  async function handleExplain(claimId: string, logId: string) {
    setExplainingLogId(logId);
    setExplainErrors(prev => { const next = { ...prev }; delete next[logId]; return next; });
    try {
      const result = await runAssessmentExplanation(claimId, logId);
      const saved = await createAssessmentExplanation({
        log_id: logId,
        claim_id: claimId,
        explanation_text: result.explanation_text,
        generated_by: 'audit_log_ui',
      });
      setExplanations(prev => ({ ...prev, [logId]: saved }));
      setJustExplainedLogId(logId);
      setTimeout(() => setJustExplainedLogId(prev => prev === logId ? null : prev), 3000);
      setExpanded(logId); // auto-expand so the result is immediately visible
      setExplanationSectionOpen(prev => ({ ...prev, [logId]: true }));
    } catch (e) {
      setExplainErrors(prev => ({ ...prev, [logId]: e instanceof Error ? e.message : 'Explanation failed' }));
    } finally {
      setExplainingLogId(null);
    }
  }

  // Missing Documentation — keyed by claim_id, like Fraud (reflects the
  // claim's current state, not tied to one specific assessment_logs row).
  // Scoped to REFER_FOR_FURTHER_REVIEW rows only in the UI — see the
  // workflow's own prompt: it determines what's "still required to complete
  // assessment," which only applies when assessment couldn't be completed.
  const [missingDocsChecks, setMissingDocsChecks] = useState<Record<string, MissingDocumentationCheck>>({});
  const [checkingMissingDocsClaimId, setCheckingMissingDocsClaimId] = useState<string | null>(null);
  const [missingDocsErrors, setMissingDocsErrors] = useState<Record<string, string>>({});
  const [justCheckedMissingDocsClaimId, setJustCheckedMissingDocsClaimId] = useState<string | null>(null);

  function loadMissingDocsChecks() {
    getMissingDocumentationChecks({ limit: 500 })
      .then(checks => {
        // Results are ordered latest-first — keep only the first (most recent) per claim
        const byClaimId: Record<string, MissingDocumentationCheck> = {};
        for (const c of checks) {
          if (!byClaimId[c.claim_id]) byClaimId[c.claim_id] = c;
        }
        setMissingDocsChecks(byClaimId);
      })
      .catch(() => {}); // non-critical — indicators just won't show until this loads
  }

  async function handleMissingDocsCheck(claimId: string, logId: string) {
    setCheckingMissingDocsClaimId(claimId);
    setMissingDocsErrors(prev => { const next = { ...prev }; delete next[claimId]; return next; });
    try {
      const result = await runMissingDocumentationCheck(claimId);
      const saved = await createMissingDocumentationCheck({
        claim_id: claimId,
        all_requirements_met: result.all_requirements_met,
        missing_documents: result.missing_documents,
        submitted_documents_summary: result.submitted_documents_summary,
        checked_by: 'audit_log_ui',
      });
      setMissingDocsChecks(prev => ({ ...prev, [claimId]: saved }));
      setJustCheckedMissingDocsClaimId(claimId);
      setTimeout(() => setJustCheckedMissingDocsClaimId(prev => prev === claimId ? null : prev), 3000);
      setExpanded(logId); // auto-expand so the result is immediately visible
      setMissingDocsSectionOpen(prev => ({ ...prev, [logId]: true }));
    } catch (e) {
      setMissingDocsErrors(prev => ({ ...prev, [claimId]: e instanceof Error ? e.message : 'Missing documentation check failed' }));
    } finally {
      setCheckingMissingDocsClaimId(null);
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
    loadExplanations();
    loadMissingDocsChecks();
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
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">AI Insights</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {logs.map(log => (
                <>
                  <tr
                    key={log.log_id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => toggle(log.log_id)}
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
                    <td className="px-4 py-3 relative" onClick={e => e.stopPropagation()}>
                      {!log.claim_id || !log.log_id ? (
                        <span className="text-gray-300">—</span>
                      ) : explainingLogId === log.log_id || checkingMissingDocsClaimId === log.claim_id || checkingClaimId === log.claim_id ? (
                        <span className="text-xs text-gray-400 flex items-center gap-1.5">
                          <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                          </svg>
                          Running…
                        </span>
                      ) : (
                        <>
                          <button
                            onClick={() => setInsightsMenuOpen(prev => prev === log.log_id ? null : log.log_id)}
                            className="inline-flex items-center gap-2 border border-gray-200 hover:border-brand-300 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50 transition"
                          >
                            AI Insights
                            <span className="inline-flex gap-1">
                              <span
                                title="Explanation"
                                className={`w-1.5 h-1.5 rounded-full ${explanations[log.log_id] ? 'bg-green-500' : 'bg-gray-200'}`}
                              />
                              {log.recommendation === 'REFER_FOR_FURTHER_REVIEW' && (
                                <span
                                  title="Missing Documentation"
                                  className={`w-1.5 h-1.5 rounded-full ${
                                    !missingDocsChecks[log.claim_id] ? 'bg-gray-200'
                                    : missingDocsChecks[log.claim_id].all_requirements_met ? 'bg-green-500'
                                    : 'bg-orange-500'
                                  }`}
                                />
                              )}
                              <span
                                title="Fraud Signals"
                                className={`w-1.5 h-1.5 rounded-full ${
                                  !fraudChecks[log.claim_id] ? 'bg-gray-200'
                                  : fraudChecks[log.claim_id].risk_level === 'LOW' ? 'bg-green-500'
                                  : 'bg-orange-500'
                                }`}
                              />
                            </span>
                          </button>

                          {insightsMenuOpen === log.log_id && (
                            <>
                              {/* Click-outside-to-close backdrop */}
                              <div className="fixed inset-0 z-10" onClick={() => setInsightsMenuOpen(null)} />
                              <div className="absolute right-4 top-full mt-1 w-72 bg-white border border-gray-200 rounded-xl shadow-lg z-20 p-1.5">
                                {/* Explanation item */}
                                <div className="flex items-start justify-between gap-2 px-2.5 py-2 rounded-lg hover:bg-gray-50">
                                  <button
                                    onClick={() => explanations[log.log_id] ? viewSection(log.log_id, 'explanation') : handleExplain(log.claim_id, log.log_id)}
                                    className="flex-1 text-left"
                                  >
                                    <p className="text-xs font-semibold text-gray-800">Assessment Explanation</p>
                                    <p className="text-[11px] text-gray-400 mt-0.5">
                                      {explanations[log.log_id]
                                        ? `Explained ${fmtDateTime(explanations[log.log_id].generated_at)} — click to view`
                                        : 'Not yet checked — click to run'}
                                    </p>
                                    {explainErrors[log.log_id] && (
                                      <p className="text-[11px] text-red-600 mt-0.5">Failed: {explainErrors[log.log_id]}</p>
                                    )}
                                  </button>
                                  {explanations[log.log_id] && (
                                    <button
                                      onClick={() => handleExplain(log.claim_id, log.log_id)}
                                      title="Re-run"
                                      className="flex-shrink-0 text-gray-300 hover:text-brand-600 mt-0.5"
                                    >
                                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                      </svg>
                                    </button>
                                  )}
                                </div>

                                {/* Missing Docs item — REFER rows only */}
                                {log.recommendation === 'REFER_FOR_FURTHER_REVIEW' && (
                                  <>
                                    <div className="h-px bg-gray-100 my-1" />
                                    <div className="flex items-start justify-between gap-2 px-2.5 py-2 rounded-lg hover:bg-gray-50">
                                      <button
                                        onClick={() => missingDocsChecks[log.claim_id] ? viewSection(log.log_id, 'missingDocs') : handleMissingDocsCheck(log.claim_id, log.log_id)}
                                        className="flex-1 text-left"
                                      >
                                        <p className="text-xs font-semibold text-gray-800">Missing Documentation</p>
                                        <p className="text-[11px] text-gray-400 mt-0.5">
                                          {missingDocsChecks[log.claim_id]
                                            ? `Checked ${fmtDateTime(missingDocsChecks[log.claim_id].checked_at)} — click to view`
                                            : 'Not yet checked — click to run'}
                                        </p>
                                        {missingDocsErrors[log.claim_id] && (
                                          <p className="text-[11px] text-red-600 mt-0.5">Failed: {missingDocsErrors[log.claim_id]}</p>
                                        )}
                                      </button>
                                      {missingDocsChecks[log.claim_id] && (
                                        <>
                                          {missingDocsChecks[log.claim_id].all_requirements_met ? (
                                            <span className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-green-100 text-green-800">Complete</span>
                                          ) : (
                                            <span className="flex-shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-orange-100 text-orange-800">
                                              {missingDocsChecks[log.claim_id].missing_documents?.length || 0} missing
                                            </span>
                                          )}
                                        </>
                                      )}
                                    </div>
                                  </>
                                )}

                                {/* Fraud item */}
                                <div className="h-px bg-gray-100 my-1" />
                                <div className="flex items-start justify-between gap-2 px-2.5 py-2 rounded-lg hover:bg-gray-50">
                                  <button
                                    onClick={() => fraudChecks[log.claim_id] ? viewSection(log.log_id, 'fraud') : handleFraudCheck(log.claim_id, log.log_id)}
                                    className="flex-1 text-left"
                                  >
                                    <p className="text-xs font-semibold text-gray-800">Fraud / Anomaly Signals</p>
                                    <p className="text-[11px] text-gray-400 mt-0.5">
                                      {fraudChecks[log.claim_id]
                                        ? `Checked ${fmtDateTime(fraudChecks[log.claim_id].checked_at)} — click to view`
                                        : 'Not yet checked — click to run'}
                                    </p>
                                    {fraudErrors[log.claim_id] && (
                                      <p className="text-[11px] text-red-600 mt-0.5">Failed: {fraudErrors[log.claim_id]}</p>
                                    )}
                                  </button>
                                  {fraudChecks[log.claim_id] && (
                                    <span className="flex-shrink-0">
                                      <RiskBadge level={fraudChecks[log.claim_id].risk_level} />
                                    </span>
                                  )}
                                </div>
                              </div>
                            </>
                          )}
                        </>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400">
                      <svg
                        className={`w-4 h-4 transition-transform ${expanded === log.log_id ? 'rotate-180' : ''}`}
                        fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                      </svg>
                    </td>
                  </tr>
                  {expanded === log.log_id && (
                    <tr key={`${log.log_id}-exp`} className="bg-gray-50">
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
                          {log.log_id && explanations[log.log_id] && (
                            <div className="col-span-2 pt-2 border-t border-gray-200">
                              <button
                                onClick={() => setExplanationSectionOpen(prev => ({ ...prev, [log.log_id]: !prev[log.log_id] }))}
                                className="w-full flex items-center justify-between py-1 text-left"
                              >
                                <h4 className="font-semibold text-gray-700 text-sm">Assessment Explanation</h4>
                                <svg
                                  className={`w-4 h-4 text-gray-400 transition-transform ${explanationSectionOpen[log.log_id] ? 'rotate-180' : ''}`}
                                  fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                                </svg>
                              </button>
                              {explanationSectionOpen[log.log_id] && (
                                <div className="text-gray-700 mt-2">
                                  <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                      p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                                      // Manual bullet/number rendering, not native list-style — the LLM
                                      // often writes "loose" list items (a bold lead-in followed by a
                                      // separate paragraph), which causes a block-level <p> inside the
                                      // <li>. Native markers detach visually from block-level content;
                                      // a flex row keeps the marker and content together regardless.
                                      ul: ({ children }) => <ul className="list-none pl-0 space-y-2 mb-2">{children}</ul>,
                                      ol: ({ children }) => <ol className="list-none pl-0 space-y-2 mb-2">{children}</ol>,
                                      li: ({ children }) => (
                                        <li className="flex gap-2 leading-snug">
                                          <span className="select-none text-gray-400">•</span>
                                          <span className="flex-1 [&>p]:mb-1 [&>p:last-child]:mb-0">{children}</span>
                                        </li>
                                      ),
                                      strong: ({ children }) => <strong className="font-semibold text-gray-800">{children}</strong>,
                                      h2: ({ children }) => <h4 className="font-semibold text-gray-700 text-sm mt-3 mb-1 first:mt-0">{children}</h4>,
                                      h3: ({ children }) => <h4 className="font-semibold text-gray-700 text-sm mt-3 mb-1 first:mt-0">{children}</h4>,
                                    }}
                                  >
                                    {explanations[log.log_id].explanation_text}
                                  </ReactMarkdown>
                                </div>
                              )}
                            </div>
                          )}
                          {log.claim_id && log.log_id && missingDocsChecks[log.claim_id] && (
                            <div className="col-span-2 pt-2 border-t border-gray-200">
                              <button
                                onClick={() => setMissingDocsSectionOpen(prev => ({ ...prev, [log.log_id]: !prev[log.log_id] }))}
                                className="w-full flex items-center justify-between py-1 text-left"
                              >
                                <h4 className="font-semibold text-gray-700 text-sm flex items-center gap-2">
                                  Missing Documentation
                                  {missingDocsChecks[log.claim_id].all_requirements_met ? (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                                      Complete
                                    </span>
                                  ) : (
                                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-orange-100 text-orange-800">
                                      {missingDocsChecks[log.claim_id].missing_documents?.length || 0} missing
                                    </span>
                                  )}
                                </h4>
                                <svg
                                  className={`w-4 h-4 text-gray-400 transition-transform ${missingDocsSectionOpen[log.log_id] ? 'rotate-180' : ''}`}
                                  fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                                </svg>
                              </button>
                              {missingDocsSectionOpen[log.log_id] && (
                                <div className="space-y-2 mt-2">
                                  {missingDocsChecks[log.claim_id].all_requirements_met && log.recommendation === 'REFER_FOR_FURTHER_REVIEW' && (
                                    <p className="text-xs text-orange-700 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2">
                                      Required document types are present, but the assessment still referred this
                                      claim for review — document presence doesn&apos;t guarantee the content is
                                      sufficient to resolve every rule. See Assessment Explanation above for what
                                      specifically remains unresolved.
                                    </p>
                                  )}
                                  <p>
                                    <span className="text-gray-500">Submitted documents:</span>{' '}
                                    {missingDocsChecks[log.claim_id].submitted_documents_summary || '—'}
                                  </p>
                                  {missingDocsChecks[log.claim_id].missing_documents?.length > 0 ? (
                                    <ul className="list-disc list-inside space-y-1">
                                      {missingDocsChecks[log.claim_id].missing_documents.map((d, i) => (
                                        <li key={i}>
                                          <span className="font-medium">{d.document_type}</span>{' '}
                                          <span className="font-mono text-xs text-gray-400">({d.linked_rule_id})</span>
                                          {': '}{d.reason}
                                        </li>
                                      ))}
                                    </ul>
                                  ) : (
                                    <p className="text-gray-400">No missing documents identified.</p>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                          {log.claim_id && log.log_id && fraudChecks[log.claim_id] && (
                            <div className="col-span-2 pt-2 border-t border-gray-200">
                              <button
                                onClick={() => setFraudSectionOpen(prev => ({ ...prev, [log.log_id]: !prev[log.log_id] }))}
                                className="w-full flex items-center justify-between py-1 text-left"
                              >
                                <h4 className="font-semibold text-gray-700 text-sm flex items-center gap-2">
                                  Fraud/Anomaly Risk Signals
                                  <RiskBadge level={fraudChecks[log.claim_id].risk_level} />
                                </h4>
                                <svg
                                  className={`w-4 h-4 text-gray-400 transition-transform ${fraudSectionOpen[log.log_id] ? 'rotate-180' : ''}`}
                                  fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                                </svg>
                              </button>
                              {fraudSectionOpen[log.log_id] && (
                                <div className="space-y-2 mt-2">
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
