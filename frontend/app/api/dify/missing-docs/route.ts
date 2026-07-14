/**
 * Server-side proxy for the Missing_Documentation_Advisor Dify workflow app.
 * Keeps DIFY_MISSING_DOCS_KEY out of the browser bundle — the Audit Log page
 * calls this route instead of Dify directly. Only shown for
 * REFER_FOR_FURTHER_REVIEW rows in the UI — the workflow's own prompt frames
 * its purpose as "what's still required to complete assessment," which only
 * applies when assessment couldn't be completed (REFER), not a finished
 * REJECT/APPROVE.
 */
import { NextRequest, NextResponse } from 'next/server';

const DIFY_URL = process.env.DIFY_URL || '';
const DIFY_MISSING_DOCS_KEY = process.env.DIFY_MISSING_DOCS_KEY || '';

export async function POST(req: NextRequest) {
  if (!DIFY_URL || !DIFY_MISSING_DOCS_KEY) {
    return NextResponse.json(
      { error: 'Missing Documentation Advisor is not configured on the server. Set DIFY_URL and DIFY_MISSING_DOCS_KEY.' },
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
      Authorization: `Bearer ${DIFY_MISSING_DOCS_KEY}`,
    },
    body: JSON.stringify({
      // Start node marks `query` as required (leftover from being designed
      // for Dify's interactive chat-style test panel) even though the
      // actual logic only reads claim_id — placeholder so the call isn't
      // rejected with "query is required in input form".
      inputs: { claim_id, query: `What documentation is missing for claim ${claim_id}?` },
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
