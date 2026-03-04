import type { Run } from '@/types';

export function RecentActivity({ runs }: { runs: Run[] }) {
  const recent = [...runs]
    .sort((a, b) => {
      const left = a.startedAt ? new Date(a.startedAt).getTime() : 0;
      const right = b.startedAt ? new Date(b.startedAt).getTime() : 0;

      return right - left;
    })
    .slice(0, 5);

  return (
    <div className="rounded border border-slate-200 p-4">
      <h3 className="mb-2 text-sm font-semibold">Recent Activity</h3>
      <ul className="space-y-1 text-sm text-slate-700">
        {recent.map((run) => (
          <li key={run.id}>
            Run #{run.id} is <span className="font-medium capitalize">{run.status}</span>
          </li>
        ))}
        {!recent.length && <li>No recent runs available.</li>}
      </ul>
    </div>
  );
}
