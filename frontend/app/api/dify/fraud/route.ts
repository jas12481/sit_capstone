/**
 * Server-side proxy for the Fraud/Anomaly Risk Signals Dify workflow app.
 * Keeps DIFY_FRAUD_KEY out of the browser bundle — the Audit Log page calls
 * this route instead of Dify directly. Reuses the same DIFY_URL as the chat
 * proxy (same Dify workspace); DIFY_FRAUD_KEY is its own server-only key
 * (no NEXT_PUBLIC_ prefix).
 */
import { NextRequest, NextResponse } from 'next/server';

const DIFY_URL = process.env.DIFY_URL || '';
const DIFY_FRAUD_KEY = process.env.DIFY_FRAUD_KEY || '';

export async function POST(req: NextRequest) {
  if (!DIFY_URL || !DIFY_FRAUD_KEY) {
    return NextResponse.json(
      { error: 'Fraud risk check is not configured on the server. Set DIFY_URL and DIFY_FRAUD_KEY.' },
      { status: 500 }
    );
  }

  const { claim_id } = await req.json();
  if (!claim_id) {
    return NextResponse.json({ error: 'claim_id is required' }, { status: 400 });
  }

  const res = await fetch(`${DIFY_URL}/v1/workflows/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${DIFY_FRAUD_KEY}`,
    },
    body: JSON.stringify({
      // The workflow's Start node marks `query` as required (a leftover from
      // being designed for Dify's interactive chat-style test panel) even
      // though the actual logic only reads `claim_id` — send a placeholder
      // so the API call isn't rejected with "query is required in input form".
      inputs: { claim_id, query: `Check claim ${claim_id} for fraud/anomaly risk signals` },
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

  const answer = json?.data?.outputs?.answer;
  try {
    const parsed = JSON.parse(answer);
    return NextResponse.json(parsed);
  } catch {
    return NextResponse.json({ error: 'Could not parse workflow output as JSON', raw: answer }, { status: 502 });
  }
}
