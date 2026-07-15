'use client';

import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, CartesianGrid,
} from 'recharts';
import {
  getAssessmentLogs, getFraudRiskChecks, getMissingDocumentationChecks,
  type AssessmentLog, type FraudRiskCheck, type MissingDocumentationCheck,
} from '@/lib/mcp';

function toPercent(score: number): number {
  if (score <= 1) return Math.round(score * 100);
  if (score <= 5) return Math.round((score / 5) * 100);
  return Math.min(100, Math.round(score));
}

const COLOURS = {
  APPROVE: '#22c55e',
  REJECT: '#ef4444',
  REFER_FOR_FURTHER_REVIEW: '#f97316',
  PENDING: '#94a3b8',
};
const DOMAIN_COLOURS = ['#3b5bdb', '#7c3aed', '#0891b2', '#059669'];
const RISK_COLOURS: Record<string, string> = { LOW: '#22c55e', MEDIUM: '#f59e0b', HIGH: '#ef4444' };

function RiskPill({ level }: { level: string }) {
  const colour =
    level === 'HIGH' ? 'bg-red-100 text-red-800' :
    level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
    'bg-green-100 text-green-800';
  return <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${colour}`}>{level}</span>;
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const [logs, setLogs] = useState<AssessmentLog[]>([]);
  const [fraudChecks, setFraudChecks] = useState<FraudRiskCheck[]>([]);
  const [missingDocsChecks, setMissingDocsChecks] = useState<MissingDocumentationCheck[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getAssessmentLogs({ limit: 500 })
      .then(setLogs)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
    getFraudRiskChecks({ limit: 500 })
      .then(setFraudChecks)
      .catch(() => {}); // non-critical — Risk Signals section just shows empty state
    getMissingDocumentationChecks({ limit: 500 })
      .then(setMissingDocsChecks)
      .catch(() => {}); // non-critical — Missing Documentation section just shows empty state
  }, []);

  if (loading) return <div className="p-6 text-gray-400 text-sm">Loading…</div>;
  if (error) return <div className="p-6 text-red-600 text-sm">{error}</div>;
  if (logs.length === 0) return (
    <div className="p-6 text-gray-400 text-sm text-center py-20">
      No assessment data yet. Run some claims assessments in the Chat view first.
    </div>
  );

  // ── aggregations ─────────────────────────────────────────────────────────

  const totalRuns = logs.length;
  const distinctClaimsAssessed = new Set(logs.map(l => l.claim_id)).size;
  const approveRate = (logs.filter(l => l.recommendation === 'APPROVE').length / totalRuns * 100).toFixed(0);

  // Trailing window, not all-time — an all-time average stays dominated by however many
  // hundred old rows already exist, so a prompt/judge redesign (like the grounded-hallucination-
  // check rework) wouldn't visibly move these cards for a long time. Same "last N" convention
  // as the trend chart below (last 30), just a wider window since these are single numbers
  // rather than a line.
  const RECENT_WINDOW = 50;
  const recentLogs = [...logs]
    .filter(l => l.assessed_at)
    .sort((a, b) => new Date(b.assessed_at).getTime() - new Date(a.assessed_at).getTime())
    .slice(0, RECENT_WINDOW);
  const avgJudge = toPercent(recentLogs.reduce((s, l) => s + (l.judge_overall_score ?? 0), 0) / recentLogs.length);
  // Judge rubric scores this dimension "higher = lower risk / safer" (see Life_Assess_Claim.yml's
  // llm_judge node) — invert to show the actual risk percentage (lower = better, as labelled).
  const avgHallucinationRisk = 100 - toPercent(recentLogs.reduce((s, l) => s + (l.judge_hallucination_risk_score ?? 0), 0) / recentLogs.length);

  // Recommendation distribution
  const recCounts: Record<string, number> = {};
  logs.forEach(l => { recCounts[l.recommendation] = (recCounts[l.recommendation] || 0) + 1; });
  const recData = Object.entries(recCounts).map(([name, value]) => ({ name, value }));

  // Claims volume by workflow type
  const domainCounts: Record<string, number> = {};
  logs.forEach(l => { domainCounts[l.workflow_type] = (domainCounts[l.workflow_type] || 0) + 1; });
  const domainData = Object.entries(domainCounts).map(([name, count]) => ({ name, count }));

  // Judge score trend (last 30 by assessed_at)
  const sorted = [...logs]
    .filter(l => l.assessed_at && l.judge_overall_score != null)
    .sort((a, b) => new Date(a.assessed_at).getTime() - new Date(b.assessed_at).getTime())
    .slice(-30)
    .map((l, i) => ({
      i: i + 1,
      overall: toPercent(l.judge_overall_score),
        completeness: toPercent(l.judge_completeness_score),
        hallucination: 100 - toPercent(l.judge_hallucination_risk_score),
    }));

  // Confidence distribution
  const confCounts: Record<string, number> = {};
  logs.forEach(l => { if (l.confidence_level) confCounts[l.confidence_level] = (confCounts[l.confidence_level] || 0) + 1; });
  const confData = Object.entries(confCounts).map(([name, value]) => ({ name, value }));

  // Rule Failure Analysis — aggregated from rule_checks, persisted on assessment_logs
  // only since the per-rule reasoning gap was fixed, so this covers a growing subset
  // of runs (not the full portfolio) — surfaced via the coverage note in the UI below.
  const logsWithRuleChecks = logs.filter(l => l.rule_checks && l.rule_checks.length > 0);
  const ruleFailStats = (() => {
    const byRule: Record<string, { rule_id: string; rule_name: string; count: number; mandatoryCount: number }> = {};
    for (const l of logsWithRuleChecks) {
      for (const rc of l.rule_checks || []) {
        if (rc.result !== 'FAIL') continue;
        if (!byRule[rc.rule_id]) byRule[rc.rule_id] = { rule_id: rc.rule_id, rule_name: rc.rule_name, count: 0, mandatoryCount: 0 };
        byRule[rc.rule_id].count += 1;
        if (String(rc.is_mandatory) === 'true') byRule[rc.rule_id].mandatoryCount += 1;
      }
    }
    return Object.values(byRule).sort((a, b) => b.count - a.count);
  })();
  const topFailedRules = ruleFailStats.slice(0, 8).map(r => ({
    name: r.rule_id,
    fullName: r.rule_name,
    value: r.count,
    mandatory: r.mandatoryCount > 0,
  }));
  const recentRuleFailures = [...logsWithRuleChecks]
    .sort((a, b) => new Date(b.assessed_at).getTime() - new Date(a.assessed_at).getTime())
    .flatMap(l => (l.rule_checks || [])
      .filter(rc => rc.result === 'FAIL')
      .map(rc => ({ claim_id: l.claim_id, ...rc })))
    .slice(0, 8);

  // Missing Documentation — aggregated from whatever's been checked so far via the
  // Audit Log (on-demand, scoped to REFER_FOR_FURTHER_REVIEW rows there), same
  // accumulates-over-time pattern as Fraud checks below. Dedupe to latest per claim.
  const latestMissingDocsChecks = (() => {
    const byClaimId: Record<string, MissingDocumentationCheck> = {};
    for (const c of [...missingDocsChecks].sort((a, b) => new Date(b.checked_at).getTime() - new Date(a.checked_at).getTime())) {
      if (!byClaimId[c.claim_id]) byClaimId[c.claim_id] = c;
    }
    return Object.values(byClaimId);
  })();
  const docCompletionData = [
    { name: 'Complete', value: latestMissingDocsChecks.filter(c => c.all_requirements_met).length },
    { name: 'Missing Docs', value: latestMissingDocsChecks.filter(c => !c.all_requirements_met).length },
  ];
  const missingDocTypeCounts: Record<string, number> = {};
  latestMissingDocsChecks.forEach(c => {
    (c.missing_documents || []).forEach(d => {
      missingDocTypeCounts[d.document_type] = (missingDocTypeCounts[d.document_type] || 0) + 1;
    });
  });
  const missingDocTypeData = Object.entries(missingDocTypeCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)
    .map(([name, value]) => ({ name, value }));
  const claimsMissingDocs = latestMissingDocsChecks.filter(c => !c.all_requirements_met);

  // Status Cross-Check — observe-only: does a claim's fresh, independent recommendation
  // agree with the status already recorded on it? Only computed for already-decided claims
  // (a freshly-pending claim's status gets finalized by the write-back instead, so those
  // rows have neither field set — see mcp_server/main.py POST /assessment-logs). Never
  // influences the verdict; this is purely a governance signal for humans to look at.
  const logsWithCrossCheck = logs.filter(l => l.status_cross_check === 'CONSISTENT' || l.status_cross_check === 'MISMATCH');
  const crossCheckMismatchCount = logsWithCrossCheck.filter(l => l.status_cross_check === 'MISMATCH').length;
  const crossCheckConsistentCount = logsWithCrossCheck.length - crossCheckMismatchCount;
  const crossCheckMismatchRate = logsWithCrossCheck.length > 0
    ? Math.round((crossCheckMismatchCount / logsWithCrossCheck.length) * 100)
    : 0;
  const crossCheckDistribution = [
    { name: 'Consistent', value: crossCheckConsistentCount },
    { name: 'Mismatch', value: crossCheckMismatchCount },
  ];
  // Dedupe to latest per claim — a repeatedly-tested claim shouldn't crowd out distinct
  // mismatched claims in the list below.
  const latestCrossCheckByClaim = (() => {
    const byClaimId: Record<string, AssessmentLog> = {};
    for (const l of [...logsWithCrossCheck].sort((a, b) => new Date(b.assessed_at).getTime() - new Date(a.assessed_at).getTime())) {
      if (!byClaimId[l.claim_id]) byClaimId[l.claim_id] = l;
    }
    return Object.values(byClaimId);
  })();
  const mismatchedClaims = latestCrossCheckByClaim.filter(l => l.status_cross_check === 'MISMATCH');

  // Repeat-Assessment Consistency — same claim, same prompt_version: do repeated runs
  // (each identified by its own log_id) agree on a recommendation? Only comparing within
  // the same prompt_version matters — otherwise a disagreement might just mean the prompt
  // changed between runs, not that the AI is unreliable.
  const repeatGroups: Record<string, AssessmentLog[]> = {};
  logs.forEach(l => {
    if (!l.claim_id || !l.prompt_version) return;
    const key = `${l.claim_id}::${l.prompt_version}`;
    (repeatGroups[key] ||= []).push(l);
  });
  const groupsWithRepeats = Object.values(repeatGroups).filter(g => g.length > 1);
  const inconsistentGroups = groupsWithRepeats
    .filter(g => new Set(g.map(l => l.recommendation)).size > 1)
    .sort((a, b) => b.length - a.length);
  const consistentGroupCount = groupsWithRepeats.length - inconsistentGroups.length;
  const repeatConsistencyRate = groupsWithRepeats.length > 0
    ? Math.round((consistentGroupCount / groupsWithRepeats.length) * 100)
    : 0;
  const repeatDistribution = [
    { name: 'Consistent', value: consistentGroupCount },
    { name: 'Inconsistent', value: inconsistentGroups.length },
  ];
  const inconsistentGroupSummaries = inconsistentGroups.slice(0, 8).map(g => {
    const counts: Record<string, number> = {};
    g.forEach(l => { counts[l.recommendation] = (counts[l.recommendation] || 0) + 1; });
    return {
      claim_id: g[0].claim_id,
      prompt_version: g[0].prompt_version,
      runs: g.length,
      breakdown: Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([rec, n]) => `${rec} ×${n}`).join(', '),
    };
  });

  // Fraud/Anomaly Risk Signals — aggregated from whatever's been checked so
  // far via the Audit Log (this app is on-demand, not a full-portfolio scan,
  // so this grows as claims officers check individual claims). Dedupe to one
  // (latest) check per claim first — fraudChecks is an event log ordered by
  // checked_at desc, so a re-checked claim would otherwise be double-counted
  // and could show a stale risk level alongside its current one.
  const latestFraudChecks = (() => {
    const byClaimId: Record<string, FraudRiskCheck> = {};
    for (const c of fraudChecks) {
      if (!byClaimId[c.claim_id]) byClaimId[c.claim_id] = c;
    }
    return Object.values(byClaimId);
  })();

  const riskLevelCounts: Record<string, number> = { LOW: 0, MEDIUM: 0, HIGH: 0 };
  latestFraudChecks.forEach(c => { riskLevelCounts[c.risk_level] = (riskLevelCounts[c.risk_level] || 0) + 1; });
  const riskLevelData = ['LOW', 'MEDIUM', 'HIGH'].map(name => ({ name, value: riskLevelCounts[name] || 0 }));
  const highRiskClaims = latestFraudChecks.filter(c => c.risk_level === 'HIGH').slice(0, 5);

  // signal is free text (a per-claim descriptive summary, not a fixed category) so a
  // "most common signal" count would be near-meaningless — show the raw recent flags instead.
  // LOW-risk checks are excluded here — nothing worth surfacing to a reviewer at that level.
  const recentFlags = latestFraudChecks
    .filter(c => c.risk_level !== 'LOW')
    .sort((a, b) => new Date(b.checked_at).getTime() - new Date(a.checked_at).getTime())
    .flatMap(c => (c.flags || []).map(f => ({ claim_id: c.claim_id, risk_level: c.risk_level, ...f })))
    .slice(0, 8);

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Management Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Claims volume, recommendation rates, and quality trends</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total Assessments" value={distinctClaimsAssessed} sub={`${totalRuns} total runs`} />
        <StatCard label="Approval Rate" value={`${approveRate}%`} />
        <StatCard label="Avg Judge Score" value={`${avgJudge}%`} sub={`overall quality, last ${recentLogs.length}`} />
        <StatCard label="Avg Hallucination Risk" value={`${avgHallucinationRisk}%`} sub={`lower = better, last ${recentLogs.length}`} />
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-2 gap-4">
        {/* Recommendation distribution */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Recommendation Distribution</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={recData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                labelLine={false}
              >
                {recData.map(entry => (
                  <Cell key={entry.name} fill={COLOURS[entry.name as keyof typeof COLOURS] || '#94a3b8'} />
                ))}
              </Pie>
              <Legend formatter={v => v.replace(/_/g, ' ')} />
              <Tooltip formatter={(v: number, n) => [`${v} (${((v / totalRuns) * 100).toFixed(0)}%)`, (n as string).replace(/_/g, ' ')]} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Claims volume by domain */}
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Claims Volume by Domain</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={domainData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} />
              <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {domainData.map((_, i) => (
                  <Cell key={i} fill={DOMAIN_COLOURS[i % DOMAIN_COLOURS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Judge score trend */}
      {sorted.length > 1 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">LLM-as-Judge Score Trend (last {sorted.length} runs)</h2>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={sorted} margin={{ top: 5, right: 20, left: -20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
              <XAxis dataKey="i" tick={{ fontSize: 11 }} label={{ value: 'Run #', position: 'insideBottom', offset: -2, fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} unit="%" />
              <Tooltip formatter={(v, n) => [`${v}%`, n]} />
              <Legend />
              <Line type="monotone" dataKey="overall" stroke="#3b5bdb" strokeWidth={2} dot={false} name="Overall" />
              <Line type="monotone" dataKey="completeness" stroke="#7c3aed" strokeWidth={1.5} dot={false} name="Completeness" strokeDasharray="4 2" />
              <Line type="monotone" dataKey="hallucination" stroke="#ef4444" strokeWidth={1.5} dot={false} name="Hallucination risk" strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Confidence distribution */}
      {confData.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Confidence Level Distribution</h2>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={confData} layout="vertical" margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
              <XAxis type="number" tick={{ fontSize: 12 }} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b5bdb" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Rule Failure Analysis — accumulates as fresh assessments run (rule_checks
          persistence only covers runs after the per-rule reasoning gap was fixed) */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mt-2">Rule Failure Analysis</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Based on {logsWithRuleChecks.length} assessment{logsWithRuleChecks.length === 1 ? '' : 's'} with rule-level
          data recorded — coverage grows as new assessments run.
        </p>
      </div>
      {topFailedRules.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-5 text-sm text-gray-400 text-center py-10">
          No rule failures recorded yet in assessments with rule-level data.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Most Frequently Failed Rules</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={topFailedRules} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <XAxis type="number" tick={{ fontSize: 12 }} tickLine={false} allowDecimals={false} />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={80} />
                <Tooltip formatter={(v: number, _n, p) => [`${v} fail(s)`, p.payload.fullName]} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {topFailedRules.map((r, i) => (
                    <Cell key={i} fill={r.mandatory ? '#ef4444' : '#f59e0b'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-xs text-gray-400 mt-2">Red = mandatory rule, amber = non-mandatory.</p>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Recent Rule Failures</h2>
            {recentRuleFailures.length > 0 ? (
              <ul className="divide-y divide-gray-100 text-sm max-h-[220px] overflow-y-auto">
                {recentRuleFailures.map((f, i) => (
                  <li key={i} className="py-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-gray-500">{f.claim_id}</span>
                      <span className="text-xs font-semibold text-gray-700">{f.rule_name}</span>
                      {String(f.is_mandatory) === 'true' && (
                        <span className="text-[10px] text-red-700 bg-red-50 rounded-full px-1.5 py-0.5">mandatory</span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{f.reason}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-sm text-gray-400 text-center py-16">No rule failures to show.</div>
            )}
          </div>
        </div>
      )}

      {/* Missing Documentation — accumulates as REFER claims are checked via the Audit Log */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mt-2">Missing Documentation</h2>
      </div>
      {latestMissingDocsChecks.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-5 text-sm text-gray-400 text-center py-10">
          No claims checked for missing documentation yet. Use the &quot;Check missing documentation&quot; action in the Audit Log.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Documentation Completeness</h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={docCompletionData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} />
                <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  <Cell fill="#22c55e" />
                  <Cell fill="#f97316" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Most Commonly Missing Document Types</h2>
            {missingDocTypeData.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={missingDocTypeData} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                  <XAxis type="number" tick={{ fontSize: 12 }} tickLine={false} allowDecimals={false} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} width={110} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#f97316" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-sm text-gray-400 text-center py-16">No missing documents recorded — all checked claims are complete.</div>
            )}
          </div>

          {claimsMissingDocs.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5 col-span-2">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">Claims With Missing Documentation</h2>
              <ul className="divide-y divide-gray-100 text-sm">
                {claimsMissingDocs.map(c => (
                  <li key={c.id} className="py-2">
                    <div className="flex items-start justify-between gap-4">
                      <span className="font-mono text-xs text-gray-700">{c.claim_id}</span>
                      <span className="text-xs text-orange-700 bg-orange-50 rounded-full px-2 py-0.5 whitespace-nowrap">
                        {c.missing_documents.length} missing
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {c.missing_documents.map(d => d.document_type).join(', ')}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Status Cross-Check — grows as already-decided claims get (re-)assessed; observe-only */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mt-2">Status Cross-Check</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          Based on {logsWithCrossCheck.length} assessment{logsWithCrossCheck.length === 1 ? '' : 's'} of
          claims that already had a recorded status — does fresh, independent AI judgment agree with
          what&apos;s already on record? Observe-only: never changes a verdict or overwrites the claim.
        </p>
      </div>
      {logsWithCrossCheck.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-5 text-sm text-gray-400 text-center py-10">
          No cross-checks recorded yet — this only applies to claims that already had a decided status
          when assessed.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Consistent vs. Mismatch</h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={crossCheckDistribution} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} />
                <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip formatter={(v: number) => [`${v} (${((v / logsWithCrossCheck.length) * 100).toFixed(0)}%)`, '']} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  <Cell fill="#22c55e" />
                  <Cell fill="#f59e0b" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-xs text-gray-400 mt-2">{crossCheckMismatchRate}% mismatch rate across cross-checked assessments.</p>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Claims With a Mismatch</h2>
            {mismatchedClaims.length > 0 ? (
              <ul className="divide-y divide-gray-100 text-sm max-h-[220px] overflow-y-auto">
                {mismatchedClaims.map(l => (
                  <li key={l.log_id} className="py-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-gray-500">{l.claim_id}</span>
                      <span className="text-xs text-amber-700 bg-amber-50 rounded-full px-2 py-0.5">mismatch</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{l.status_cross_check_note}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-sm text-gray-400 text-center py-16">No mismatches — every cross-checked assessment agrees with its recorded status.</div>
            )}
          </div>
        </div>
      )}

      {/* Repeat-Assessment Consistency — mostly a testing/QA signal, since a real claim is
          typically only assessed once; grows whenever the same claim gets assessed more
          than once under the same prompt_version */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mt-2">Repeat-Assessment Consistency</h2>
        <p className="text-xs text-gray-400 mt-0.5">
          {groupsWithRepeats.length} claim{groupsWithRepeats.length === 1 ? '' : 's'} assessed more than
          once under the same prompt version — do repeated runs agree? Caveat: <code className="font-mono bg-gray-100 px-1 rounded">prompt_version</code> is
          currently a static label per workflow, not bumped when the underlying prompt actually changes
          — so some &quot;inconsistent&quot; groups here may reflect real development changes between
          runs rather than LLM flakiness on an unchanged system.
        </p>
      </div>
      {groupsWithRepeats.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-5 text-sm text-gray-400 text-center py-10">
          No claim has been assessed more than once under the same prompt version yet.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Consistent vs. Inconsistent</h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={repeatDistribution} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} />
                <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip formatter={(v: number) => [`${v} (${((v / groupsWithRepeats.length) * 100).toFixed(0)}%)`, '']} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  <Cell fill="#22c55e" />
                  <Cell fill="#ef4444" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <p className="text-xs text-gray-400 mt-2">{repeatConsistencyRate}% of repeat-tested claims got the same recommendation every time.</p>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Claims With Inconsistent Runs</h2>
            {inconsistentGroupSummaries.length > 0 ? (
              <ul className="divide-y divide-gray-100 text-sm max-h-[220px] overflow-y-auto">
                {inconsistentGroupSummaries.map((g, i) => (
                  <li key={i} className="py-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-gray-500">{g.claim_id}</span>
                      <span className="text-xs text-red-700 bg-red-50 rounded-full px-2 py-0.5">{g.runs} runs</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{g.breakdown}</p>
                    <p className="text-[11px] text-gray-400 mt-0.5">{g.prompt_version}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-sm text-gray-400 text-center py-16">Every repeat-tested claim got a consistent recommendation.</div>
            )}
          </div>
        </div>
      )}

      {/* Fraud/Anomaly Risk Signals — accumulates as claims are checked via the Audit Log */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mt-2">Risk Signals</h2>
      </div>
      {latestFraudChecks.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-5 text-sm text-gray-400 text-center py-10">
          No claims checked for fraud/anomaly signals yet. Use the &quot;Check for fraud signals&quot; action in the Audit Log.
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Risk Level Distribution</h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={riskLevelData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} tickLine={false} />
                <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {riskLevelData.map(entry => (
                    <Cell key={entry.name} fill={RISK_COLOURS[entry.name] || '#94a3b8'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="text-sm font-semibold text-gray-700 mb-4">Recent Flags Raised</h2>
            {recentFlags.length > 0 ? (
              <ul className="divide-y divide-gray-100 text-sm max-h-[220px] overflow-y-auto">
                {recentFlags.map((f, i) => (
                  <li key={i} className="py-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs text-gray-500">{f.claim_id}</span>
                      <RiskPill level={f.risk_level} />
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{f.explanation || f.signal}</p>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-sm text-gray-400 text-center py-16">No flags raised in any check so far.</div>
            )}
          </div>

          {highRiskClaims.length > 0 && (
            <div className="bg-white border border-gray-200 rounded-xl p-5 col-span-2">
              <h2 className="text-sm font-semibold text-gray-700 mb-4">High-Risk Claims Needing Follow-up</h2>
              <ul className="divide-y divide-gray-100 text-sm">
                {highRiskClaims.map(c => (
                  <li key={c.id} className="py-2 flex items-start justify-between gap-4">
                    <div>
                      <span className="font-mono text-xs text-gray-700">{c.claim_id}</span>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {(c.flags || []).map(f => f.signal).join(', ') || 'No specific signal recorded'}
                      </p>
                    </div>
                    <span className="text-xs text-red-700 bg-red-50 rounded-full px-2 py-0.5 whitespace-nowrap">
                      {c.recommended_action?.replace(/_/g, ' ')}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
