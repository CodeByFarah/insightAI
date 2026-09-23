import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { Visualization } from '../../types';
import { formatNumber } from '../../utils/format';

interface BoxRow {
  column: string;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
}

/**
 * Recharts has no box plot, so the five-number summary is drawn as stacked
 * segments: an invisible offset up to the minimum, the whiskers, and the
 * inter-quartile box. The exact values stay available in the tooltip.
 */
export function BoxPlotChart({ chart }: { chart: Visualization }) {
  const rows = chart.data as unknown as BoxRow[];
  const data = rows.map((row) => ({
    column: row.column,
    offset: row.min,
    lowerWhisker: row.q1 - row.min,
    box: row.q3 - row.q1,
    upperWhisker: row.max - row.q3,
    raw: row,
  }));

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="column" tick={{ fontSize: 11 }} stroke="var(--text-faint)" />
        <YAxis tick={{ fontSize: 11 }} stroke="var(--text-faint)" width={64} />
        <Tooltip content={<BoxTooltip />} />
        <Bar dataKey="offset" stackId="box" fill="transparent" isAnimationActive={false} />
        <Bar dataKey="lowerWhisker" stackId="box" fill="#c3d4f2" isAnimationActive={false} />
        <Bar dataKey="box" stackId="box" fill="#1f5fd6" isAnimationActive={false} />
        <Bar dataKey="upperWhisker" stackId="box" fill="#c3d4f2" isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function BoxTooltip({ active, payload }: { active?: boolean; payload?: { payload: { raw: BoxRow } }[] }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload.raw;
  return (
    <div className="card" style={{ padding: 12 }}>
      <strong>{row.column}</strong>
      <dl style={{ margin: '8px 0 0', fontSize: 12 }}>
        {(['min', 'q1', 'median', 'q3', 'max'] as const).map((key) => (
          <div key={key} className="row row--between" style={{ gap: 16 }}>
            <dt className="muted">{key}</dt>
            <dd style={{ margin: 0 }}>{formatNumber(row[key])}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
