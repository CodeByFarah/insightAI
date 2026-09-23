import { Link } from 'react-router-dom';
import { PageHeader } from '../components/PageHeader';
import { EmptyState, ErrorBanner, Loading } from '../components/States';
import { useAsync } from '../hooks/useAsync';
import { api } from '../services/api';
import type { Dataset } from '../types';
import { formatDate, formatNumber } from '../utils/format';

interface Props {
  title: string;
  subtitle: string;
  /** Where to send the user once they pick a dataset. */
  target: (datasetId: number) => string;
}

/** The Analysis and AI Assistant tabs need a dataset before they mean anything. */
export function SelectDatasetPage({ title, subtitle, target }: Props) {
  const { data, loading, error, reload } = useAsync<Dataset[]>(() => api.listDatasets(), []);

  if (loading) return <Loading />;
  if (error) return <ErrorBanner error={error} onRetry={reload} />;

  return (
    <div className="stack">
      <PageHeader title={title} subtitle={subtitle} />
      {data && data.length === 0 ? (
        <EmptyState
          title="No datasets yet"
          description="Upload a CSV first — analysis and the assistant both work from an uploaded dataset."
          action={
            <Link className="button" to="/datasets">
              Upload a dataset
            </Link>
          }
        />
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th scope="col">Dataset</th>
                <th scope="col">Rows</th>
                <th scope="col">Columns</th>
                <th scope="col">Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((dataset) => (
                <tr key={dataset.id}>
                  <td>
                    <Link to={target(dataset.id)}>{dataset.filename}</Link>
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
    </div>
  );
}
