import { create } from 'zustand';

import type { Lead } from '@/types';

type LeadsState = {
  leads: Lead[];
  setLeads: (leads: Lead[]) => void;
  upsertLead: (lead: Lead) => void;
};

export const useLeadsStore = create<LeadsState>((set) => ({
  leads: [],
  setLeads: (leads) => set({ leads }),
  upsertLead: (lead) =>
    set((state) => {
      const existingIndex = state.leads.findIndex((current) => current.id === lead.id);

      if (existingIndex === -1) {
        return { leads: [lead, ...state.leads] };
      }

      const nextLeads = [...state.leads];
      nextLeads[existingIndex] = lead;

      return { leads: nextLeads };
    })
}));
