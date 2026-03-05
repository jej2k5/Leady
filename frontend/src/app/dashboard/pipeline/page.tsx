'use client';

import { useEffect } from 'react';

import { RunLog } from '@/components/pipeline/RunLog';
import { RunTrigger } from '@/components/pipeline/RunTrigger';
import { useRunStore } from '@/stores/runStore';

export default function DashboardPipelinePage() {
  const { runs, fetchRuns, loading, error, setActiveRunId, startRunLogStream, stopRunLogStream } = useRunStore();

  useEffect(() => {
    void fetchRuns();

    return () => {
      stopRunLogStream();
    };
  }, [fetchRuns, stopRunLogStream]);

  return (
    <div className="space-y-4">
      <RunTrigger />
      {loading && <p className="text-sm text-slate-500">Refreshing pipeline runs...</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="rounded border border-slate-200 p-4">
        <h2 className="mb-2 text-sm font-semibold">Run Queue</h2>
        <ul className="space-y-1 text-sm">
          {runs.map((run) => (
            <li key={run.id} className="flex items-center justify-between">
              <span>#{run.id} — {run.status}</span>
              <button
                type="button"
                className="rounded border border-slate-300 px-2 py-1 text-xs"
                onClick={() => {
                  setActiveRunId(run.id);
                  void startRunLogStream(run.id);
                }}
              >
                View Logs
              </button>
            </li>
          ))}
          {!runs.length && <li>No runs yet.</li>}
        </ul>
      </div>
      <RunLog />
    </div>
  );
}
