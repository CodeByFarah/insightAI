import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { AnalysisPage } from './pages/AnalysisPage';
import { AssistantPage } from './pages/AssistantPage';
import { DashboardPage } from './pages/DashboardPage';
import { DatasetPreviewPage } from './pages/DatasetPreviewPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { SelectDatasetPage } from './pages/SelectDatasetPage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="datasets" element={<DatasetsPage />} />
        <Route path="datasets/:datasetId" element={<DatasetPreviewPage />} />
        <Route path="datasets/:datasetId/analysis" element={<AnalysisPage />} />
        <Route path="datasets/:datasetId/assistant" element={<AssistantPage />} />
        <Route
          path="analysis"
          element={
            <SelectDatasetPage
              title="Analysis"
              subtitle="Choose a dataset to analyze."
              target={(id) => `/datasets/${id}/analysis`}
            />
          }
        />
        <Route
          path="assistant"
          element={
            <SelectDatasetPage
              title="AI Assistant"
              subtitle="Choose the dataset you want to ask about."
              target={(id) => `/datasets/${id}/assistant`}
            />
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
