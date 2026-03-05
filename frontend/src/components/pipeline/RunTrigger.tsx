'use client';

import { useMemo, useState } from 'react';

import { useRunStore } from '@/stores/runStore';

export function RunTrigger() {
  const { triggerRun, loading } = useRunStore();
  const [seedDataText, setSeedDataText] = useState('');
  const [parseError, setParseError] = useState<string | undefined>();

  const hasSeedData = useMemo(() => seedDataText.trim().length > 0, [seedDataText]);

  function handleTriggerRun() {
    if (!hasSeedData) {
      setParseError(undefined);
      void triggerRun();
      return;
    }

    try {
      const seedData = JSON.parse(seedDataText) as Record<string, Array<Record<string, string | number | boolean | null>>>;
      setParseError(undefined);
      void triggerRun({ source_seed_data: seedData });
    } catch {
      setParseError('Seed data must be valid JSON.');
    }
  }

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-700" htmlFor="pipeline-seed-data">
        Optional source seed data (JSON)
      </label>
      <textarea
        id="pipeline-seed-data"
        className="min-h-28 w-full rounded border border-slate-300 px-3 py-2 font-mono text-xs text-slate-800"
        placeholder='{"funding":[{"company_name":"Acme","url":"https://example.com","text":"Raised round"}]}'
        value={seedDataText}
        onChange={(event) => setSeedDataText(event.target.value)}
      />
      <p className="text-xs text-slate-500">Supported keys: funding, hiring, github.</p>
      {parseError && <p className="text-xs text-red-600">{parseError}</p>}
      <button
        type="button"
        className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40"
        onClick={handleTriggerRun}
        disabled={loading}
      >
        {loading ? 'Starting...' : 'Trigger Pipeline Run'}
      </button>
    </div>
  );
}
