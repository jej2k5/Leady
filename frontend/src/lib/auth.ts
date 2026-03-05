import type { NextAuthConfig } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import Google from 'next-auth/providers/google';

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export const authConfig: NextAuthConfig = {
  trustHost: true,
  providers: [
    Credentials({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }

        // TODO: Replace with backend authentication endpoint integration.
        return {
          id: String(credentials.email),
          email: String(credentials.email),
          name: String(credentials.email)
        };
      }
    }),
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID ?? '',
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? ''
    })
  ],
  session: {
    strategy: 'jwt'
  },
  pages: {
    signIn: '/login'
  },
  callbacks: {
    async jwt({ token, account, user }) {
      if (account?.provider === 'google') {
        const googleIdToken = typeof account.id_token === 'string' ? account.id_token : undefined;
        const googleAccessToken = typeof account.access_token === 'string' ? account.access_token : undefined;

        if (googleIdToken || googleAccessToken) {
          try {
            const response = await fetch(`${apiBaseUrl}/api/auth/google/exchange`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                id_token: googleIdToken,
                access_token: googleAccessToken
              })
            });

            if (response.ok) {
              const payload = (await response.json()) as { token?: string; user?: { id?: string } };
              if (payload.token) {
                token.accessToken = payload.token;
              }
              if (payload.user?.id) {
                token.userId = payload.user.id;
              }
            }
          } catch {
            // Keep existing token if the backend exchange temporarily fails.
          }
        }
      }

      if (user?.id) {
        token.userId = user.id;
      }

      return token;
    },
    async session({ session, token }) {
      if (session.user && token.userId) {
        session.user.id = String(token.userId);
      }

      if (token.accessToken) {
        session.accessToken = String(token.accessToken);
      }

      return session;
    }
  }
};
