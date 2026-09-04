import { formatMoney } from '../utils/money'
import './BudgetJar.css'

export default function BudgetJar({ category }) {
  const { label, allocated, spent, color } = category
  const remaining = Math.max(0, allocated - spent)
  const over = spent > allocated
  // Fill represents remaining budget: full = all budget available, empties as you spend
  const remainingPct = allocated > 0 ? Math.round((remaining / allocated) * 100) : 0

  return (
    <div className="budget-jar">
      <div className="budget-jar__bar-wrap">
        <div className="budget-jar__bar-track">
          <div
            className={`budget-jar__bar-fill${over ? ' budget-jar__bar-fill--over' : ''}`}
            style={{ height: `${over ? 0 : remainingPct}%`, background: over ? '#e06060' : color }}
          />
        </div>
      </div>
      <p className="budget-jar__label">{label}</p>
      <p className="budget-jar__amounts">
        <span style={{ color }}>{formatMoney(spent)}</span>
        <span className="budget-jar__slash"> / </span>
        <span className="budget-jar__alloc">{formatMoney(allocated)}</span>
      </p>
      <p className={`budget-jar__remain${over ? ' budget-jar__remain--over' : ''}`}>
        {over ? `${formatMoney(spent - allocated)} over` : `${formatMoney(remaining)} left`}
      </p>
    </div>
  )
}
