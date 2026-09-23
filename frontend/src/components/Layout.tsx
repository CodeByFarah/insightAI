import { NavLink, Outlet } from 'react-router-dom';

const LINKS = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/datasets', label: 'Datasets', end: false },
  { to: '/analysis', label: 'Analysis', end: false },
  { to: '/assistant', label: 'AI Assistant', end: false },
];

export function Layout() {
  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand__name">InsightAI</span>
          <span className="brand__tagline">Data → Analysis → Insight</span>
        </div>
        <nav className="nav" aria-label="Main">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? 'nav__link nav__link--active' : 'nav__link')}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <p className="sidebar__footer">
          Statistics are computed in Python. The assistant explains them; it never invents them.
        </p>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
