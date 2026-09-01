import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import ExpenseEntry from '../components/ExpenseEntry'
import LoadingState from '../components/LoadingState'
import EmptyState from '../components/EmptyState'
import { getSpending } from '../services/spending'
import './SpendLog.css'

const ALL = 'all'

export default function SpendLog() {
  const [spending, setSpending] = useState([])
  const [filter, setFilter] = useState(ALL)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getSpending().then(setSpending).finally(() => setLoading(false))
  }, [])

  if (loading) return <AppShell><LoadingState /></AppShell>

  const categories = [ALL, ...new Set(spending.map((s) => s.category))]
  const filtered = filter === ALL ? spending : spending.filter((s) => s.category === filter)
  const total = filtered.reduce((s, e) => s + e.amount, 0)

  return (
    <AppShell>
      <div className="spend-log">
        <header className="spend-log__header">
          <h1 className="spend-log__title">Spend Log</h1>
          <span className="spend-log__total">${total.toFixed(2)}</span>
        </header>

        <div className="spend-log__filters" role="group" aria-label="Filter by category">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              className={`spend-filter${filter === cat ? ' spend-filter--active' : ''}`}
              onClick={() => setFilter(cat)}
            >
              {cat === ALL ? 'All' : cat}
            </button>
          ))}
        </div>

        <div className="spend-log__list">
          {filtered.length === 0 ? (
            <EmptyState title="No transactions" message="Transactions will appear here as you log spending." />
          ) : (
            filtered.map((e) => <ExpenseEntry key={e.id} entry={e} />)
          )}
        </div>
      </div>
    </AppShell>
  )
}
