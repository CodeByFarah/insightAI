interface Props {
  label: string;
  value: string | number;
  hint?: string;
  alert?: boolean;
}

export function StatCard({ label, value, hint, alert = false }: Props) {
  return (
    <div className={alert ? 'stat stat--alert' : 'stat'}>
      <p className="stat__label">{label}</p>
      <p className="stat__value">{value}</p>
      {hint ? <p className="stat__hint">{hint}</p> : null}
    </div>
  );
}
