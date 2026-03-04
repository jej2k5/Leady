'use client';

import { useEffect } from 'react';

import { RunLog } from '@/components/pipeline/RunLog';
import { RunTrigger } from '@/components/pipeline/RunTrigger';
import { useRunStore } from '@/stores/runStore';

export default function DashboardPipelinePage() {
  const { runs, fetchRuns, loading } = useRunStore();

  useEffect(() => {
    void fetchRuns();
  }, [fetchRuns]);

  return (
    <div className="space-y-4">
      <RunTrigger />
      {loading && <p className="text-sm text-slate-500">Refreshing pipeline runs...</p>}
      <div className="rounded border border-slate-200 p-4">
        <h2 className="mb-2 text-sm font-semibold">Run Queue</h2>
        <ul className="space-y-1 text-sm">
          {runs.map((run) => (
            <li key={run.id}>#{run.id} — {run.status}</li>
          ))}
          {!runs.length && <li>No runs yet.</li>}
        </ul>
      </div>
      <RunLog />
    </div>
  );
}
