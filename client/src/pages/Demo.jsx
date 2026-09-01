// ============================================================
// DEVELOPMENT / DEMO ONLY — remove before production deployment
// This file and its import in App.jsx should be deleted before
// shipping to staging or production.
// ============================================================

import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import './Demo.css'

const PAGES = [
  {
    group: 'Public / Auth',
    items: [
      { label: 'Welcome',          path: '/',               note: 'Landing page' },
      { label: 'Register',         path: '/register',       note: 'Sign-up form (bypassed in demo)' },
      { label: 'Sign In',          path: '/login',          note: 'Login form (bypassed in demo)' },
    ],
  },
  {
    group: 'Onboarding',
    items: [
      { label: 'Goal Selection',   path: '/onboarding/goals',  note: 'Step 1 of 2' },
      { label: 'Income Setup',     path: '/onboarding/income', note: 'Step 2 of 2' },
    ],
  },
  {
    group: 'Core App (auth-protected)',
    items: [
      { label: 'Dashboard',        path: '/dashboard',      note: 'Overview with mock budget + spending' },
      { label: 'Today',            path: '/today',          note: 'Daily tip + checklist' },
      { label: 'Budget',           path: '/budget',         note: 'Category jars + breakdown table' },
      { label: 'Spend Log',        path: '/spend',          note: 'Filterable transaction list' },
      { label: 'Learning Hub',     path: '/learn',          note: '6 mock lessons, filter by topic' },
      { label: 'Cards',            path: '/cards',          note: 'Credit card browser + filter' },
    ],
  },
  {
    group: 'Lesson Flow (uses "Investing 101" lesson)',
    items: [
      { label: 'Lesson — read',    path: '/learn/investing-intro',       note: 'Step-through lesson content' },
      { label: 'Quiz',             path: '/learn/investing-intro/quiz',   note: 'Interactive quiz with reveal' },
      {
        label: 'Quiz Result — Pass',
        path: '/learn/investing-intro/result',
        state: { score: 100, correct: 3, total: 3 },
        note: 'Score 100%',
      },
      {
        label: 'Quiz Result — Fail',
        path: '/learn/investing-intro/result',
        state: { score: 33, correct: 1, total: 3 },
        note: 'Score 33% (below 70% pass threshold)',
      },
    ],
  },
]

export default function Demo() {
  const navigate = useNavigate()

  // Activate demo mode so PrivateRoute passes authenticated pages through
  useEffect(() => {
    sessionStorage.setItem('ym_demo', '1')
  }, [])

  function exitDemo() {
    sessionStorage.removeItem('ym_demo')
    navigate('/')
  }

  return (
    <div className="demo-page">
      <header className="demo-header">
        <div className="demo-header__left">
          <span className="demo-badge">DEV ONLY</span>
          <h1 className="demo-title">Page Preview</h1>
          <p className="demo-sub">
            Auth is bypassed via a mock user. All data is mock. This route only exists in
            Vite dev mode (<code>import.meta.env.DEV</code>).
          </p>
        </div>
        <button type="button" className="demo-exit" onClick={exitDemo}>
          Exit demo
        </button>
      </header>

      <div className="demo-groups">
        {PAGES.map((group) => (
          <section key={group.group} className="demo-group">
            <h2 className="demo-group__title">{group.group}</h2>
            <div className="demo-group__items">
              {group.items.map((item) =>
                item.state ? (
                  <button
                    key={item.label}
                    type="button"
                    className="demo-item"
                    onClick={() => navigate(item.path, { state: item.state })}
                  >
                    <span className="demo-item__label">{item.label}</span>
                    <span className="demo-item__note">{item.note}</span>
                    <span className="demo-item__path">{item.path}</span>
                  </button>
                ) : (
                  <Link key={item.label + item.path} to={item.path} className="demo-item">
                    <span className="demo-item__label">{item.label}</span>
                    <span className="demo-item__note">{item.note}</span>
                    <span className="demo-item__path">{item.path}</span>
                  </Link>
                )
              )}
            </div>
          </section>
        ))}
      </div>

      <footer className="demo-footer">
        <p>
          Demo mode is stored in <code>sessionStorage</code> as <code>ym_demo=1</code>.
          Closing the tab clears it automatically.
          To clear manually, click <strong>Exit demo</strong> above.
        </p>
      </footer>
    </div>
  )
}
