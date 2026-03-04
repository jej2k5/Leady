'use client';

import { useLeadsStore } from '@/stores/leadsStore';

import { ScoreBadge } from './ScoreBadge';

export function LeadDetail() {
  const { leads, selectedLeadId } = useLeadsStore();
  const selected = leads.find((lead) => lead.id === selectedLeadId);

  if (!selected) {
    return <div className="rounded border border-dashed border-slate-300 p-4 text-sm text-slate-500">Select a lead to see details.</div>;
  }

  return (
    <div className="rounded border border-slate-200 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-lg font-semibold">{selected.companyName}</h3>
        <ScoreBadge score={selected.score} />
      </div>
      <dl className="grid grid-cols-2 gap-2 text-sm">
        <dt className="text-slate-500">Domain</dt>
        <dd>{selected.domain}</dd>
        <dt className="text-slate-500">Industry</dt>
        <dd>{selected.industry ?? 'Unknown'}</dd>
        <dt className="text-slate-500">Employees</dt>
        <dd>{selected.employeeCount ?? 'N/A'}</dd>
        <dt className="text-slate-500">Location</dt>
        <dd>{selected.location ?? 'N/A'}</dd>
      </dl>
    </div>
  );
}
