type ScoreBadgeProps = {
  score?: number;
};

export function ScoreBadge({ score = 0 }: ScoreBadgeProps) {
  const colorClass = score >= 75 ? 'bg-green-100 text-green-700' : score >= 40 ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-700';

  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${colorClass}`}>Score {Math.round(score)}</span>;
}
