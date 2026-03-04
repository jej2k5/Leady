'use client';

import { useEffect } from 'react';

import { LeadDetail } from '@/components/leads/LeadDetail';
import { LeadFilters } from '@/components/leads/LeadFilters';
import { LeadTable } from '@/components/leads/LeadTable';
import { useLeadsStore } from '@/stores/leadsStore';

export default function DashboardLeadsPage() {
  const { loading, error, fetchLeads } = useLeadsStore();

  useEffect(() => {
    void fetchLeads();
  }, [fetchLeads]);

  return (
    <div className="space-y-4">
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
