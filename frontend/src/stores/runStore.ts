import { create } from 'zustand';

import { createRun, getRuns, updateRunStatus, type RunDto } from '@/lib/api';
import type { Run, RunLogEntry } from '@/types';

type RunState = {
  runs: Run[];
  activeRunId?: string;
  runLogs: Record<string, RunLogEntry[]>;
  loading: boolean;
  error?: string;
  streamTimerId?: number;
  setActiveRunId: (id?: string) => void;
  fetchRuns: () => Promise<void>;
  triggerRun: () => Promise<void>;
  startRunLogStream: (runId: string) => void;
  stopRunLogStream: () => void;
};

function mapRun(run: RunDto): Run {
  return {
    id: String(run.run_id),
    status: run.status,
    startedAt: run.started_at ?? undefined,
    finishedAt: run.completed_at ?? undefined,
    totalCandidates: run.companies_discovered,
    signalsCollected: run.signals_collected,
    contactsCollected: run.contacts_collected
  };
}

export const useRunStore = create<RunState>((set, get) => ({
  runs: [],
  activeRunId: undefined,
  runLogs: {},
  loading: false,
  error: undefined,
  streamTimerId: undefined,
  setActiveRunId: (id) => set({ activeRunId: id }),
  fetchRuns: async () => {
    set({ loading: true, error: undefined });

    try {
      const runs = await getRuns();
      set({ runs: runs.map(mapRun), loading: false });
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Failed to load runs.' });
    }
  },
  triggerRun: async () => {
    try {
      const { run_id } = await createRun('queued');
      await updateRunStatus(run_id, 'running');
      await get().fetchRuns();
      set({ activeRunId: String(run_id) });
      get().startRunLogStream(String(run_id));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to trigger run.' });
    }
  },
  startRunLogStream: (runId) => {
    const { streamTimerId } = get();
    if (streamTimerId) {
      window.clearInterval(streamTimerId);
    }

    set((state) => ({
      runLogs: {
        ...state.runLogs,
        [runId]: [
          ...(state.runLogs[runId] ?? []),
          {
            id: crypto.randomUUID(),
            runId,
            timestamp: new Date().toISOString(),
            level: 'info',
            message: `Run ${runId} stream started.`
          }
        ]
      }
    }));

    const timerId = window.setInterval(async () => {
      const runs = await getRuns();
      const current = runs.find((run) => String(run.run_id) === runId);

      if (!current) {
        return;
      }

      const statusMessage = `Run ${runId} status: ${current.status}. Companies: ${current.companies_discovered}, Signals: ${current.signals_collected}`;

      set((state) => ({
        runs: runs.map(mapRun),
        runLogs: {
          ...state.runLogs,
          [runId]: [
            ...(state.runLogs[runId] ?? []),
            {
              id: crypto.randomUUID(),
              runId,
              timestamp: new Date().toISOString(),
              level: current.status === 'failed' ? 'error' : current.status === 'completed' ? 'success' : 'info',
              message: statusMessage
            }
          ]
        }
      }));

      if (current.status === 'failed' || current.status === 'completed') {
        get().stopRunLogStream();
      }
    }, 5000);

    set({ streamTimerId: timerId, activeRunId: runId });
  },
  stopRunLogStream: () => {
    const { streamTimerId } = get();

    if (streamTimerId) {
      window.clearInterval(streamTimerId);
    }

    set({ streamTimerId: undefined });
  }
}));
