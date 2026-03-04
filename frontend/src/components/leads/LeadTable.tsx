'use client';

import { useMemo } from 'react';

import { useLeadsStore } from '@/stores/leadsStore';

import { ScoreBadge } from './ScoreBadge';

export function LeadTable() {
  const { leads, pagination, setPagination, setSelectedLeadId } = useLeadsStore();

  const paginatedLeads = useMemo(() => {
    const start = (pagination.page - 1) * pagination.pageSize;

    return leads.slice(start, start + pagination.pageSize);
  }, [leads, pagination.page, pagination.pageSize]);

  const totalPages = Math.max(1, Math.ceil(leads.length / pagination.pageSize));

  return (
    <div className="rounded border border-slate-200">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-slate-600">
          <tr>
            <th className="px-3 py-2">Company</th>
            <th className="px-3 py-2">Domain</th>
            <th className="px-3 py-2">Score</th>
            <th className="px-3 py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {paginatedLeads.map((lead) => (
            <tr key={lead.id} className="cursor-pointer border-t border-slate-100 hover:bg-slate-50" onClick={() => setSelectedLeadId(lead.id)}>
              <td className="px-3 py-2">{lead.companyName}</td>
              <td className="px-3 py-2">{lead.domain}</td>
              <td className="px-3 py-2">
                <ScoreBadge score={lead.score} />
              </td>
              <td className="px-3 py-2 capitalize">{lead.status}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="flex items-center justify-between border-t border-slate-200 p-3">
        <p className="text-xs text-slate-600">
          Page {pagination.page} / {totalPages}
        </p>
        <div className="flex gap-2">
          <button
            className="rounded border border-slate-300 px-2 py-1 text-xs disabled:opacity-40"
            type="button"
            disabled={pagination.page === 1}
            onClick={() => setPagination({ page: pagination.page - 1 })}
          >
            Prev
          </button>
          <button
            className="rounded border border-slate-300 px-2 py-1 text-xs disabled:opacity-40"
            type="button"
            disabled={pagination.page >= totalPages}
            onClick={() => setPagination({ page: pagination.page + 1 })}
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
