'use client';

import type { ReactNode } from 'react';
import { useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

import { AUTH_ERROR_EVENT, AUTH_ERROR_MESSAGE } from '@/lib/api';

type AuthGuardProps = {
  children: ReactNode;
};

export function AuthGuard({ children }: AuthGuardProps) {
  const { status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.replace('/login');
    }
  }, [router, status]);

  useEffect(() => {
    const onAuthError = () => {
      router.replace(`/login?reason=${encodeURIComponent('expired')}`);
    };

    window.addEventListener(AUTH_ERROR_EVENT, onAuthError);
    return () => {
      window.removeEventListener(AUTH_ERROR_EVENT, onAuthError);
    };
  }, [router]);

  if (status === 'loading') {
    return <p className="text-sm text-slate-600">Checking session...</p>;
  }

  if (status === 'unauthenticated') {
    return <p className="text-sm text-amber-700">{AUTH_ERROR_MESSAGE}</p>;
  }

  return <>{children}</>;
}
