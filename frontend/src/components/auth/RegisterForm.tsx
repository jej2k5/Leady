'use client';

import Link from 'next/link';
import { signIn } from 'next-auth/react';
import { useState } from 'react';

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export function RegisterForm() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError('Please enter email and password.');
      return;
    }

    setSubmitting(true);

    try {
      const response = await fetch(`${apiBaseUrl}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: email.trim(),
          password,
          name: name.trim() || undefined
        })
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
        setError(payload?.detail ?? 'Registration failed. Please try again.');
        setSubmitting(false);
        return;
      }

      const signInResult = await signIn('credentials', {
        email,
        password,
        redirect: false,
        callbackUrl: '/dashboard'
      });

      if (!signInResult || signInResult.error) {
        window.location.href = '/login?registered=1';
        return;
      }

      window.location.href = signInResult.url ?? '/dashboard';
    } catch {
      setError('Registration failed. Please try again.');
      setSubmitting(false);
      return;
    }

    setSubmitting(false);
  };

  return (
    <form className="space-y-3" onSubmit={onSubmit}>
      <p className="text-sm text-slate-600">Create your account to access the dashboard.</p>
      <div className="space-y-1">
        <label className="block text-xs font-medium text-slate-600" htmlFor="name">
          Name (optional)
        </label>
        <input
          id="name"
          type="text"
          autoComplete="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
          placeholder="Jane Doe"
        />
      </div>
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
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
          placeholder="At least 8 characters"
        />
      </div>
      {error ? <p className="text-xs text-red-600">{error}</p> : null}
      <button
        className="w-full rounded border border-slate-300 px-3 py-2 text-sm"
        type="submit"
        disabled={submitting}
      >
        {submitting ? 'Creating account…' : 'Create account'}
      </button>
      <p className="text-xs text-slate-600">
        Already have an account?{' '}
        <Link className="font-medium text-slate-900 underline" href="/login">
          Sign in
        </Link>
      </p>
    </form>
  );
}
