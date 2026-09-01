import './GoalMeter.css'

export default function GoalMeter({ label, current, target, unit = '$' }) {
  const pct = target > 0 ? Math.min(100, Math.round((current / target) * 100)) : 0
  const radius = 54
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (pct / 100) * circumference

  return (
    <div className="goal-meter">
      <div className="goal-meter__ring" aria-label={`${label}: ${pct}%`}>
        <svg viewBox="0 0 120 120" width="120" height="120">
          <circle cx="60" cy="60" r={radius} className="goal-meter__track" />
          <circle
            cx="60" cy="60" r={radius}
            className="goal-meter__fill"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 60 60)"
          />
        </svg>
        <div className="goal-meter__center">
          <span className="goal-meter__pct">{pct}%</span>
        </div>
      </div>
      <div className="goal-meter__info">
        <p className="goal-meter__label">{label}</p>
        <p className="goal-meter__values">
          <span className="goal-meter__current">{unit}{current.toLocaleString()}</span>
          <span className="goal-meter__divider"> / </span>
          <span className="goal-meter__target">{unit}{target.toLocaleString()}</span>
        </p>
      </div>
    </div>
  )
}
