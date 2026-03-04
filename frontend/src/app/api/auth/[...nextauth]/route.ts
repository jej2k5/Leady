import NextAuth from 'next-auth';

import { authConfig } from '@/lib/auth';

export const { GET, POST } = NextAuth(authConfig).handlers;
