import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './DesktopSidebar.css'

const NAV = [
  { to: '/dashboard', label: 'Dashboard',    icon: '◈' },
  { to: '/today',     label: 'Today',        icon: '◷' },
  { to: '/budget',    label: 'Budget',       icon: '◫' },
  { to: '/goals',     label: 'Goals',        icon: '◇' },
  { to: '/spend',     label: 'Spend Log',    icon: '◎' },
  { to: '/learn',     label: 'Learn',        icon: '◉' },
  { to: '/cards',     label: 'Cards',        icon: '▣' },
]

export default function DesktopSidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <aside className="sidebar" aria-label="Main navigation">
      <div className="sidebar__logo">
        <span className="sidebar__logo-mark">Y</span>
        <span className="sidebar__logo-text serif">YoungMoney</span>
      </div>

      <nav className="sidebar__nav">
        {NAV.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
          >
            <span className="sidebar__icon" aria-hidden="true">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__foot">
        {user && (
          <p className="sidebar__user">{user.first_name || user.email}</p>
        )}
        <button type="button" className="sidebar__logout" onClick={handleLogout}>
          Sign out
        </button>
      </div>
    </aside>
  )
}
