'use client';

import { signIn } from 'next-auth/react';

import { GoogleButton } from './GoogleButton';

export function LoginForm() {
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600">Sign in with your workspace credentials or Google.</p>
      <button
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        type="button"
        onClick={() => signIn('credentials', { callbackUrl: '/dashboard' })}
      >
        Sign in with Credentials
      </button>
      <GoogleButton />
    </div>
  );
}
