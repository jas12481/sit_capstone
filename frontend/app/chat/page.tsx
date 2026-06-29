'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  routing?: string;
  timestamp: string;
};

const DIFY_URL = process.env.NEXT_PUBLIC_DIFY_URL || '';
const DIFY_KEY = process.env.NEXT_PUBLIC_DIFY_API_KEY || '';

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string>('');
  const [error, setError] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function send() {
    const query = input.trim();
    if (!query || loading) return;
    if (!DIFY_URL || !DIFY_KEY) {
      setError('Dify API URL and key are not configured. Set NEXT_PUBLIC_DIFY_URL and NEXT_PUBLIC_DIFY_API_KEY in .env.local.');
      return;
    }

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    setError('');

    try {
      const body: Record<string, unknown> = {
        inputs: {},
        query,
        response_mode: 'blocking',
        user: 'claims-officer',
      };
      if (conversationId) body.conversation_id = conversationId;

      const res = await fetch(`${DIFY_URL}/v1/chat-messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${DIFY_KEY}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Dify API error ${res.status}: ${text}`);
      }

      const data = await res.json();
      if (data.conversation_id) setConversationId(data.conversation_id);

      const assistantMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.answer || '(no response)',
        routing: data.metadata?.usage ? `Tokens: ${data.metadata.usage.total_tokens}` : undefined,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  function reset() {
    setMessages([]);
    setConversationId('');
    setError('');
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-gray-900">Claims Assistant</h1>
          <p className="text-sm text-gray-500">Ask about claims, policies, and assessments</p>
        </div>
        <button
          onClick={reset}
          className="text-sm text-gray-500 hover:text-gray-700 px-3 py-1.5 rounded-md border border-gray-200 hover:border-gray-300 transition"
        >
          New conversation
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 py-20">
            <svg className="w-12 h-12 mb-4 text-gray-300" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.77 9.77 0 01-4-.832L3 20l1.09-3.635C3.4 15.24 3 13.66 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p className="text-sm font-medium">Start a conversation</p>
            <p className="text-xs mt-1">Try: "Show me claim CLM-0003" or "Assess CLM-0005"</p>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl rounded-2xl px-4 py-3 ${
              msg.role === 'user'
                ? 'bg-brand-500 text-white'
                : 'bg-white border border-gray-200 text-gray-900'
            }`}>
              <div className="text-sm leading-relaxed">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    table: ({ children }) => (
                      <div className="overflow-x-auto my-2">
                        <table className="min-w-full border-collapse text-xs">{children}</table>
                      </div>
                    ),
                    thead: ({ children }) => (
                      <thead className={msg.role === 'user' ? 'bg-brand-600' : 'bg-gray-100'}>{children}</thead>
                    ),
                    th: ({ children }) => (
                      <th className={`px-3 py-2 text-left font-semibold border ${
                        msg.role === 'user' ? 'border-brand-400 text-white' : 'border-gray-200 text-gray-700'
                      }`}>{children}</th>
                    ),
                    td: ({ children }) => (
                      <td className={`px-3 py-2 border ${
                        msg.role === 'user' ? 'border-brand-400' : 'border-gray-200 text-gray-800'
                      }`}>{children}</td>
                    ),
                    tr: ({ children }) => (
                      <tr className={msg.role === 'assistant' ? 'even:bg-gray-50' : ''}>{children}</tr>
                    ),
                    p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside space-y-0.5 mb-1">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside space-y-0.5 mb-1">{children}</ol>,
                    li: ({ children }) => <li className="leading-snug">{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                    h2: ({ children }) => <h2 className="font-semibold text-sm mt-3 mb-1 first:mt-0">{children}</h2>,
                    h3: ({ children }) => <h3 className="font-medium text-sm mt-2 mb-1 first:mt-0">{children}</h3>,
                    code: ({ children }) => (
                      <code className={`px-1 py-0.5 rounded text-xs font-mono ${
                        msg.role === 'user' ? 'bg-brand-400' : 'bg-gray-100 text-gray-800'
                      }`}>{children}</code>
                    ),
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              </div>
              <div className={`flex items-center justify-between mt-1.5 gap-4 ${
                msg.role === 'user' ? 'text-brand-100' : 'text-gray-400'
              }`}>
                <span className="text-xs">{msg.timestamp}</span>
                {msg.routing && <span className="text-xs">{msg.routing}</span>}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-2 text-gray-400">
                <span className="inline-flex gap-1">
                  <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 rounded-full bg-gray-300 animate-bounce" style={{ animationDelay: '300ms' }} />
                </span>
                <span className="text-xs">Processing…</span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Quick prompts */}
      {messages.length === 0 && (
        <div className="px-6 pb-2">
          <div className="flex flex-wrap gap-2">
            {[
              'Show me claim CLM-0003',
              'Assess claim CLM-0005',
              'What are the details of policy POL-LI-0001?',
              'How does critical illness coverage work?',
            ].map(p => (
              <button
                key={p}
                onClick={() => setInput(p)}
                className="text-xs px-3 py-1.5 rounded-full border border-gray-200 text-gray-600 hover:border-brand-400 hover:text-brand-600 transition bg-white"
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex items-end gap-3">
          <textarea
            className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition min-h-[52px] max-h-40"
            placeholder="Ask about a claim, policy, or assessment…"
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || loading}
            className="bg-brand-500 hover:bg-brand-600 disabled:bg-gray-200 disabled:cursor-not-allowed text-white rounded-xl px-5 py-3 text-sm font-medium transition flex-shrink-0"
          >
            Send
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">Enter to send · Shift+Enter for new line</p>
      </div>
    </div>
  );
}
