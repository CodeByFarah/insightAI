import type {
  AIStatus,
  Analysis,
  ChatMessage,
  Conversation,
  Dashboard,
  Dataset,
  DatasetPreview,
  Insight,
  Visualization,
} from '../types';

const BASE_URL = '/api';

/** An error carrying the backend's structured code and safe message. */
export class ApiError extends Error {
  readonly code: string;
  readonly status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, init);
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', 'Could not reach the server. Is the backend running?');
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      body?.error ?? 'HTTP_ERROR',
      body?.message ?? 'Something went wrong. Please try again.',
    );
  }
  return body as T;
}

export const api = {
  dashboard: () => request<Dashboard>('/dashboard'),
  aiStatus: () => request<AIStatus>('/ai/status'),

  listDatasets: () => request<Dataset[]>('/datasets'),
  getDataset: (id: number) => request<Dataset>(`/datasets/${id}`),
  deleteDataset: (id: number) => request<void>(`/datasets/${id}`, { method: 'DELETE' }),
  previewDataset: (id: number, rows = 20) =>
    request<DatasetPreview>(`/datasets/${id}/preview?rows=${rows}`),

  uploadDataset: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<Dataset>('/datasets', { method: 'POST', body: form });
  },

  runAnalysis: (id: number, force = false) =>
    request<Analysis>(`/datasets/${id}/analyze?force=${force}`, { method: 'POST' }),
  getAnalysis: (id: number) => request<Analysis>(`/datasets/${id}/analysis`),
  getInsights: (id: number) => request<Insight[]>(`/datasets/${id}/insights`),
  getVisualizations: (id: number) => request<Visualization[]>(`/datasets/${id}/visualizations`),

  getConversation: (id: number) => request<Conversation>(`/datasets/${id}/ai/messages`),
  askQuestion: (id: number, question: string) =>
    request<{ dataset_id: number; answer: ChatMessage }>(`/datasets/${id}/ai/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    }),
};
