import { useNavigate, useParams } from 'react-router-dom';
import { DataTable } from '../components/DataTable';
import { DatasetTabs } from '../components/DatasetTabs';
import { PageHeader } from '../components/PageHeader';
import { StatCard } from '../components/StatCard';
import { ErrorBanner, Loading } from '../components/States';
import { TypeBadge } from '../components/TypeBadge';
import { useAsync } from '../hooks/useAsync';
import { api } from '../services/api';
import type { DatasetPreview } from '../types';
import { formatNumber, formatPercent } from '../utils/format';

export function DatasetPreviewPage() {
  const { datasetId } = useParams();
  const id = Number(datasetId);
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync<DatasetPreview>(
    () => api.previewDataset(id, 20),
    [id],
  );

  if (loading) return <Loading label="Reading the file…" />;
  if (error) return <ErrorBanner error={error} onRetry={reload} />;
  if (!data) return null;

  return (
    <div className="stack">
      <PageHeader
        title={data.filename}
        subtitle="Check the data before running a full analysis."
        actions={
          <button
            type="button"
            className="button"
            onClick={() => navigate(`/datasets/${id}/analysis`)}
          >
            Run analysis
          </button>
        }
      />
      <DatasetTabs datasetId={id} />

      <section className="grid grid--stats">
        <StatCard label="Rows" value={formatNumber(data.row_count)} />
        <StatCard label="Columns" value={formatNumber(data.column_count)} />
        <StatCard
          label="Missing values"
          value={formatNumber(data.total_missing)}
          alert={data.total_missing > 0}
        />
        <StatCard
          label="Duplicate rows"
          value={formatNumber(data.duplicate_rows)}
          alert={data.duplicate_rows > 0}
        />
      </section>

      <section className="card">
        <div className="card__header">
          <h2>Columns</h2>
          <p className="card__description">Detected types and completeness for each column.</p>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th scope="col">Column</th>
                <th scope="col">Detected type</th>
                <th scope="col">Pandas dtype</th>
                <th scope="col">Missing</th>
                <th scope="col">Unique</th>
              </tr>
            </thead>
            <tbody>
              {data.columns.map((column) => (
                <tr key={column.name}>
                  <td>{column.name}</td>
                  <td>
                    <TypeBadge type={column.inferred_type} />
                  </td>
                  <td className="mono muted">{column.dtype}</td>
                  <td className="numeric">
                    {formatNumber(column.missing_count)}{' '}
                    <span className="muted">({formatPercent(column.missing_pct)})</span>
                  </td>
                  <td className="numeric">{formatNumber(column.unique_count)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card">
        <div className="card__header">
          <h2>First {data.rows.length} rows</h2>
          <p className="card__description">Values are shown exactly as they were parsed.</p>
        </div>
        <DataTable columns={data.columns.map((column) => column.name)} rows={data.rows} />
      </section>
    </div>
  );
}
