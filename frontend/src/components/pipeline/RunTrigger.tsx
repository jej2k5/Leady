'use client';

import { useRunStore } from '@/stores/runStore';

export function RunTrigger() {
  const { triggerRun, loading } = useRunStore();

  return (
    <button
      type="button"
      className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40"
      onClick={() => void triggerRun()}
      disabled={loading}
    >
      Trigger Pipeline Run
    </button>
  );
}
