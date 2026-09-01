import './EmptyState.css'

export default function EmptyState({ title, message, action, actionLabel }) {
  return (
    <div className="empty-state">
      <p className="empty-state__icon">○</p>
      <h3 className="empty-state__title">{title}</h3>
      {message && <p className="empty-state__msg">{message}</p>}
      {action && (
        <button type="button" className="empty-state__btn" onClick={action}>
          {actionLabel || 'Get started'}
        </button>
      )}
    </div>
  )
}
