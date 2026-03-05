import type { NextAuthConfig } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import Google from 'next-auth/providers/google';

const googleClientId = process.env.GOOGLE_CLIENT_ID;
const googleClientSecret = process.env.GOOGLE_CLIENT_SECRET;
const isGoogleAuthConfigured = Boolean(googleClientId && googleClientSecret);

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
    ...(isGoogleAuthConfigured
      ? [
          Google({
            clientId: googleClientId,
            clientSecret: googleClientSecret
          })
        ]
      : [])
  ],
  session: {
    strategy: 'jwt'
  },
  pages: {
    signIn: '/login'
  },
  callbacks: {
    async jwt({ token, account, user }) {
      if (account?.provider === 'google' && account.access_token) {
        token.accessToken = account.access_token;
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
