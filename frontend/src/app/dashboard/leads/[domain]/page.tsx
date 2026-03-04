'use client';

import { use, useEffect } from 'react';

import { LeadDetail } from '@/components/leads/LeadDetail';
import { LeadFilters } from '@/components/leads/LeadFilters';
import { LeadTable } from '@/components/leads/LeadTable';
import { useLeadsStore } from '@/stores/leadsStore';

type DomainLeadsPageProps = {
  params: Promise<{
    domain: string;
  }>;
};

export default function DomainLeadsPage({ params }: DomainLeadsPageProps) {
  const { domain } = use(params);
  const { fetchLeads, setFilters } = useLeadsStore();

  useEffect(() => {
    setFilters({ query: domain });
    void fetchLeads();
  }, [domain, fetchLeads, setFilters]);

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold">Leads for {domain}</h2>
      <LeadFilters />
      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <LeadTable />
        <LeadDetail />
      </div>
    </div>
  );
}
