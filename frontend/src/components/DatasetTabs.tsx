import { NavLink } from 'react-router-dom';

/** The product flow: preview the data, analyze it, then ask about it. */
export function DatasetTabs({ datasetId }: { datasetId: number }) {
  const steps = [
    { to: `/datasets/${datasetId}`, label: 'Preview', end: true },
    { to: `/datasets/${datasetId}/analysis`, label: 'Analysis', end: false },
    { to: `/datasets/${datasetId}/assistant`, label: 'AI Assistant', end: false },
  ];
  return (
    <nav className="flow" aria-label="Dataset steps">
      {steps.map((step, index) => (
        <span key={step.to} className="row" style={{ gap: 8 }}>
          {index > 0 ? <span aria-hidden="true">→</span> : null}
          <NavLink
            to={step.to}
            end={step.end}
            className={({ isActive }) => (isActive ? 'flow__step flow__step--active' : 'flow__step')}
          >
            {step.label}
          </NavLink>
        </span>
      ))}
    </nav>
  );
}
