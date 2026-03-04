import type { Run } from '@/types';

export function RecentActivity({ runs }: { runs: Run[] }) {
  return (
    <div className="rounded border border-slate-200 p-4">
      <h3 className="mb-2 text-sm font-semibold">Recent Activity</h3>
      <ul className="space-y-1 text-sm text-slate-700">
        {runs.slice(0, 5).map((run) => (
          <li key={run.id}>Run #{run.id} is {run.status}</li>
        ))}
        {!runs.length && <li>No recent runs available.</li>}
      </ul>
    </div>
  );
}
