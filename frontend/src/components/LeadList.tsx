export interface LeadListProps {
  leads: Array<{ id: string; name: string }>;
}

export function LeadList({ leads }: LeadListProps) {
  return (
    <ul>
      {leads.map((lead) => (
        <li key={lead.id}>{lead.name}</li>
      ))}
    </ul>
  );
}
