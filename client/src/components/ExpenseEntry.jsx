import './ExpenseEntry.css'

const CATEGORY_COLORS = {
  food: '#7fa882',
  transport: '#c9a96e',
  utilities: '#8fa8c8',
  subscriptions: '#b8829a',
  fun: '#e8834a',
  housing: '#e8834a',
  other: '#9a8f82',
}

export default function ExpenseEntry({ entry }) {
  const { merchant, category, amount, date } = entry
  const color = CATEGORY_COLORS[category] ?? '#9a8f82'
  const displayDate = new Date(date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })

  return (
    <div className="expense-entry">
      <div className="expense-entry__dot" style={{ background: color }} />
      <div className="expense-entry__info">
        <p className="expense-entry__merchant">{merchant}</p>
        <p className="expense-entry__category">{category}</p>
      </div>
      <div className="expense-entry__right">
        <p className="expense-entry__amount">-${amount.toFixed(2)}</p>
        <p className="expense-entry__date">{displayDate}</p>
      </div>
    </div>
  )
}
