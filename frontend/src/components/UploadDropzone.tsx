import { useRef, useState } from 'react';
import type { DragEvent } from 'react';
import { api, ApiError } from '../services/api';
import type { Dataset } from '../types';
import { formatBytes } from '../utils/format';

const MAX_BYTES = 20 * 1024 * 1024;

interface Props {
  onUploaded: (dataset: Dataset) => void;
}

export function UploadDropzone({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selected, setSelected] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  /** Client-side checks mirror the server's; the server remains authoritative. */
  function validate(file: File): string | null {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      return 'Only CSV files are accepted. Choose a file ending in .csv.';
    }
    if (file.size > MAX_BYTES) {
      return `That file is ${formatBytes(file.size)}. The limit is ${formatBytes(MAX_BYTES)}.`;
    }
    if (file.size === 0) {
      return 'That file is empty.';
    }
    return null;
  }

  async function upload(file: File) {
    setSelected(file);
    const problem = validate(file);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setUploading(true);
    try {
      onUploaded(await api.uploadDataset(file));
      setSelected(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'The upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  }

  function onDrop(event: DragEvent<HTMLElement>) {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files?.[0];
    if (file) void upload(file);
  }

  return (
    <div>
      <label
        className={dragging ? 'dropzone dropzone--active' : 'dropzone'}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void upload(file);
            event.target.value = '';
          }}
        />
        <p className="dropzone__title">
          {uploading ? 'Uploading…' : 'Drop a CSV file here, or click to browse'}
        </p>
        <p className="dropzone__hint">
          CSV only, up to {formatBytes(MAX_BYTES)}. The file is parsed on upload, so a broken file
          is rejected straight away.
        </p>
        {selected ? (
          <p className="dropzone__hint mono">
            {selected.name} · {formatBytes(selected.size)}
          </p>
        ) : null}
        {uploading ? (
          <div className="progress">
            <div className="progress__bar" style={{ width: '70%' }} />
          </div>
        ) : null}
      </label>
      {error ? (
        <div className="banner banner--error" role="alert" style={{ marginTop: 12 }}>
          {error}
        </div>
      ) : null}
    </div>
  );
}
