'use client';

import { useEffect, useState } from 'react';

import { getStatsOverview } from '@/lib/api';
import { useLeadsStore } from '@/stores/leadsStore';
import { useRunStore } from '@/stores/runStore';

import { CategoryBreakdown } from './CategoryBreakdown';
import { RecentActivity } from './RecentActivity';
import { ScoreDistribution } from './ScoreDistribution';
import { StatsCards } from './StatsCards';

export function DashboardOverview() {
  const { leads, fetchLeads } = useLeadsStore();
  const { runs, fetchRuns } = useRunStore();
  const [stats, setStats] = useState({ runs: 0, companies: 0, completed_runs: 0, average_company_score: 0 });

  useEffect(() => {
    void fetchLeads();
    void fetchRuns();
    void getStatsOverview().then(setStats).catch(() => undefined);
  }, [fetchLeads, fetchRuns]);

  return (
    <div className="space-y-4">
      <StatsCards
        runs={stats.runs}
        companies={stats.companies}
        completedRuns={stats.completed_runs}
        averageScore={stats.average_company_score}
      />
      <div className="grid gap-4 md:grid-cols-3">
        <ScoreDistribution leads={leads} />
        <CategoryBreakdown leads={leads} />
        <RecentActivity runs={runs} />
      </div>
    </div>
  );
}
