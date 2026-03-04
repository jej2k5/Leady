import { create } from 'zustand';

import type { Run } from '@/types';

type RunState = {
  runs: Run[];
  activeRunId?: string;
  setRuns: (runs: Run[]) => void;
  setActiveRunId: (id?: string) => void;
};

export const useRunStore = create<RunState>((set) => ({
  runs: [],
  activeRunId: undefined,
  setRuns: (runs) => set({ runs }),
  setActiveRunId: (id) => set({ activeRunId: id })
}));
