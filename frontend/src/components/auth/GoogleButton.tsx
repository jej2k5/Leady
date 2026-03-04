'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';

export function GoogleButton() {
  const [loading, setLoading] = useState(false);

  return (
    <button
      type="button"
      className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
      onClick={async () => {
        setLoading(true);
        await signIn('google', { callbackUrl: '/dashboard' });
      }}
      disabled={loading}
    >
      {loading ? 'Redirecting...' : 'Continue with Google'}
    </button>
  );
}
