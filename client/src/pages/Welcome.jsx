import { Link } from 'react-router-dom'
import './Welcome.css'

export default function Welcome() {
  return (
    <div className="welcome">
      <div className="welcome__content">
        <div className="welcome__logo-mark">Y</div>
        <h1 className="welcome__title serif">YoungMoney</h1>
        <p className="welcome__tagline">
          Get smart about money. One lesson, one decision at a time.
        </p>
        <div className="welcome__actions">
          <Link to="/register" className="welcome__btn welcome__btn--primary">
            Get started — it's free
          </Link>
          <Link to="/login" className="welcome__btn welcome__btn--ghost">
            Sign in
          </Link>
        </div>
        <div className="welcome__features">
          <div className="welcome__feature">
            <span className="welcome__feature-icon">◉</span>
            <p>Financial lessons built for beginners</p>
          </div>
          <div className="welcome__feature">
            <span className="welcome__feature-icon">▣</span>
            <p>Credit card reward optimizer</p>
          </div>
          <div className="welcome__feature">
            <span className="welcome__feature-icon">◫</span>
            <p>Budget tools that actually make sense</p>
          </div>
        </div>
      </div>
    </div>
  )
}
