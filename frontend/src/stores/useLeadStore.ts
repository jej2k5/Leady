import { create } from "zustand";

interface LeadState {
  selectedLeadId: string | null;
  setSelectedLeadId: (id: string | null) => void;
}

export const useLeadStore = create<LeadState>((set) => ({
  selectedLeadId: null,
  setSelectedLeadId: (id) => set({ selectedLeadId: id }),
}));
