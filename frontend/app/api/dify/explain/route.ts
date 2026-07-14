/**
 * Server-side proxy for the Explain_Assessment_Reasoning Dify workflow app.
 * Keeps DIFY_EXPLAIN_KEY out of the browser bundle — the Audit Log page calls
 * this route instead of Dify directly. Only ever used in "explain an existing
 * logged assessment" mode here (every Audit Log row already has a logged
 * assessment) — the workflow's other mode, a fresh walkthrough for an
 * unassessed claim, has no use case on this page and is left Dify-only.
 *
 * Requires log_id (not just claim_id): a claim can have multiple
 * assessment_logs rows (repeat assessments), and this explains one specific
 * verdict, not "whatever's currently newest" for that claim.
 */
import { NextRequest, NextResponse } from 'next/server';

const DIFY_URL = process.env.DIFY_URL || '';
const DIFY_EXPLAIN_KEY = process.env.DIFY_EXPLAIN_KEY || '';

export async function POST(req: NextRequest) {
  if (!DIFY_URL || !DIFY_EXPLAIN_KEY) {
    return NextResponse.json(
      { error: 'Explain Assessment Reasoning is not configured on the server. Set DIFY_URL and DIFY_EXPLAIN_KEY.' },
      { status: 500 }
    );
  }

  const { claim_id, log_id } = await req.json();
  if (!claim_id || !log_id) {
    return NextResponse.json({ error: 'claim_id and log_id are required' }, { status: 400 });
  }

  const res = await fetch(`${DIFY_URL}/v1/workflows/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${DIFY_EXPLAIN_KEY}`,
    },
    body: JSON.stringify({
      inputs: {
        claim_id,
        log_id,
        // Start node marks `query` as required (leftover from being designed
        // for Dify's interactive chat-style test panel) even though this
        // path only reads claim_id/log_id — placeholder so the call isn't
        // rejected with "query is required in input form".
        query: `Explain assessment ${log_id} for claim ${claim_id}`,
      },
      response_mode: 'blocking',
      user: 'frontend-audit-log',
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json({ error: text || `Dify workflow error (${res.status})` }, { status: res.status });
  }

  const json = await res.json();
  const status = json?.data?.status;
  if (status !== 'succeeded') {
    return NextResponse.json(
      { error: json?.data?.error || `Workflow did not succeed (status: ${status})` },
      { status: 502 }
    );
  }

  // Plain text output, not a JSON-stringified "answer" like other workflows —
  // explanation_existing is the only field populated when log_id resolves to
  // a real logged assessment (the only path this route is ever used for).
  const explanation = json?.data?.outputs?.explanation_existing;
  if (!explanation) {
    return NextResponse.json(
      { error: 'Workflow returned no explanation — the log_id may not have matched an assessment_logs row.' },
      { status: 502 }
    );
  }

  return NextResponse.json({ explanation_text: explanation });
}
