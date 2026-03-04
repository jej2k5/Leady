'use client';

import { signOut, useSession } from 'next-auth/react';

type HeaderProps = {
  title?: string;
  subtitle?: string;
};

export function Header({ title = 'Dashboard', subtitle = 'Track your lead pipeline end-to-end.' }: HeaderProps) {
  const { data: session } = useSession();

  return (
    <header className="mb-6 flex items-center justify-between border-b border-slate-200 pb-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        <p className="text-sm text-slate-600">{subtitle}</p>
      </div>
      <div className="flex items-center gap-3">
        <p className="hidden text-sm text-slate-500 md:block">{session?.user?.email}</p>
        <button
          className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
          type="button"
          onClick={() => signOut({ callbackUrl: '/login' })}
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
