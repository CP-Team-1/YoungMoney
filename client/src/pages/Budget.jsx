import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import BudgetJar from '../components/BudgetJar'
import ProgressBar from '../components/ProgressBar'
import LoadingState from '../components/LoadingState'
import { getBudget } from '../services/budget'
import './Budget.css'

export default function Budget() {
  const [budget, setBudget] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getBudget().then(setBudget).finally(() => setLoading(false))
  }, [])

  if (loading) return <AppShell><LoadingState /></AppShell>

  const totalAllocated = budget.categories.reduce((s, c) => s + c.allocated, 0)
  const totalSpent = budget.categories.reduce((s, c) => s + c.spent, 0)
  const unallocated = budget.income - totalAllocated

  return (
    <AppShell>
      <div className="budget-page">
        <header className="budget-page__header">
          <h1 className="budget-page__title">Budget</h1>
          <div className="budget-page__income">
            <span className="budget-page__income-label">Monthly income</span>
            <span className="budget-page__income-val">${budget.income.toLocaleString()}</span>
          </div>
        </header>

        <div className="budget-summary">
          <div className="budget-summary__item">
            <span className="budget-summary__val">${totalAllocated.toLocaleString()}</span>
            <span className="budget-summary__label">Allocated</span>
          </div>
          <div className="budget-summary__item">
            <span className="budget-summary__val budget-summary__val--spent">${totalSpent.toLocaleString()}</span>
            <span className="budget-summary__label">Spent</span>
          </div>
          <div className="budget-summary__item">
            <span className={`budget-summary__val${unallocated < 0 ? ' budget-summary__val--over' : ' budget-summary__val--free'}`}>
              ${Math.abs(unallocated).toLocaleString()}
            </span>
            <span className="budget-summary__label">{unallocated < 0 ? 'Over-allocated' : 'Unallocated'}</span>
          </div>
        </div>

        <div className="budget-page__bar">
          <ProgressBar value={totalSpent} max={budget.income} color="orange" label="Spent vs income" showPercent />
        </div>

        <section className="budget-jars-section">
          <h2 className="budget-jars-title">Categories</h2>
          <div className="budget-jars">
            {budget.categories.map((cat) => (
              <BudgetJar key={cat.id} category={cat} />
            ))}
          </div>
        </section>

        <section className="budget-table-section">
          <h2 className="budget-table-title">Breakdown</h2>
          <div className="budget-table">
            {budget.categories.map((cat) => {
              const pct = cat.allocated > 0 ? Math.round((cat.spent / cat.allocated) * 100) : 0
              return (
                <div key={cat.id} className="budget-row">
                  <div className="budget-row__left">
                    <span className="budget-row__dot" style={{ background: cat.color }} />
                    <span className="budget-row__label">{cat.label}</span>
                  </div>
                  <div className="budget-row__right">
                    <span className="budget-row__spent">${cat.spent}</span>
                    <span className="budget-row__alloc"> / ${cat.allocated}</span>
                    <span className={`budget-row__pct${pct > 100 ? ' budget-row__pct--over' : ''}`}>{pct}%</span>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      </div>
    </AppShell>
  )
}
