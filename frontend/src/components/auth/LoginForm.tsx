'use client';

import { signIn } from 'next-auth/react';

export function LoginForm() {
  return (
    <div>
      <p>Credentials and Google auth placeholder.</p>
      <button type="button" onClick={() => signIn('credentials')}>
        Sign in with Credentials
      </button>
      <button type="button" onClick={() => signIn('google')}>
        Sign in with Google
      </button>
    </div>
  );
}
