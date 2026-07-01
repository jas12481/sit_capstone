/**
 * Server-side proxy for Dify chat-messages. Keeps DIFY_API_KEY out of the
 * browser bundle — the Chat page calls this route instead of Dify directly.
 * DIFY_URL / DIFY_API_KEY are server-only env vars (no NEXT_PUBLIC_ prefix).
 */
import { NextRequest, NextResponse } from 'next/server';

const DIFY_URL = process.env.DIFY_URL || '';
const DIFY_API_KEY = process.env.DIFY_API_KEY || '';

export async function POST(req: NextRequest) {
  if (!DIFY_URL || !DIFY_API_KEY) {
    return NextResponse.json(
      { error: 'Dify is not configured on the server. Set DIFY_URL and DIFY_API_KEY.' },
      { status: 500 }
    );
  }

  const body = await req.json();

  const res = await fetch(`${DIFY_URL}/v1/chat-messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${DIFY_API_KEY}`,
    },
    body: JSON.stringify(body),
  });

  const text = await res.text();
  return new NextResponse(text, {
    status: res.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
