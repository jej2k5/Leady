export type LeadStatus = 'new' | 'enriched' | 'scored' | 'qualified' | 'rejected';

export type PipelineStage = 'discovery' | 'enrichment' | 'scoring' | 'outreach' | 'closed';

export interface Lead {
  id: string;
  domain: string;
  companyName: string;
  contactName?: string;
  contactEmail?: string;
  score?: number;
  status: LeadStatus;
  createdAt: string;
  updatedAt: string;
}

export interface Run {
  id: string;
  source: string;
  status: 'queued' | 'running' | 'completed' | 'failed';
  startedAt?: string;
  finishedAt?: string;
  totalCandidates?: number;
  qualifiedLeads?: number;
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
