import './ProgressBar.css'

export default function ProgressBar({ value, max = 100, color = 'orange', label, showPercent = false }) {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0
  return (
    <div className="progress-bar">
      {(label || showPercent) && (
        <div className="progress-bar__header">
          {label && <span className="progress-bar__label">{label}</span>}
          {showPercent && <span className="progress-bar__pct">{pct}%</span>}
        </div>
      )}
      <div className="progress-bar__track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div
          className={`progress-bar__fill progress-bar__fill--${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
