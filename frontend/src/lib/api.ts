import axios from 'axios';
import { getSession } from 'next-auth/react';

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export type CompanyDto = {
  id: number;
  run_id?: number | null;
  name: string;
  domain?: string | null;
  industry?: string | null;
  employee_count?: number | null;
  location?: string | null;
  score: number;
  created_at?: string | null;
  updated_at?: string | null;
};

export type RunDto = {
  run_id: number;
  status: 'queued' | 'running' | 'completed' | 'failed';
  started_at?: string | null;
  completed_at?: string | null;
  companies_discovered: number;
  signals_collected: number;
  contacts_collected: number;
};

export type StatsOverviewDto = {
  runs: number;
  companies: number;
  completed_runs: number;
  average_company_score: number;
};

export const apiClient = axios.create({
  baseURL: apiBaseUrl,
  headers: {
    'Content-Type': 'application/json'
  }
});

apiClient.interceptors.request.use(async (config) => {
  const session = await getSession();
  const token = session?.accessToken;

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export async function getCompanies(params?: { q?: string; runId?: number }): Promise<CompanyDto[]> {
  const response = await apiClient.get<CompanyDto[]>('/api/companies', {
    params: {
      q: params?.q,
      run_id: params?.runId
    }
  });

  return response.data;
}

export async function getCompany(companyId: number): Promise<CompanyDto> {
  const response = await apiClient.get<CompanyDto>(`/api/companies/${companyId}`);

  return response.data;
}

export async function getRuns(): Promise<RunDto[]> {
  const response = await apiClient.get<RunDto[]>('/api/runs');

  return response.data;
}

export async function createRun(status: RunDto['status'] = 'queued'): Promise<{ run_id: number }> {
  const response = await apiClient.post<{ run_id: number }>('/api/runs', { status });

  return response.data;
}

export async function updateRunStatus(runId: number, status: RunDto['status']): Promise<void> {
  await apiClient.patch(`/api/runs/${runId}`, { status });
}

export async function getStatsOverview(): Promise<StatsOverviewDto> {
  const response = await apiClient.get<StatsOverviewDto>('/api/stats/overview');

  return response.data;
}
