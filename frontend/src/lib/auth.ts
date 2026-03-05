import type { NextAuthConfig } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import Google from 'next-auth/providers/google';

const apiBaseUrl = process.env.API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

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

        const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            username: String(credentials.email),
            password: String(credentials.password)
          })
        });

        if (!response.ok) {
          return null;
        }

        const data = (await response.json()) as {
          token?: string;
          user?: {
            id?: string | number;
            email?: string;
            username?: string;
            name?: string;
            sub?: string;
            role?: string;
          };
        };

        if (!data.token) {
          return null;
        }

        return {
          id: String(data.user?.id ?? data.user?.sub ?? data.user?.email ?? credentials.email),
          email: String(data.user?.email ?? data.user?.username ?? credentials.email),
          name: String(data.user?.name ?? data.user?.email ?? credentials.email),
          role: data.user?.role,
          backendAccessToken: data.token
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
      if (account?.provider === 'google' && account.access_token) {
        token.accessToken = account.access_token;
      }

      if (user && 'backendAccessToken' in user && user.backendAccessToken) {
        token.accessToken = String(user.backendAccessToken);
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
