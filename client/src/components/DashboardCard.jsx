import './DashboardCard.css'

export default function DashboardCard({ title, children, accent, action, actionLabel }) {
  return (
    <div className={`dash-card${accent ? ` dash-card--${accent}` : ''}`}>
      <div className="dash-card__header">
        <h3 className="dash-card__title">{title}</h3>
        {action && (
          <button type="button" className="dash-card__action" onClick={action}>
            {actionLabel || 'See all'}
          </button>
        )}
      </div>
      <div className="dash-card__body">{children}</div>
    </div>
  )
}
