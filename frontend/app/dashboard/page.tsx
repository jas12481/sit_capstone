'use client';

import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, CartesianGrid,
} from 'recharts';
import { getAssessmentLogs, type AssessmentLog } from '@/lib/mcp';

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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    getAssessmentLogs({ limit: 500 })
      .then(setLogs)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-gray-400 text-sm">Loading…</div>;
  if (error) return <div className="p-6 text-red-600 text-sm">{error}</div>;
  if (logs.length === 0) return (
    <div className="p-6 text-gray-400 text-sm text-center py-20">
      No assessment data yet. Run some claims assessments in the Chat view first.
    </div>
  );

  // ── aggregations ─────────────────────────────────────────────────────────

  const totalAssessments = logs.length;
  const approveRate = (logs.filter(l => l.recommendation === 'APPROVE').length / totalAssessments * 100).toFixed(0);
  const avgJudge = toPercent(logs.reduce((s, l) => s + (l.judge_overall_score ?? 0), 0) / totalAssessments);
  const avgHallucinationRisk = toPercent(logs.reduce((s, l) => s + (l.judge_hallucination_risk_score ?? 0), 0) / totalAssessments);

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
        hallucination: toPercent(l.judge_hallucination_risk_score),
    }));

  // Confidence distribution
  const confCounts: Record<string, number> = {};
  logs.forEach(l => { if (l.confidence_level) confCounts[l.confidence_level] = (confCounts[l.confidence_level] || 0) + 1; });
  const confData = Object.entries(confCounts).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-gray-900">Management Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Claims volume, recommendation rates, and quality trends</p>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Total Assessments" value={totalAssessments} />
        <StatCard label="Approval Rate" value={`${approveRate}%`} />
        <StatCard label="Avg Judge Score" value={`${avgJudge}%`} sub="overall quality" />
        <StatCard label="Avg Hallucination Risk" value={`${avgHallucinationRisk}%`} sub="lower = better" />
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
                label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
              >
                {recData.map(entry => (
                  <Cell key={entry.name} fill={COLOURS[entry.name as keyof typeof COLOURS] || '#94a3b8'} />
                ))}
              </Pie>
              <Legend formatter={v => v.replace(/_/g, ' ')} />
              <Tooltip formatter={(v, n) => [v, (n as string).replace(/_/g, ' ')]} />
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
    </div>
  );
}
