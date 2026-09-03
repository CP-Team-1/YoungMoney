import './LoadingState.css'

export default function LoadingState({ message = 'Loading…' }) {
  return (
    <div className="loading-state" aria-live="polite">
      <div className="loading-state__spinner" aria-hidden="true" />
      <p className="loading-state__msg">{message}</p>
    </div>
  )
}
