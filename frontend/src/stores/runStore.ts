import { getSession } from 'next-auth/react';
import { create } from 'zustand';

import { getRuns, startPipelineRun, type RunDto } from '@/lib/api';
import type { Run, RunLogEntry } from '@/types';

type RunState = {
  runs: Run[];
  activeRunId?: string;
  runLogs: Record<string, RunLogEntry[]>;
  loading: boolean;
  error?: string;
  streamTimerId?: number;
  eventSource?: EventSource;
  setActiveRunId: (id?: string) => void;
  fetchRuns: () => Promise<void>;
  triggerRun: () => Promise<void>;
  startRunLogStream: (runId: string) => Promise<void>;
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

function createLog(runId: string, message: string, level: RunLogEntry['level'] = 'info'): RunLogEntry {
  return {
    id: crypto.randomUUID(),
    runId,
    timestamp: new Date().toISOString(),
    level,
    message
  };
}

export const useRunStore = create<RunState>((set, get) => ({
  runs: [],
  activeRunId: undefined,
  runLogs: {},
  loading: false,
  error: undefined,
  streamTimerId: undefined,
  eventSource: undefined,
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
    set({ error: undefined });

    try {
      const { run_id } = await startPipelineRun();
      await get().fetchRuns();
      void get().startRunLogStream(String(run_id));
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Failed to start pipeline run.' });
    }
  },
  startRunLogStream: async (runId) => {
    get().stopRunLogStream();

    set((state) => ({
      activeRunId: runId,
      runLogs: {
        ...state.runLogs,
        [runId]: [...(state.runLogs[runId] ?? []), createLog(runId, `Connected to run ${runId} stream.`)]
      }
    }));

    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
    const session = await getSession();
    const token = session?.accessToken;
    const streamUrl = token
      ? `${apiBase}/api/runs/${runId}/stream?access_token=${encodeURIComponent(token)}`
      : `${apiBase}/api/runs/${runId}/stream`;

    try {
      const source = new EventSource(streamUrl);

      source.onmessage = (event) => {
        set((state) => ({
          runLogs: {
            ...state.runLogs,
            [runId]: [...(state.runLogs[runId] ?? []), createLog(runId, event.data)]
          }
        }));
      };

      source.onerror = () => {
        source.close();

        set((state) => ({
          runLogs: {
            ...state.runLogs,
            [runId]: [
              ...(state.runLogs[runId] ?? []),
              createLog(runId, 'SSE unavailable; using status polling fallback.', 'warning')
            ]
          },
          eventSource: undefined
        }));

        const timerId = window.setInterval(async () => {
          const runs = await getRuns();
          const current = runs.find((run) => String(run.run_id) === runId);

          if (!current) {
            return;
          }

          const level: RunLogEntry['level'] =
            current.status === 'failed' ? 'error' : current.status === 'completed' ? 'success' : 'info';

          set((state) => ({
            runs: runs.map(mapRun),
            runLogs: {
              ...state.runLogs,
              [runId]: [
                ...(state.runLogs[runId] ?? []),
                createLog(
                  runId,
                  `Status ${current.status}. Companies ${current.companies_discovered}, signals ${current.signals_collected}, contacts ${current.contacts_collected}.`,
                  level
                )
              ]
            }
          }));

          if (current.status === 'completed' || current.status === 'failed') {
            get().stopRunLogStream();
          }
        }, 5000);

        set({ streamTimerId: timerId });
      };

      set({ eventSource: source });
    } catch {
      set((state) => ({
        runLogs: {
          ...state.runLogs,
          [runId]: [...(state.runLogs[runId] ?? []), createLog(runId, 'Unable to start stream client.', 'error')]
        }
      }));
    }
  },
  stopRunLogStream: () => {
    const { streamTimerId, eventSource } = get();

    if (eventSource) {
      eventSource.close();
    }

    if (streamTimerId) {
      window.clearInterval(streamTimerId);
    }

    set({ streamTimerId: undefined, eventSource: undefined });
  }
}));
