import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { UploadDropzone } from '../components/UploadDropzone';
import { EmptyState, ErrorBanner, Loading } from '../components/States';
import { useAsync } from '../hooks/useAsync';
import { api } from '../services/api';
import type { Dataset } from '../types';
import { formatBytes, formatDate, formatNumber } from '../utils/format';

export function DatasetsPage() {
  const { data, loading, error, reload } = useAsync<Dataset[]>(() => api.listDatasets(), []);
  const [deleting, setDeleting] = useState<number | null>(null);

  async function remove(dataset: Dataset) {
    if (!window.confirm(`Delete ${dataset.filename}? Its analyses are deleted too.`)) return;
    setDeleting(dataset.id);
    try {
      await api.deleteDataset(dataset.id);
      reload();
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="stack">
      <PageHeader title="Datasets" subtitle="Every CSV you have uploaded." />

      <section className="card">
        <div className="card__header">
          <h2>Upload</h2>
        </div>
        <UploadDropzone onUploaded={reload} />
      </section>

      {loading ? <Loading /> : null}
      {error ? <ErrorBanner error={error} onRetry={reload} /> : null}

      {data && data.length === 0 ? (
        <EmptyState
          title="No datasets yet"
          description="Upload a CSV above. The repository ships sample files in data/sample."
        />
      ) : null}

      {data && data.length > 0 ? (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th scope="col">File</th>
                <th scope="col">Rows</th>
                <th scope="col">Columns</th>
                <th scope="col">Size</th>
                <th scope="col">Uploaded</th>
                <th scope="col" aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {data.map((dataset) => (
                <tr key={dataset.id}>
                  <td>
                    <Link to={`/datasets/${dataset.id}`}>{dataset.filename}</Link>
                  </td>
                  <td className="numeric">{formatNumber(dataset.row_count)}</td>
                  <td className="numeric">{formatNumber(dataset.column_count)}</td>
                  <td className="numeric muted">{formatBytes(dataset.file_size_bytes)}</td>
                  <td className="muted">{formatDate(dataset.uploaded_at)}</td>
                  <td>
                    <button
                      type="button"
                      className="button button--danger"
                      onClick={() => void remove(dataset)}
                      disabled={deleting === dataset.id}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
