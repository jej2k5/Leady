import type { Lead } from '@/types';

export function CategoryBreakdown({ leads }: { leads: Lead[] }) {
  const breakdown = leads.reduce<Record<string, number>>((acc, lead) => {
    const key = lead.industry ?? 'Uncategorized';
    acc[key] = (acc[key] ?? 0) + 1;

    return acc;
  }, {});

  const sorted = Object.entries(breakdown).sort((a, b) => b[1] - a[1]);

  return (
    <div className="rounded border border-slate-200 p-4">
      <h3 className="mb-2 text-sm font-semibold">Industry Breakdown</h3>
      <ul className="space-y-1 text-sm">
        {sorted.slice(0, 6).map(([industry, count]) => (
          <li key={industry} className="flex justify-between">
            <span>{industry}</span>
            <span className="font-semibold">{count}</span>
          </li>
        ))}
        {!sorted.length && <li className="text-slate-500">No categories yet.</li>}
      </ul>
    </div>
  );
}
