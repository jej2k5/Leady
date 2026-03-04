import type { Lead } from '@/types';

export function ScoreDistribution({ leads }: { leads: Lead[] }) {
  const buckets = [
    { label: 'High (75+)', value: leads.filter((lead) => (lead.score ?? 0) >= 75).length, color: 'bg-green-500' },
    {
      label: 'Medium (40-74)',
      value: leads.filter((lead) => (lead.score ?? 0) >= 40 && (lead.score ?? 0) < 75).length,
      color: 'bg-amber-500'
    },
    { label: 'Low (<40)', value: leads.filter((lead) => (lead.score ?? 0) < 40).length, color: 'bg-slate-500' }
  ];

  const total = Math.max(1, leads.length);

  return (
    <div className="rounded border border-slate-200 p-4">
      <h3 className="mb-3 text-sm font-semibold">Score Distribution</h3>
      <div className="space-y-2">
        {buckets.map((bucket) => (
          <div key={bucket.label}>
            <div className="mb-1 flex justify-between text-xs">
              <span>{bucket.label}</span>
              <span>{bucket.value}</span>
            </div>
            <div className="h-2 rounded bg-slate-100">
              <div className={`h-2 rounded ${bucket.color}`} style={{ width: `${(bucket.value / total) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
