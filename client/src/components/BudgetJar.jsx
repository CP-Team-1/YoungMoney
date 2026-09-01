import './BudgetJar.css'

export default function BudgetJar({ category }) {
  const { label, allocated, spent, color } = category
  const pct = allocated > 0 ? Math.min(100, Math.round((spent / allocated) * 100)) : 0
  const remaining = Math.max(0, allocated - spent)
  const over = spent > allocated

  return (
    <div className="budget-jar">
      <div className="budget-jar__bar-wrap">
        <div className="budget-jar__bar-track">
          <div
            className={`budget-jar__bar-fill${over ? ' budget-jar__bar-fill--over' : ''}`}
            style={{ height: `${pct}%`, background: over ? '#e06060' : color }}
          />
        </div>
      </div>
      <p className="budget-jar__label">{label}</p>
      <p className="budget-jar__amounts">
        <span style={{ color }}>${spent}</span>
        <span className="budget-jar__slash"> / </span>
        <span className="budget-jar__alloc">${allocated}</span>
      </p>
      <p className={`budget-jar__remain${over ? ' budget-jar__remain--over' : ''}`}>
        {over ? `$${spent - allocated} over` : `$${remaining} left`}
      </p>
    </div>
  )
}
