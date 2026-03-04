type StatsCardsProps = {
  runs: number;
  companies: number;
  completedRuns: number;
  averageScore: number;
};

export function StatsCards({ runs, companies, completedRuns, averageScore }: StatsCardsProps) {
  const cards = [
    { label: 'Total Runs', value: runs },
    { label: 'Companies', value: companies },
    { label: 'Completed Runs', value: completedRuns },
    { label: 'Avg. Score', value: averageScore }
  ];

  return (
    <div className="grid gap-3 md:grid-cols-4">
      {cards.map((card) => (
        <div key={card.label} className="rounded border border-slate-200 p-4">
          <p className="text-xs uppercase tracking-wide text-slate-500">{card.label}</p>
          <p className="mt-1 text-2xl font-semibold">{card.value}</p>
        </div>
      ))}
    </div>
  );
}
