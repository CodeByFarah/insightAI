import type { Insight } from '../types';
import { EmptyState } from './States';

export function InsightList({ insights }: { insights: Insight[] }) {
  if (insights.length === 0) {
    return (
      <EmptyState
        title="No issues found"
        description="The analysis did not flag missing data, duplicates, strong correlations or imbalanced categories in this dataset."
      />
    );
  }

  return (
    <div className="stack" style={{ gap: 8 }}>
      {insights.map((insight) => (
        <article key={insight.id} className={`insight insight--${insight.severity}`}>
          <div className="insight__top">
            <span className="insight__title">{insight.title}</span>
            <span className="insight__metric">{insight.metric}</span>
          </div>
          <p className="insight__description">{insight.description}</p>
        </article>
      ))}
    </div>
  );
}
