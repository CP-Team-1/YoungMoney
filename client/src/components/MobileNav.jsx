import { NavLink } from 'react-router-dom'
import './MobileNav.css'

const NAV = [
  { to: '/dashboard', label: 'Home',  icon: '◈' },
  { to: '/budget',    label: 'Budget', icon: '◫' },
  { to: '/spend',     label: 'Spend',  icon: '◎' },
  { to: '/learn',     label: 'Learn',  icon: '◉' },
  { to: '/cards',     label: 'Cards',  icon: '▣' },
]

export default function MobileNav() {
  return (
    <nav className="mobile-nav" aria-label="Main navigation">
      {NAV.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => `mobile-nav__item${isActive ? ' mobile-nav__item--active' : ''}`}
        >
          <span className="mobile-nav__icon" aria-hidden="true">{icon}</span>
          <span className="mobile-nav__label">{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
