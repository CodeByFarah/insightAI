import { Link, useNavigate } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { StatCard } from '../components/StatCard';
import { UploadDropzone } from '../components/UploadDropzone';
import { EmptyState, ErrorBanner, Loading } from '../components/States';
import { useAsync } from '../hooks/useAsync';
import { api } from '../services/api';
import type { Dashboard } from '../types';
import { formatDate, formatNumber } from '../utils/format';

export function DashboardPage() {
  const navigate = useNavigate();
  const { data, loading, error, reload } = useAsync<Dashboard>(() => api.dashboard(), []);

  if (loading) return <Loading label="Loading dashboard…" />;
  if (error) return <ErrorBanner error={error} onRetry={reload} />;
  if (!data) return null;

  return (
    <div className="stack">
      <PageHeader
        title="Dashboard"
        subtitle="Upload a CSV, analyze it in Python, and explore what the numbers show."
      />

      <section className="grid grid--stats">
        <StatCard label="Datasets" value={formatNumber(data.dataset_count)} />
        <StatCard label="Analyses run" value={formatNumber(data.analysis_count)} />
        <StatCard label="Rows stored" value={formatNumber(data.total_rows)} />
        <StatCard
          label="AI assistant"
          value={data.ai_enabled ? 'Enabled' : 'Disabled'}
          hint={data.ai_enabled ? 'Gemini is configured.' : 'Set GEMINI_API_KEY to enable it.'}
        />
      </section>

      <section className="card">
        <div className="card__header">
          <h2>Upload a dataset</h2>
          <p className="card__description">CSV files only. Analysis runs on demand.</p>
        </div>
        <UploadDropzone onUploaded={(dataset) => navigate(`/datasets/${dataset.id}`)} />
      </section>

      <section className="card">
        <div className="card__header row row--between">
          <div>
            <h2>Recent activity</h2>
            <p className="card__description">Your most recently uploaded datasets.</p>
          </div>
          <Link className="button button--secondary" to="/datasets">
            All datasets
          </Link>
        </div>
        {data.recent_datasets.length === 0 ? (
          <EmptyState
            title="Nothing uploaded yet"
            description="Upload a CSV above to see it here. Sample files live in data/sample."
          />
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th scope="col">File</th>
                  <th scope="col">Rows</th>
                  <th scope="col">Columns</th>
                  <th scope="col">Uploaded</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_datasets.map((dataset) => (
                  <tr key={dataset.id}>
                    <td>
                      <Link to={`/datasets/${dataset.id}`}>{dataset.filename}</Link>
                    </td>
                    <td className="numeric">{formatNumber(dataset.row_count)}</td>
                    <td className="numeric">{formatNumber(dataset.column_count)}</td>
                    <td className="muted">{formatDate(dataset.uploaded_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
