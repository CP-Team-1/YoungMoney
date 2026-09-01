import { useLocation, useNavigate, useParams, Link } from 'react-router-dom'
import AppShell from '../components/AppShell'
import './QuizResult.css'

export default function QuizResult() {
  const { lessonId } = useParams()
  const { state } = useLocation()
  const navigate = useNavigate()

  const score = state?.score ?? 0
  const correct = state?.correct ?? 0
  const total = state?.total ?? 0

  const passed = score >= 70
  const grade = score >= 90 ? 'Excellent' : score >= 70 ? 'Good job' : 'Keep learning'

  return (
    <AppShell>
      <div className="result-page">
        <div className="result-card">
          <div className={`result-badge${passed ? ' result-badge--pass' : ' result-badge--retry'}`}>
            {passed ? '✓' : '↺'}
          </div>

          <h1 className="result-title">{grade}</h1>
          <p className="result-sub">
            You got <strong>{correct} out of {total}</strong> questions right.
          </p>

          <div className="result-score">
            <span className="result-score__num">{score}</span>
            <span className="result-score__denom">/ 100</span>
          </div>

          {!passed && (
            <p className="result-hint">
              Review the lesson and try again — you need 70% to pass.
            </p>
          )}

          <div className="result-actions">
            {!passed && (
              <Link to={`/learn/${lessonId}`} className="result-btn result-btn--retry">
                Review lesson
              </Link>
            )}
            <button type="button" className="result-btn result-btn--primary" onClick={() => navigate('/learn')}>
              {passed ? 'Next lesson →' : 'All lessons'}
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
