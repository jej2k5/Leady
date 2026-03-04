'use client';

import { useEffect } from 'react';

import { RunLog } from '@/components/pipeline/RunLog';
import { useRunStore } from '@/stores/runStore';

export default function DashboardRunsPage() {
  const { runs, fetchRuns, setActiveRunId, startRunLogStream, stopRunLogStream } = useRunStore();

  useEffect(() => {
    void fetchRuns();

    return () => {
      stopRunLogStream();
    };
  }, [fetchRuns, stopRunLogStream]);

  return (
    <div className="space-y-4">
      <div className="rounded border border-slate-200 p-4">
        <h2 className="mb-2 text-sm font-semibold">Runs</h2>
        <ul className="space-y-2 text-sm">
          {runs.map((run) => (
            <li key={run.id} className="flex items-center justify-between rounded border border-slate-200 px-3 py-2">
              <span>Run #{run.id} — {run.status}</span>
              <button
                className="rounded border border-slate-300 px-2 py-1 text-xs"
                type="button"
                onClick={() => {
                  setActiveRunId(run.id);
                  startRunLogStream(run.id);
                }}
              >
                Stream Logs
              </button>
            </li>
          ))}
        </ul>
      </div>
      <RunLog />
    </div>
  );
}
