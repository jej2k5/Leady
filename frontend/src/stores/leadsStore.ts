import { create } from 'zustand';

import { getCompanies, type CompanyDto } from '@/lib/api';
import type { Lead } from '@/types';

type LeadsFilters = {
  query: string;
  minScore?: number;
};

type Pagination = {
  page: number;
  pageSize: number;
};

type LeadsState = {
  leads: Lead[];
  loading: boolean;
  error?: string;
  selectedLeadId?: string;
  filters: LeadsFilters;
  pagination: Pagination;
  setFilters: (filters: Partial<LeadsFilters>) => void;
  setPagination: (pagination: Partial<Pagination>) => void;
  setSelectedLeadId: (id?: string) => void;
  fetchLeads: () => Promise<void>;
};

function mapCompanyToLead(company: CompanyDto): Lead {
  return {
    id: String(company.id),
    runId: company.run_id ? String(company.run_id) : undefined,
    domain: company.domain ?? 'unknown',
    companyName: company.name,
    industry: company.industry ?? undefined,
    employeeCount: company.employee_count ?? undefined,
    location: company.location ?? undefined,
    score: company.score,
    status: company.score > 75 ? 'qualified' : company.score > 40 ? 'scored' : 'new',
    createdAt: company.created_at ?? undefined,
    updatedAt: company.updated_at ?? undefined
  };
}

export const useLeadsStore = create<LeadsState>((set, get) => ({
  leads: [],
  loading: false,
  error: undefined,
  selectedLeadId: undefined,
  filters: {
    query: '',
    minScore: undefined
  },
  pagination: {
    page: 1,
    pageSize: 10
  },
  setFilters: (filters) =>
    set((state) => ({
      filters: { ...state.filters, ...filters },
      pagination: { ...state.pagination, page: 1 }
    })),
  setPagination: (pagination) =>
    set((state) => ({
      pagination: { ...state.pagination, ...pagination }
    })),
  setSelectedLeadId: (id) => set({ selectedLeadId: id }),
  fetchLeads: async () => {
    const { filters } = get();
    set({ loading: true, error: undefined });

    try {
      const companies = await getCompanies({
        q: filters.query || undefined
      });

      const mapped = companies
        .map(mapCompanyToLead)
        .filter((lead) => (filters.minScore ? (lead.score ?? 0) >= filters.minScore : true));

      set({ leads: mapped, loading: false });
    } catch (error) {
      set({
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch leads.'
      });
    }
  }
}));
