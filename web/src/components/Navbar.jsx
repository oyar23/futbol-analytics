import { NavLink } from 'react-router-dom'
import Emblem from './Emblem.jsx'

const links = [
  { to: '/', label: 'Inicio', end: true },
  { to: '/kpis', label: 'KPIs' },
  { to: '/tiros', label: 'Mapa de tiros' },
  { to: '/scouting', label: 'Scouting' },
  { to: '/fisico-xg', label: 'Físico & xG' },
]

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="brand">
          <Emblem size={40} />
          <span className="brand-text">
            <div className="brand-title">Qatar 2022 · Análisis</div>
            <div className="brand-sub">Fútbol Analytics</div>
          </span>
        </NavLink>

        <nav className="nav-links">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
            >
              {l.label}
            </NavLink>
          ))}
        </nav>

        <div className="nav-author">
          <div className="name">Lautaro Oyarzun</div>
          <div className="role">Analista de Datos / BI</div>
        </div>
      </div>
    </header>
  )
}
