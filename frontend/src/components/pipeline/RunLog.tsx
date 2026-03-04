'use client';

import { useRunStore } from '@/stores/runStore';

const levelColor: Record<string, string> = {
  info: 'text-slate-100',
  success: 'text-green-300',
  warning: 'text-amber-300',
  error: 'text-red-300'
};

export function RunLog() {
  const { activeRunId, runLogs } = useRunStore();

  if (!activeRunId) {
    return <div className="rounded border border-dashed border-slate-300 p-4 text-sm text-slate-500">Trigger a run to start log streaming.</div>;
  }

  const logs = runLogs[activeRunId] ?? [];

  return (
    <div className="rounded border border-slate-200 p-4">
      <h3 className="mb-2 text-sm font-semibold">Run #{activeRunId} Log Stream</h3>
      <div className="max-h-64 space-y-1 overflow-auto rounded bg-slate-950 p-3 font-mono text-xs text-slate-100">
        {logs.map((log) => (
          <p key={log.id} className={levelColor[log.level]}>
            [{new Date(log.timestamp).toLocaleTimeString()}] {log.message}
          </p>
        ))}
        {!logs.length && <p>No logs yet.</p>}
      </div>
    </div>
  );
}
