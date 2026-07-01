/** Supabase timestamps sometimes lack a timezone suffix; append Z to force UTC. */
const asUtc = (s: string) => new Date(s.endsWith('Z') || s.includes('+') ? s : s + 'Z');

export const fmtDateTime = (s?: string | null) =>
  s ? asUtc(s).toLocaleString('en-GB') : '—';

export const fmtTime = () => new Date().toLocaleTimeString();
