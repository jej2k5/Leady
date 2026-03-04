import type { ReactNode } from 'react';
import Link from 'next/link';

type DashboardShellProps = {
  children: ReactNode;
};

export function DashboardShell({ children }: DashboardShellProps) {
  return (
    <div>
      <aside>
        <nav>
          <Link href="/dashboard">Overview</Link> | <Link href="/dashboard/leads">Leads</Link> |{' '}
          <Link href="/dashboard/runs">Runs</Link> | <Link href="/dashboard/pipeline">Pipeline</Link> |{' '}
          <Link href="/dashboard/settings">Settings</Link>
        </nav>
      </aside>
      <section>{children}</section>
    </div>
  );
}
