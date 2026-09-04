import { formatMoney } from '../utils/money'
import './ExpenseEntry.css'

const CATEGORY_COLORS = {
  food: '#7fa882',
  transport: '#c9a96e',
  utilities: '#8fa8c8',
  subscriptions: '#b8829a',
  fun: '#e8834a',
  housing: '#e8834a',
  savings: '#7fa882',
  other: '#9a8f82',
}

// color prop is optional — when provided (from budget category user choice) it overrides the default map
export default function ExpenseEntry({ entry, onEdit, onDelete, color: colorProp }) {
  const { merchant, category, amount, date } = entry
  const color = colorProp ?? CATEGORY_COLORS[category] ?? '#9a8f82'
  const displayDate = new Date(date + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })

  return (
    <div className="expense-entry">
      <div className="expense-entry__dot" style={{ background: color }} />
      <div className="expense-entry__info">
        <p className="expense-entry__merchant">{merchant}</p>
        <p className="expense-entry__category">{category}</p>
      </div>
      <div className="expense-entry__right">
        <p className="expense-entry__amount">-{formatMoney(amount)}</p>
        <p className="expense-entry__date">{displayDate}</p>
      </div>
      {(onEdit || onDelete) && (
        <div className="expense-entry__actions">
          {onEdit && (
            <button
              type="button"
              className="expense-entry__action-btn"
              onClick={() => onEdit(entry)}
              aria-label={`Edit ${merchant}`}
            >
              ✎
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              className="expense-entry__action-btn expense-entry__action-btn--del"
              onClick={() => onDelete(entry.id)}
              aria-label={`Delete ${merchant}`}
            >
              ×
            </button>
          )}
        </div>
      )}
    </div>
  )
}
