'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';

import { LeadDetail } from '@/components/leads/LeadDetail';
import { LeadFilters } from '@/components/leads/LeadFilters';
import { LeadTable } from '@/components/leads/LeadTable';
import { useLeadsStore } from '@/stores/leadsStore';

export default function DomainLeadsPage() {
  const { domain } = useParams<{ domain: string }>();
  const { loading, error, setFilters } = useLeadsStore();

  useEffect(() => {
    setFilters({ query: domain });
  }, [domain, setFilters]);

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Leads for {domain}</h2>
      <LeadFilters />
      {loading && <p className="text-sm text-slate-500">Loading leads...</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <LeadTable />
        <LeadDetail />
      </div>
    </div>
  );
}
