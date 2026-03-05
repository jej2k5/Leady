'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';

import { AUTH_ERROR_MESSAGE } from '@/lib/api';

import { GoogleButton } from './GoogleButton';

export function LoginForm() {
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const sessionExpired = searchParams.get('reason') === 'expired';

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError('Please enter both email and password.');
      return;
    }

    setSubmitting(true);
    const result = await signIn('credentials', {
      email,
      password,
      redirect: false,
      callbackUrl: '/dashboard'
    });
    setSubmitting(false);

    if (!result || result.error) {
      setError('Sign in failed. Check your credentials and try again.');
      return;
    }

    window.location.href = result.url ?? '/dashboard';
  };

  return (
    <form className="space-y-3" onSubmit={onSubmit}>
      <p className="text-sm text-slate-600">Sign in with your workspace credentials or Google.</p>
      {sessionExpired ? <p className="text-xs text-amber-700">{AUTH_ERROR_MESSAGE}</p> : null}
      <div className="space-y-1">
        <label className="block text-xs font-medium text-slate-600" htmlFor="email">
          Email
        </label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
          placeholder="you@company.com"
        />
      </div>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-slate-600" htmlFor="password">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
          placeholder="••••••••"
        />
      </div>
      {error ? <p className="text-xs text-red-600">{error}</p> : null}
      <button
        className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
        type="submit"
        disabled={submitting}
      >
        {submitting ? 'Signing in…' : 'Sign in with Credentials'}
      </button>
      <GoogleButton />
    </form>
  );
}
