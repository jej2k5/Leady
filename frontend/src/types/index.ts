export type LeadStatus = 'new' | 'enriched' | 'scored' | 'qualified' | 'rejected';

export type PipelineStage = 'discovery' | 'enrichment' | 'scoring' | 'outreach' | 'closed';

export interface Lead {
  id: string;
  runId?: string;
  domain: string;
  companyName: string;
  industry?: string;
  employeeCount?: number;
  location?: string;
  score?: number;
  status: LeadStatus;
  createdAt?: string;
  updatedAt?: string;
}

export interface Run {
  id: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  startedAt?: string;
  finishedAt?: string;
  totalCandidates?: number;
  signalsCollected?: number;
  contactsCollected?: number;
}

export interface RunLogEntry {
  id: string;
  runId: string;
  timestamp: string;
  level: 'info' | 'success' | 'warning' | 'error';
  message: string;
}

export interface PipelineMetrics {
  stage: PipelineStage;
  totalLeads: number;
  conversionRate: number;
}

export interface AuthUser {
  id: string;
  email: string;
  name?: string;
}

export interface AuthSession {
  user: AuthUser;
  accessToken?: string;
  expires: string;
}
