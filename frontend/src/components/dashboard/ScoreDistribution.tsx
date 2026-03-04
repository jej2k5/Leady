import type { Lead } from '@/types';

export function ScoreDistribution({ leads }: { leads: Lead[] }) {
  const buckets = {
    high: leads.filter((lead) => (lead.score ?? 0) >= 75).length,
    medium: leads.filter((lead) => (lead.score ?? 0) >= 40 && (lead.score ?? 0) < 75).length,
    low: leads.filter((lead) => (lead.score ?? 0) < 40).length
  };

  return (
    <div className="rounded border border-slate-200 p-4">
      <h3 className="mb-2 text-sm font-semibold">Score Distribution</h3>
      <p className="text-sm text-slate-700">High: {buckets.high}</p>
      <p className="text-sm text-slate-700">Medium: {buckets.medium}</p>
      <p className="text-sm text-slate-700">Low: {buckets.low}</p>
    </div>
  );
}
