export interface Dataset {
  id: number;
  filename: string;
  file_size_bytes: number;
  row_count: number;
  column_count: number;
  uploaded_at: string;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  inferred_type: 'numeric' | 'categorical' | 'datetime' | 'boolean';
  non_null_count: number;
  missing_count: number;
  missing_pct: number;
  unique_count: number;
}

export interface DatasetPreview {
  dataset_id: number;
  filename: string;
  row_count: number;
  column_count: number;
  columns: ColumnProfile[];
  rows: Record<string, string>[];
  total_missing: number;
  duplicate_rows: number;
}

export interface Insight {
  id: number;
  title: string;
  description: string;
  category: string;
  severity: 'critical' | 'warning' | 'info';
  metric: string;
  column_name: string | null;
}

export type ChartType = 'histogram' | 'bar' | 'box' | 'scatter' | 'heatmap' | 'timeseries';

export interface Visualization {
  id: string;
  type: ChartType;
  title: string;
  description: string;
  x_label?: string | null;
  y_label?: string | null;
  column?: string | null;
  data: Record<string, unknown>[];
  meta?: Record<string, unknown> | null;
}

export interface NumericStats {
  count: number;
  mean: number | null;
  median: number | null;
  std: number | null;
  min: number | null;
  max: number | null;
  q1: number | null;
  q3: number | null;
  iqr: number | null;
  skew: number | null;
}

export interface AnalysisSummary {
  overview: {
    rows: number;
    columns: number;
    memory_usage_human: string;
    numeric_columns: string[];
    categorical_columns: string[];
    datetime_columns: string[];
    boolean_columns: string[];
  };
  columns: ColumnProfile[];
  numeric_statistics: Record<string, NumericStats>;
  categorical_analysis: Record<
    string,
    {
      unique_count: number;
      top_values: { value: string; count: number; pct: number }[];
      dominant_value: string | null;
      dominant_pct: number;
    }
  >;
  data_quality: {
    total_missing: number;
    missing_pct: number;
    duplicate_rows: number;
    duplicate_pct: number;
    constant_columns: string[];
    high_cardinality_columns: { name: string; unique_count: number; unique_ratio: number }[];
    suspicious_types: {
      name: string;
      detected_type: string;
      suggested_type: string;
      match_ratio: number;
    }[];
    columns: { name: string; missing_count: number; missing_pct: number; unique_count: number }[];
  };
  correlation: {
    columns: string[];
    matrix: (number | null)[][];
    strong_pairs: {
      column_a: string;
      column_b: string;
      correlation: number;
      direction: 'positive' | 'negative';
    }[];
  };
  outliers: Record<string, { count: number; pct: number }>;
  anomalies?: { applicable: boolean; anomalous_rows: number; anomalous_pct: number };
}

export interface Analysis {
  id: number;
  dataset_id: number;
  created_at: string;
  summary: AnalysisSummary;
  insights: Insight[];
  visualizations: Visualization[];
}

export interface Dashboard {
  dataset_count: number;
  analysis_count: number;
  total_rows: number;
  recent_datasets: Dataset[];
  most_recent_dataset: Dataset | null;
  ai_enabled: boolean;
}

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Conversation {
  dataset_id: number;
  ai_enabled: boolean;
  messages: ChatMessage[];
}

export interface AIStatus {
  enabled: boolean;
  provider: string;
  message: string;
}

export interface ApiErrorBody {
  error: string;
  message: string;
  details?: Record<string, unknown>;
}
