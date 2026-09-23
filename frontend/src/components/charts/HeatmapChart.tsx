import type { Visualization } from '../../types';

/** Correlation heatmap. A CSS grid reads better here than a charting library. */
export function HeatmapChart({ chart }: { chart: Visualization }) {
  const columns = (chart.meta?.columns as string[] | undefined) ?? [];
  if (columns.length === 0) return null;

  const lookup = new Map<string, number | null>();
  for (const cell of chart.data) {
    lookup.set(`${cell.y as string}::${cell.x as string}`, (cell.value as number) ?? null);
  }

  return (
    <div
      className="heatmap"
      style={{ gridTemplateColumns: `minmax(90px, auto) repeat(${columns.length}, 1fr)` }}
    >
      <span />
      {columns.map((column) => (
        <span key={`head-${column}`} className="heatmap__label heatmap__label--top">
          {column}
        </span>
      ))}
      {columns.map((rowName) => (
        <Row key={rowName} rowName={rowName} columns={columns} lookup={lookup} />
      ))}
    </div>
  );
}

function Row({
  rowName,
  columns,
  lookup,
}: {
  rowName: string;
  columns: string[];
  lookup: Map<string, number | null>;
}) {
  return (
    <>
      <span className="heatmap__label">{rowName}</span>
      {columns.map((columnName) => {
        const value = lookup.get(`${rowName}::${columnName}`) ?? null;
        return (
          <span
            key={`${rowName}-${columnName}`}
            className="heatmap__cell"
            style={{ background: cellColor(value), color: textColor(value) }}
            title={`${rowName} vs ${columnName}: ${value ?? 'n/a'}`}
          >
            {value === null ? '—' : value.toFixed(2)}
          </span>
        );
      })}
    </>
  );
}

/** Blue for positive, amber for negative, intensity by strength. */
function cellColor(value: number | null): string {
  if (value === null) return 'var(--surface-muted)';
  const intensity = Math.min(Math.abs(value), 1);
  return value >= 0
    ? `rgba(31, 95, 214, ${0.08 + intensity * 0.72})`
    : `rgba(180, 95, 6, ${0.08 + intensity * 0.72})`;
}

function textColor(value: number | null): string {
  return value !== null && Math.abs(value) > 0.6 ? '#fff' : 'var(--text)';
}
