import { useCallback, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ChartCard } from '../components/charts/ChartCard';
import { DatasetTabs } from '../components/DatasetTabs';
import { InsightList } from '../components/InsightList';
import { PageHeader } from '../components/PageHeader';
import { StatCard } from '../components/StatCard';
import { EmptyState, ErrorBanner, Loading } from '../components/States';
import { useAsync } from '../hooks/useAsync';
import { api, ApiError } from '../services/api';
import type { Analysis } from '../types';
import { formatDate, formatNumber, formatPercent } from '../utils/format';

export function AnalysisPage() {
  const { datasetId } = useParams();
  const id = Number(datasetId);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<ApiError | null>(null);

  const loader = useCallback(() => api.getAnalysis(id), [id]);
  const { data, loading, error, reload, setData } = useAsync<Analysis>(loader, [id]);

  async function run(force: boolean) {
    setRunning(true);
    setRunError(null);
    try {
      setData(await api.runAnalysis(id, force));
    } catch (err) {
      setRunError(err instanceof ApiError ? err : new ApiError(0, 'UNKNOWN', 'Analysis failed.'));
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <Loading label="Loading analysis…" />;

  const notAnalyzedYet = error?.code === 'ANALYSIS_NOT_FOUND';

  return (
    <div className="stack">
      <PageHeader
        title="Analysis"
        subtitle={
          data
            ? `Computed ${formatDate(data.created_at)} from the uploaded file.`
            : 'Run the analysis engine over this dataset.'
        }
        actions={
          <button
            type="button"
            className="button"
            disabled={running}
            onClick={() => void run(Boolean(data))}
          >
            {running ? 'Analyzing…' : data ? 'Re-run analysis' : 'Run analysis'}
          </button>
        }
      />
      <DatasetTabs datasetId={id} />

      {runError ? <ErrorBanner error={runError} /> : null}
      {error && !notAnalyzedYet ? <ErrorBanner error={error} onRetry={reload} /> : null}

      {notAnalyzedYet && !data ? (
        <EmptyState
          title="No analysis yet"
          description="Running an analysis computes statistics, data-quality checks, correlations, insights and charts. The result is stored, so it only has to run once."
          action={
            <button
              type="button"
              className="button"
              disabled={running}
              onClick={() => void run(false)}
            >
              {running ? 'Analyzing…' : 'Run analysis'}
            </button>
          }
        />
      ) : null}

      {data ? <AnalysisContent analysis={data} datasetId={id} /> : null}
    </div>
  );
}

function AnalysisContent({ analysis, datasetId }: { analysis: Analysis; datasetId: number }) {
  const { summary } = analysis;
  const quality = summary.data_quality;

  return (
    <>
      <section className="grid grid--stats">
        <StatCard
          label="Rows"
          value={formatNumber(summary.overview.rows)}
          hint={`${summary.overview.memory_usage_human} in memory`}
        />
        <StatCard
          label="Columns"
          value={formatNumber(summary.overview.columns)}
          hint={`${summary.overview.numeric_columns.length} numeric, ${summary.overview.categorical_columns.length} categorical`}
        />
        <StatCard
          label="Missing values"
          value={formatNumber(quality.total_missing)}
          hint={`${formatPercent(quality.missing_pct)} of all cells`}
          alert={quality.missing_pct >= 5}
        />
        <StatCard
          label="Duplicate rows"
          value={formatNumber(quality.duplicate_rows)}
          hint={formatPercent(quality.duplicate_pct)}
          alert={quality.duplicate_rows > 0}
        />
      </section>

      <section className="card">
        <div className="card__header">
          <h2>Key insights</h2>
          <p className="card__description">
            Findings derived from the computed statistics. Every number below was calculated from
            your file.
          </p>
        </div>
        <InsightList insights={analysis.insights} />
      </section>

      <QualitySection summary={summary} />
      <NumericSection summary={summary} />

      <section className="stack">
        <div className="row row--between">
          <div>
            <h2>Visualizations</h2>
            <p className="card__description">Charts chosen from the detected column types.</p>
          </div>
          <Link className="button button--secondary" to={`/datasets/${datasetId}/assistant`}>
            Ask the assistant
          </Link>
        </div>
        <div className="grid grid--charts">
          {analysis.visualizations.map((chart) => (
            <ChartCard key={chart.id} chart={chart} />
          ))}
        </div>
      </section>
    </>
  );
}

function QualitySection({ summary }: { summary: Analysis['summary'] }) {
  const quality = summary.data_quality;
  const problemColumns = quality.columns.filter((column) => column.missing_count > 0);

  return (
    <section className="card">
      <div className="card__header">
        <h2>Data quality</h2>
        <p className="card__description">Where the data is incomplete or structurally odd.</p>
      </div>
      {problemColumns.length === 0 ? (
        <p className="muted">No column has missing values.</p>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th scope="col">Column</th>
                <th scope="col">Missing</th>
                <th scope="col">Missing %</th>
                <th scope="col">Unique values</th>
              </tr>
            </thead>
            <tbody>
              {problemColumns.map((column) => (
                <tr key={column.name}>
                  <td>{column.name}</td>
                  <td className="numeric">{formatNumber(column.missing_count)}</td>
                  <td className="numeric">{formatPercent(column.missing_pct)}</td>
                  <td className="numeric">{formatNumber(column.unique_count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="stack" style={{ gap: 8, marginTop: 16 }}>
        {quality.constant_columns.length > 0 ? (
          <p className="muted">
            <strong>Constant columns:</strong> {quality.constant_columns.join(', ')}
          </p>
        ) : null}
        {quality.high_cardinality_columns.length > 0 ? (
          <p className="muted">
            <strong>Identifier-like columns:</strong>{' '}
            {quality.high_cardinality_columns.map((column) => column.name).join(', ')}
          </p>
        ) : null}
        {quality.suspicious_types.length > 0 ? (
          <p className="muted">
            <strong>Types worth checking:</strong>{' '}
            {quality.suspicious_types
              .map((item) => `${item.name} to ${item.suggested_type}`)
              .join(', ')}
          </p>
        ) : null}
      </div>
    </section>
  );
}

function NumericSection({ summary }: { summary: Analysis['summary'] }) {
  const entries = Object.entries(summary.numeric_statistics);
  if (entries.length === 0) return null;

  return (
    <section className="card">
      <div className="card__header">
        <h2>Numeric statistics</h2>
        <p className="card__description">Computed with pandas over the non-missing values.</p>
      </div>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th scope="col">Column</th>
              <th scope="col">Count</th>
              <th scope="col">Mean</th>
              <th scope="col">Median</th>
              <th scope="col">Std dev</th>
              <th scope="col">Min</th>
              <th scope="col">Q1</th>
              <th scope="col">Q3</th>
              <th scope="col">Max</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([name, stats]) => (
              <tr key={name}>
                <td>{name}</td>
                <td className="numeric">{formatNumber(stats.count)}</td>
                <td className="numeric">{formatNumber(stats.mean)}</td>
                <td className="numeric">{formatNumber(stats.median)}</td>
                <td className="numeric">{formatNumber(stats.std)}</td>
                <td className="numeric">{formatNumber(stats.min)}</td>
                <td className="numeric">{formatNumber(stats.q1)}</td>
                <td className="numeric">{formatNumber(stats.q3)}</td>
                <td className="numeric">{formatNumber(stats.max)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
