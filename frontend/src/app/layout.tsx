import './globals.css';
import type { Metadata } from 'next';
import type { ReactNode } from 'react';

import { AppProviders } from '@/components/layout/AppProviders';

export const metadata: Metadata = {
  title: 'Leady',
  description: 'Lead discovery and pipeline operations dashboard.'
};

type RootLayoutProps = {
  children: ReactNode;
};

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body>
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
