'use client';

import { useEffect, useMemo, useState } from 'react';

import {
  approveDiscoveryCandidates,
  listDiscoveryCandidates,
  startPipelineRun,
  type DiscoveryCandidateDto,
  type StartPipelineRunRequest
} from '@/lib/api';

type Filters = {
  category: string;
  stage: string;
  source: string;
  minScore: string;
};

function getEvidencePayload(candidate: DiscoveryCandidateDto, sourceType?: string) {
  const matching = sourceType
    ? candidate.evidence.find((entry) => entry.source_type === sourceType)
    : candidate.evidence[0];

  return matching?.payload ?? {};
}

function getFundingSnippet(candidate: DiscoveryCandidateDto): string | undefined {
  const payload = getEvidencePayload(candidate, 'funding');
  const sentence = payload.text ?? payload.funding_sentence;
  return typeof sentence === 'string' && sentence.trim() ? sentence : undefined;
}

function getHiringSnippet(candidate: DiscoveryCandidateDto): string | undefined {
  const payload = getEvidencePayload(candidate, 'hiring');
  const summary = payload.description ?? payload.role_summary;
  return typeof summary === 'string' && summary.trim() ? summary : undefined;
}

function getGithubStars(candidate: DiscoveryCandidateDto): number | undefined {
  const payload = getEvidencePayload(candidate, 'github');
  const stars = payload.stars;
  return typeof stars === 'number' ? stars : undefined;
}

function toSeedsBySource(selectedCandidates: DiscoveryCandidateDto[]): NonNullable<StartPipelineRunRequest['source_seed_data']> {
  const sourceSeedData: NonNullable<StartPipelineRunRequest['source_seed_data']> = {};

  for (const candidate of selectedCandidates) {
    const entries = candidate.evidence.length ? candidate.evidence : [{ source_type: candidate.source_type }];

    for (const evidence of entries) {
      const source = String(evidence.source_type ?? candidate.source_type ?? '').trim();
      if (!source) {
        continue;
      }

      const payload = evidence.payload ?? {};
      const baseSeed: Record<string, string | number | boolean | null> = {
        company_name: candidate.company_name,
        domain: candidate.domain ?? null,
        url:
          (typeof payload.url === 'string' && payload.url) ||
          (typeof evidence.source_url === 'string' && evidence.source_url) ||
          candidate.source_url ||
          null
      };

      if (source === 'funding') {
        baseSeed.text = typeof payload.text === 'string' ? payload.text : null;
      }

      if (source === 'hiring') {
        baseSeed.description = typeof payload.description === 'string' ? payload.description : null;
      }

      if (source === 'github') {
        baseSeed.stars = typeof payload.stars === 'number' ? payload.stars : 0;
      }

      sourceSeedData[source] = sourceSeedData[source] ?? [];
      sourceSeedData[source].push(baseSeed);
    }
  }

  return sourceSeedData;
}

