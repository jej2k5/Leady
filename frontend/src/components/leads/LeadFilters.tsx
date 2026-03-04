'use client';

import { useEffect } from 'react';

import { useLeadsStore } from '@/stores/leadsStore';

export function LeadFilters() {
  const { filters, setFilters, fetchLeads } = useLeadsStore();

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      void fetchLeads();
    }, 300);

    return () => {
      window.clearTimeout(timeout);
    };
  }, [fetchLeads, filters.query, filters.minScore]);

  return (
    <div className="mb-4 flex gap-3">
      <input
        className="w-full max-w-sm rounded border border-slate-300 px-3 py-2 text-sm"
        placeholder="Search companies"
        value={filters.query}
        onChange={(event) => setFilters({ query: event.target.value })}
      />
      <select
        className="rounded border border-slate-300 px-3 py-2 text-sm"
        value={filters.minScore ?? ''}
        onChange={(event) =>
          setFilters({
            minScore: event.target.value ? Number(event.target.value) : undefined
          })
        }
      >
        <option value="">Any score</option>
        <option value="40">40+</option>
        <option value="75">75+</option>
      </select>
    </div>
  );
}
