'use client';

import { signIn } from 'next-auth/react';

export function GoogleButton() {
  return (
    <button
      type="button"
      className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
      onClick={() => signIn('google', { callbackUrl: '/dashboard' })}
    >
      Continue with Google
    </button>
  );
}