export default function DiscoveryDashboardPage() {
  const [candidates, setCandidates] = useState<DiscoveryCandidateDto[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [filters, setFilters] = useState<Filters>({ category: '', stage: '', source: '', minScore: '' });
  const [loading, setLoading] = useState(false);
  const [busyAction, setBusyAction] = useState<'approve' | 'reject' | 'run' | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function fetchCandidates() {
    setLoading(true);
    setError(null);

    try {
      const next = await listDiscoveryCandidates({
        category: filters.category || undefined,
        stage: filters.stage || undefined,
        source: filters.source || undefined,
        minScore: filters.minScore ? Number(filters.minScore) : undefined
      });
      setCandidates(next);
      setSelectedIds((current) => new Set([...current].filter((id) => next.some((item) => item.id === id))));
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Failed to load discovery candidates.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchCandidates();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters.category, filters.stage, filters.source, filters.minScore]);

  const selectedCandidates = useMemo(
    () => candidates.filter((candidate) => selectedIds.has(candidate.id)),
    [candidates, selectedIds]
  );

  const allSelected = candidates.length > 0 && selectedIds.size === candidates.length;

  function toggleCandidate(candidateId: number) {
    setSelectedIds((current) => {
      const next = new Set(current);
      if (next.has(candidateId)) {
        next.delete(candidateId);
      } else {
        next.add(candidateId);
      }
      return next;
    });
  }

  function toggleAll() {
    if (allSelected) {
      setSelectedIds(new Set());
      return;
    }
    setSelectedIds(new Set(candidates.map((candidate) => candidate.id)));
  }

  async function submitSelectionAction(action: 'approve' | 'reject') {
    if (!selectedIds.size) {
      setError('Select at least one candidate first.');
      return;
    }

    setBusyAction(action);
    setError(null);
    setSuccess(null);

    try {
      await approveDiscoveryCandidates({
        candidate_ids: [...selectedIds],
        action
      });
      setSuccess(action === 'approve' ? 'Selected candidates approved for next run.' : 'Selected candidates rejected.');
      setSelectedIds(new Set());
      await fetchCandidates();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to update selected candidates.');
    } finally {
      setBusyAction(null);
    }
  }

  async function runNowWithSelected() {
    if (!selectedCandidates.length) {
      setError('Select at least one candidate to run now.');
      return;
    }

    const sourceSeedData = toSeedsBySource(selectedCandidates);

    if (!Object.keys(sourceSeedData).length) {
      setError('No valid source evidence was found in the selected candidates.');
      return;
    }

    setBusyAction('run');
    setError(null);
    setSuccess(null);

    try {
      const result = await startPipelineRun({ source_seed_data: sourceSeedData });
      setSuccess(`Pipeline run #${result.run_id} started with ${selectedCandidates.length} selected candidates.`);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : 'Failed to start run with selected candidates.');
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded border border-slate-200 p-4">
        <h1 className="text-lg font-semibold text-slate-900">Discovery approval queue</h1>
        <p className="mt-1 text-sm text-slate-600">Review discovered companies and push approved seeds into the next run.</p>
      </div>

      <div className="grid gap-3 rounded border border-slate-200 p-4 md:grid-cols-4">
        <input
          className="rounded border border-slate-300 px-3 py-2 text-sm"
          placeholder="Category"
          value={filters.category}
          onChange={(event) => setFilters((current) => ({ ...current, category: event.target.value }))}
        />
        <input
          className="rounded border border-slate-300 px-3 py-2 text-sm"
          placeholder="Stage"
          value={filters.stage}
          onChange={(event) => setFilters((current) => ({ ...current, stage: event.target.value }))}
        />
        <input
          className="rounded border border-slate-300 px-3 py-2 text-sm"
          placeholder="Source"
          value={filters.source}
          onChange={(event) => setFilters((current) => ({ ...current, source: event.target.value }))}
        />
        <input
          type="number"
          className="rounded border border-slate-300 px-3 py-2 text-sm"
          placeholder="Min score"
          value={filters.minScore}
          onChange={(event) => setFilters((current) => ({ ...current, minScore: event.target.value }))}
        />
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          className="rounded bg-slate-900 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          disabled={!selectedIds.size || busyAction !== null}
          onClick={() => void submitSelectionAction('approve')}
        >
          {busyAction === 'approve' ? 'Approving...' : 'Approve for next run'}
        </button>
        <button
          type="button"
          className="rounded border border-slate-300 px-3 py-2 text-sm font-medium text-slate-800 hover:bg-slate-100 disabled:opacity-50"
          disabled={!selectedIds.size || busyAction !== null}
          onClick={() => void submitSelectionAction('reject')}
        >
          {busyAction === 'reject' ? 'Rejecting...' : 'Reject'}
        </button>
        <button
          type="button"
          className="rounded border border-emerald-600 px-3 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
          disabled={!selectedIds.size || busyAction !== null}
          onClick={() => void runNowWithSelected()}
        >
          {busyAction === 'run' ? 'Running...' : 'Run now with selected'}
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}
      {success && <p className="text-sm text-emerald-700">{success}</p>}

      <div className="overflow-x-auto rounded border border-slate-200">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left">
                <input type="checkbox" checked={allSelected} onChange={toggleAll} aria-label="Select all candidates" />
              </th>
              <th className="px-3 py-2 text-left font-semibold text-slate-700">Company</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-700">Category</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-700">Stage</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-700">Source</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-700">Score</th>
              <th className="px-3 py-2 text-left font-semibold text-slate-700">Evidence snippets</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 bg-white">
            {candidates.map((candidate) => {
              const fundingSnippet = getFundingSnippet(candidate);
              const hiringSnippet = getHiringSnippet(candidate);
              const githubStars = getGithubStars(candidate);
              const metadata = getEvidencePayload(candidate);

              return (
                <tr key={candidate.id} className="align-top">
                  <td className="px-3 py-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.has(candidate.id)}
                      onChange={() => toggleCandidate(candidate.id)}
                      aria-label={`Select ${candidate.company_name}`}
                    />
                  </td>
                  <td className="px-3 py-3 text-slate-900">
                    <p className="font-medium">{candidate.company_name}</p>
                    {candidate.domain && <p className="text-xs text-slate-500">{candidate.domain}</p>}
                  </td>
                  <td className="px-3 py-3 text-slate-700">{candidate.category ?? String(metadata.category ?? '—')}</td>
                  <td className="px-3 py-3 text-slate-700">{candidate.stage ?? String(metadata.stage ?? '—')}</td>
                  <td className="px-3 py-3 text-slate-700">{candidate.source_type}</td>
                  <td className="px-3 py-3 text-slate-700">{candidate.score.toFixed(2)}</td>
                  <td className="px-3 py-3 text-xs text-slate-700">
                    <ul className="space-y-1">
                      <li>
                        <span className="font-semibold">Funding:</span> {fundingSnippet ?? 'N/A'}
                      </li>
                      <li>
                        <span className="font-semibold">Hiring:</span> {hiringSnippet ?? 'N/A'}
                      </li>
                      <li>
                        <span className="font-semibold">GitHub stars:</span> {typeof githubStars === 'number' ? githubStars : 'N/A'}
                      </li>
                    </ul>
                  </td>
                </tr>
              );
            })}
            {!candidates.length && !loading && (
              <tr>
                <td className="px-3 py-8 text-center text-slate-500" colSpan={7}>
                  No discovery candidates found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {loading && <p className="text-sm text-slate-500">Loading discovery candidates...</p>}
    </div>
  );
}
