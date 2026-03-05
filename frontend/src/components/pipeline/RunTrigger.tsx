'use client';

import { useMemo, useState } from 'react';

import { useRunStore } from '@/stores/runStore';

type FundingSeed = {
  company_name: string;
  url: string;
  text: string;
};

type HiringSeed = {
  company_name: string;
  url: string;
  description: string;
};

type GithubSeed = {
  company_name: string;
  url: string;
  stars: number;
};

export function RunTrigger() {
  const { triggerRun, loading } = useRunStore();
  const [error, setError] = useState<string | undefined>();
  const [includeUnknownStage, setIncludeUnknownStage] = useState(false);

  const [funding, setFunding] = useState<FundingSeed>({ company_name: '', url: '', text: '' });
  const [hiring, setHiring] = useState<HiringSeed>({ company_name: '', url: '', description: '' });
  const [github, setGithub] = useState<GithubSeed>({ company_name: '', url: '', stars: 0 });

  const hasFundingSeed = useMemo(
    () => Boolean(funding.company_name.trim() || funding.url.trim() || funding.text.trim()),
    [funding.company_name, funding.url, funding.text]
  );
  const hasHiringSeed = useMemo(
    () => Boolean(hiring.company_name.trim() || hiring.url.trim() || hiring.description.trim()),
    [hiring.company_name, hiring.url, hiring.description]
  );
  const hasGithubSeed = useMemo(
    () => Boolean(github.company_name.trim() || github.url.trim() || github.stars > 0),
    [github.company_name, github.url, github.stars]
  );

  function handleTriggerRun() {
    const sourceSeedData: Record<string, Array<Record<string, string | number | boolean | null>>> = {};

    if (hasFundingSeed) {
      if (!funding.company_name.trim() || !funding.url.trim() || !funding.text.trim()) {
        setError('Funding seed requires company name, URL, and funding text.');
        return;
      }

      sourceSeedData.funding = [
        {
          company_name: funding.company_name.trim(),
          url: funding.url.trim(),
          text: funding.text.trim()
        }
      ];
    }

    if (hasHiringSeed) {
      if (!hiring.company_name.trim() || !hiring.url.trim() || !hiring.description.trim()) {
        setError('Hiring seed requires company name, URL, and description.');
        return;
      }

      sourceSeedData.hiring = [
        {
          company_name: hiring.company_name.trim(),
          url: hiring.url.trim(),
          description: hiring.description.trim()
        }
      ];
    }

    if (hasGithubSeed) {
      if (!github.company_name.trim() || !github.url.trim()) {
        setError('GitHub seed requires company name and repository URL.');
        return;
      }

      sourceSeedData.github = [
        {
          company_name: github.company_name.trim(),
          url: github.url.trim(),
          stars: github.stars
        }
      ];
    }

    setError(undefined);

    if (!Object.keys(sourceSeedData).length) {
      void triggerRun({ include_unknown_stage: includeUnknownStage });
      return;
    }

    void triggerRun({
      include_unknown_stage: includeUnknownStage,
      source_seed_data: sourceSeedData
    });
  }

  return (
    <div className="space-y-4">
      <div className="rounded border border-slate-200 p-3">
        <h3 className="mb-2 text-sm font-semibold">Funding seed</h3>
        <div className="grid gap-2 md:grid-cols-2">
          <input
            className="rounded border border-slate-300 px-2 py-1 text-sm"
            placeholder="Company name"
            value={funding.company_name}
            onChange={(event) => setFunding((current) => ({ ...current, company_name: event.target.value }))}
          />
          <input
            className="rounded border border-slate-300 px-2 py-1 text-sm"
            placeholder="Article URL"
            value={funding.url}
            onChange={(event) => setFunding((current) => ({ ...current, url: event.target.value }))}
          />
          <textarea
            className="md:col-span-2 min-h-16 rounded border border-slate-300 px-2 py-1 text-sm"
            placeholder="Funding text"
            value={funding.text}
            onChange={(event) => setFunding((current) => ({ ...current, text: event.target.value }))}
          />
        </div>
      </div>

      <div className="rounded border border-slate-200 p-3">
        <h3 className="mb-2 text-sm font-semibold">Hiring seed</h3>
        <div className="grid gap-2 md:grid-cols-2">
          <input
            className="rounded border border-slate-300 px-2 py-1 text-sm"
            placeholder="Company name"
            value={hiring.company_name}
            onChange={(event) => setHiring((current) => ({ ...current, company_name: event.target.value }))}
          />
          <input
            className="rounded border border-slate-300 px-2 py-1 text-sm"
            placeholder="Job URL"
            value={hiring.url}
            onChange={(event) => setHiring((current) => ({ ...current, url: event.target.value }))}
          />
          <textarea
            className="md:col-span-2 min-h-16 rounded border border-slate-300 px-2 py-1 text-sm"
            placeholder="Job description"
            value={hiring.description}
            onChange={(event) => setHiring((current) => ({ ...current, description: event.target.value }))}
          />
        </div>
      </div>

      <div className="rounded border border-slate-200 p-3">
        <h3 className="mb-2 text-sm font-semibold">GitHub seed</h3>
        <div className="grid gap-2 md:grid-cols-3">
          <input
            className="rounded border border-slate-300 px-2 py-1 text-sm"
            placeholder="Company name"
            value={github.company_name}
            onChange={(event) => setGithub((current) => ({ ...current, company_name: event.target.value }))}
          />
          <input
            className="rounded border border-slate-300 px-2 py-1 text-sm"
            placeholder="Repository URL"
            value={github.url}
            onChange={(event) => setGithub((current) => ({ ...current, url: event.target.value }))}
          />
          <input
            type="number"
            className="rounded border border-slate-300 px-2 py-1 text-sm"
            placeholder="Stars"
            value={github.stars}
            onChange={(event) => setGithub((current) => ({ ...current, stars: Number(event.target.value) || 0 }))}
          />
        </div>
      </div>

      <div className="rounded border border-slate-200 p-3">
        <label className="flex items-center gap-2 text-sm font-medium text-slate-800">
          <input
            type="checkbox"
            checked={includeUnknownStage}
            onChange={(event) => setIncludeUnknownStage(event.target.checked)}
          />
          Include unknown stage leads
        </label>
        <p className="mt-2 text-xs text-slate-500">
          Leads with an unknown stage may otherwise be hidden from this run.
        </p>
      </div>

      {error && <p className="text-xs text-red-600">{error}</p>}

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
