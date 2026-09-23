import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { Visualization } from '../../types';
import { BoxPlotChart } from './BoxPlotChart';
import { HeatmapChart } from './HeatmapChart';

const AXIS = { fontSize: 11 };
const STROKE = 'var(--text-faint)';
const ACCENT = '#1f5fd6';

export function ChartCard({ chart }: { chart: Visualization }) {
  return (
    <figure className="chart-card" style={{ margin: 0 }}>
      <figcaption>
        <h3>{chart.title}</h3>
        <p className="card__description">{chart.description}</p>
      </figcaption>
      <div className="chart-card__body">{renderChart(chart)}</div>
    </figure>
  );
}

function renderChart(chart: Visualization) {
  switch (chart.type) {
    case 'histogram':
      return <Histogram chart={chart} />;
    case 'bar':
      return <CategoryBar chart={chart} />;
    case 'box':
      return <BoxPlotChart chart={chart} />;
    case 'scatter':
      return <ScatterPlot chart={chart} />;
    case 'timeseries':
      return <TimeSeries chart={chart} />;
    case 'heatmap':
      return <HeatmapChart chart={chart} />;
    default:
      return <p className="muted">This chart type is not supported.</p>;
  }
}

function Histogram({ chart }: { chart: Visualization }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chart.data} margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis
          dataKey="bin"
          tick={AXIS}
          stroke={STROKE}
          interval="preserveStartEnd"
          label={{ value: chart.x_label ?? '', position: 'insideBottom', offset: -16, fontSize: 11 }}
        />
        <YAxis tick={AXIS} stroke={STROKE} width={48} label={{ value: chart.y_label ?? '', angle: -90, position: 'insideLeft', fontSize: 11 }} />
        <Tooltip cursor={{ fill: 'var(--surface-muted)' }} />
        <Bar dataKey="count" name="Rows" fill={ACCENT} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function CategoryBar({ chart }: { chart: Visualization }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={chart.data} layout="vertical" margin={{ top: 8, right: 24, bottom: 8, left: 8 }}>
        <CartesianGrid stroke="var(--border)" horizontal={false} />
        <XAxis type="number" tick={AXIS} stroke={STROKE} />
        <YAxis type="category" dataKey="category" tick={AXIS} stroke={STROKE} width={120} />
        <Tooltip
          cursor={{ fill: 'var(--surface-muted)' }}
          formatter={(value: number, _name, item) => [
            `${value.toLocaleString()} rows (${(item.payload as { pct: number }).pct}%)`,
            chart.column ?? 'Rows',
          ]}
        />
        <Bar dataKey="count" name="Rows" fill={ACCENT} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function ScatterPlot({ chart }: { chart: Visualization }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
        <CartesianGrid stroke="var(--border)" />
        <XAxis
          type="number"
          dataKey="x"
          name={chart.x_label ?? 'x'}
          tick={AXIS}
          stroke={STROKE}
          label={{ value: chart.x_label ?? '', position: 'insideBottom', offset: -16, fontSize: 11 }}
        />
        <YAxis
          type="number"
          dataKey="y"
          name={chart.y_label ?? 'y'}
          tick={AXIS}
          stroke={STROKE}
          width={64}
          label={{ value: chart.y_label ?? '', angle: -90, position: 'insideLeft', fontSize: 11 }}
        />
        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
        <Scatter data={chart.data} fill={ACCENT} fillOpacity={0.55} isAnimationActive={false} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}

function TimeSeries({ chart }: { chart: Visualization }) {
  const valueColumn = chart.meta?.value_column as string | undefined;
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chart.data} margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
        <CartesianGrid stroke="var(--border)" vertical={false} />
        <XAxis dataKey="period" tick={AXIS} stroke={STROKE} minTickGap={24} />
        <YAxis tick={AXIS} stroke={STROKE} width={56} />
        <Tooltip />
        <Line type="monotone" dataKey="rows" name="Rows" stroke={ACCENT} dot={false} isAnimationActive={false} />
        {valueColumn ? (
          <Line
            type="monotone"
            dataKey="value"
            name={`Mean ${valueColumn}`}
            stroke="#9a6200"
            dot={false}
            isAnimationActive={false}
          />
        ) : null}
      </LineChart>
    </ResponsiveContainer>
  );
}
