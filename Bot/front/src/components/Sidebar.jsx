import { NavLink } from 'react-router-dom';

import { useAuth } from '../hooks/useAuth';
import { shortName } from '../utils/format';

const NAV_ITEMS = [
  { to: '/', label: 'Mapa', icon: '🗺️', end: true },
  { to: '/mi-ubicacion', label: 'Mi ubicación', icon: '📍' },
  { to: '/historial', label: 'Historial', icon: '🕘' },
  { to: '/autorizaciones', label: 'Autorizaciones', icon: '🔐' },
];

/** Barra lateral de navegación. */
export default function Sidebar() {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__logo" aria-hidden="true">
          📍
        </span>
        <div>
          <strong>Ubicación Compartida</strong>
          <small>Panel de visualización</small>
        </div>
      </div>

      <nav className="sidebar__nav" aria-label="Navegación principal">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `sidebar__link${isActive ? ' is-active' : ''}`}
          >
            <span aria-hidden="true">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <div className="sidebar__user">
          <span className="sidebar__avatar" aria-hidden="true">
            {shortName(user).charAt(0).toUpperCase()}
          </span>
          <div className="sidebar__user-info">
            <strong>{shortName(user)}</strong>
            <small>{user?.username ? `@${user.username}` : `ID ${user?.telegram_id}`}</small>
          </div>
        </div>
        <button type="button" className="btn btn--ghost btn--block" onClick={logout}>
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
