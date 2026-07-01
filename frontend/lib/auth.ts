import type { NextAuthOptions } from 'next-auth';
import OktaProvider from 'next-auth/providers/okta';

/**
 * Shared NextAuth config — used by the route handler (app/api/auth/[...nextauth])
 * and anywhere else that needs getServerSession(authOptions).
 *
 * Requires OKTA_CLIENT_ID / OKTA_CLIENT_SECRET / OKTA_ISSUER and NEXTAUTH_SECRET
 * to be set server-side (see .env.local.example). None of these are NEXT_PUBLIC_ —
 * the OIDC exchange happens entirely server-side.
 */
export const authOptions: NextAuthOptions = {
  providers: [
    OktaProvider({
      clientId: process.env.OKTA_CLIENT_ID || '',
      clientSecret: process.env.OKTA_CLIENT_SECRET || '',
      issuer: process.env.OKTA_ISSUER || '',
    }),
  ],
  session: {
    strategy: 'jwt',
  },
  callbacks: {
    async session({ session, token }) {
      if (session.user) {
        session.user.name = (token.name as string) || session.user.name;
        session.user.email = (token.email as string) || session.user.email;
      }
      return session;
    },
  },
};
