import type { ReactNode } from 'react';

import { AuthGuard } from './AuthGuard';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

type DashboardShellProps = {
  children: ReactNode;
};

export function DashboardShell({ children }: DashboardShellProps) {
  return (
    <AuthGuard>
      <div className="flex min-h-screen gap-6">
        <Sidebar />
        <section className="flex-1">
          <Header />
          {children}
        </section>
      </div>
    </AuthGuard>
  );
}
