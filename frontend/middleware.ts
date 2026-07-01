export { default } from 'next-auth/middleware';

// Only the DSL Change Management view requires a verified Okta identity —
// Chat, Audit Log, and Dashboard stay open. Unauthenticated requests to
// /dsl are redirected to Okta sign-in automatically.
export const config = {
  matcher: ['/dsl/:path*'],
};
