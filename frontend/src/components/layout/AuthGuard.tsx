'use client';

import type { ReactNode } from 'react';
import { useEffect, useState } from 'react';
import { getSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

type AuthGuardProps = {
  children: ReactNode;
};

export function AuthGuard({ children }: AuthGuardProps) {
  const [isAllowed, setIsAllowed] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    async function validate() {
      const session = await getSession();

      if (!session) {
        router.replace('/login');
      } else {
        setIsAllowed(true);
      }

      setIsLoading(false);
    }

    void validate();
  }, [router]);

  if (isLoading) {
    return <p className="text-sm text-slate-600">Checking session...</p>;
  }

  if (!isAllowed) {
    return null;
  }

  return <>{children}</>;
}
