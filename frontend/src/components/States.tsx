import type { ReactNode } from 'react';
import { ApiError } from '../services/api';

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="loading" role="status">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty">
      <p className="empty__title">{title}</p>
      <p>{description}</p>
      {action ? <div style={{ marginTop: 16 }}>{action}</div> : null}
    </div>
  );
}

export function ErrorBanner({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  return (
    <div className="banner banner--error row row--between" role="alert">
      <span>
        <strong>{error.code.replace(/_/g, ' ').toLowerCase()}</strong> — {error.message}
      </span>
      {onRetry ? (
        <button type="button" className="button button--secondary" onClick={onRetry}>
          Retry
        </button>
      ) : null}
    </div>
  );
}

export function Notice({ children }: { children: ReactNode }) {
  return <div className="banner banner--notice">{children}</div>;
}
