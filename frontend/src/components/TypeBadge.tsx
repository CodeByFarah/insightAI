import type { ColumnProfile } from '../types';

export function TypeBadge({ type }: { type: ColumnProfile['inferred_type'] }) {
  return <span className={`badge badge--${type}`}>{type}</span>;
}
