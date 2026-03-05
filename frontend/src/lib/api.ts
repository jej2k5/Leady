import axios from 'axios';
import { getSession } from 'next-auth/react';

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export const AUTH_ERROR_EVENT = 'leady:auth-error';
export const AUTH_ERROR_MESSAGE = 'Session expired or not authenticated.';

export class AuthError extends Error {
  readonly code = 'AUTH_REQUIRED';

  constructor(message = AUTH_ERROR_MESSAGE) {
    super(message);
    this.name = 'AuthError';
  }
}

export function isAuthError(error: unknown): error is AuthError {
  return error instanceof AuthError;
}

function isProtectedRoute(url?: string): boolean {
  if (!url) {
    return false;
  }

  const pathname = url.startsWith('http') ? new URL(url).pathname : url;
  return pathname.startsWith('/api/');
}

function broadcastAuthError(message: string): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.dispatchEvent(new CustomEvent(AUTH_ERROR_EVENT, { detail: { message } }));
}

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


export type StartPipelineRunRequest = {
  days?: number;
  sources?: string;
  include_unknown_stage?: boolean;
  source_seed_data?: Record<string, Array<Record<string, string | number | boolean | null>>>;
};

export type DiscoveryCandidateEvidenceDto = {
  source_type?: string | null;
  source_url?: string | null;
  payload?: Record<string, string | number | boolean | null | undefined>;
  seen_at?: string | null;
};

export type DiscoveryCandidateDto = {
  id: number;
  company_name: string;
  domain?: string | null;
  source_type: string;
  source_url?: string | null;
  score: number;
  status: string;
  category?: string | null;
  stage?: string | null;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
  evidence: DiscoveryCandidateEvidenceDto[];
};

export type ListDiscoveryCandidatesParams = {
  category?: string;
  stage?: string;
  source?: string;
  minScore?: number;
};

export type ApproveDiscoveryCandidatesRequest = {
  candidate_ids: number[];
  action: 'approve' | 'reject';
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
  if (!isProtectedRoute(config.url)) {
    return config;
  }

  const session = await getSession();
  const token = session?.accessToken;

  if (!token) {
    throw new AuthError();
  }

  config.headers.Authorization = `Bearer ${token}`;

  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (isAuthError(error)) {
      broadcastAuthError(error.message);
      return Promise.reject(error);
    }

    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const authError = new AuthError();
      broadcastAuthError(authError.message);
      return Promise.reject(authError);
    }

    return Promise.reject(error);
  }
);

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

export async function startPipelineRun(payload?: StartPipelineRunRequest): Promise<{ run_id: number; status: string }> {
  const response = await apiClient.post<{ run_id: number; status: string }>(`/api/pipeline/start`, payload ?? {});

  return response.data;
}

export async function getStatsOverview(): Promise<StatsOverviewDto> {
  const response = await apiClient.get<StatsOverviewDto>('/api/stats/overview');

  return response.data;
}

export async function listDiscoveryCandidates(
  params?: ListDiscoveryCandidatesParams
): Promise<DiscoveryCandidateDto[]> {
  const response = await apiClient.get<DiscoveryCandidateDto[]>('/api/discovery/candidates', {
    params: {
      category: params?.category,
      stage: params?.stage,
      source: params?.source,
      min_score: params?.minScore
    }
  });

  return response.data;
}

export async function approveDiscoveryCandidates(payload: ApproveDiscoveryCandidatesRequest): Promise<void> {
  await apiClient.post('/api/discovery/candidates/approve', payload);
}
