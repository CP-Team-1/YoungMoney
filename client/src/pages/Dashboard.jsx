import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/AppShell'
import DashboardCard from '../components/DashboardCard'
import GoalMeter from '../components/GoalMeter'
import ProgressBar from '../components/ProgressBar'
import ExpenseEntry from '../components/ExpenseEntry'
import LoadingState from '../components/LoadingState'
import { useAuth } from '../context/AuthContext'
import { getBudget } from '../services/budget'
import { getSpending } from '../services/spending'
import { getLessons } from '../services/learning'
import './Dashboard.css'

export default function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [budget, setBudget] = useState(null)
  const [spending, setSpending] = useState([])
  const [lessons, setLessons] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getBudget(), getSpending(), getLessons()])
      .then(([b, s, l]) => {
        setBudget(b)
        setSpending(s)
        setLessons(l)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <AppShell><LoadingState /></AppShell>

  const totalSpent = budget.categories.reduce((s, c) => s + c.spent, 0)
  const totalAllocated = budget.categories.reduce((s, c) => s + c.allocated, 0)
  const remaining = budget.income - totalSpent
  const completedLessons = lessons.filter((l) => l.completed).length
  const recentSpend = spending.slice(0, 5)

  return (
    <AppShell>
      <div className="dashboard">
        <header className="dashboard__header">
          <div>
            <h1 className="dashboard__greeting">
              Hey{user?.first_name ? `, ${user.first_name}` : ''} 👋
            </h1>
            <p className="dashboard__date">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}</p>
          </div>
        </header>

        <div className="dashboard__grid">
          <DashboardCard title="This Month" accent="orange">
            <div className="dash-summary">
              <div className="dash-summary__stat">
                <span className="dash-summary__value">${budget.income.toLocaleString()}</span>
                <span className="dash-summary__label">Income</span>
              </div>
              <div className="dash-summary__stat">
                <span className="dash-summary__value dash-summary__value--spent">${totalSpent.toLocaleString()}</span>
                <span className="dash-summary__label">Spent</span>
              </div>
              <div className="dash-summary__stat">
                <span className={`dash-summary__value${remaining < 0 ? ' dash-summary__value--over' : ' dash-summary__value--left'}`}>
                  ${Math.abs(remaining).toLocaleString()}
                </span>
                <span className="dash-summary__label">{remaining < 0 ? 'Over budget' : 'Remaining'}</span>
              </div>
            </div>
            <ProgressBar value={totalSpent} max={totalAllocated} color="orange" showPercent />
          </DashboardCard>

          <DashboardCard title="Savings Goal">
            <div className="dash-goal">
              <GoalMeter label="Emergency Fund" current={1840} target={5000} />
              <p className="dash-goal__hint">$3,160 to go — keep it up!</p>
            </div>
          </DashboardCard>

          <DashboardCard title="Learning" action={() => navigate('/learn')} actionLabel="All lessons">
            <div className="dash-learn">
              <div className="dash-learn__stat">
                <span className="dash-learn__num">{completedLessons}</span>
                <span className="dash-learn__den"> / {lessons.length}</span>
              </div>
              <p className="dash-learn__label">lessons completed</p>
              <ProgressBar value={completedLessons} max={lessons.length} color="sage" showPercent />
              {lessons.find((l) => !l.completed) && (
                <button
                  type="button"
                  className="dash-learn__next"
                  onClick={() => navigate(`/learn/${lessons.find((l) => !l.completed).id}`)}
                >
                  Continue: {lessons.find((l) => !l.completed).title}
                </button>
              )}
            </div>
          </DashboardCard>

          <DashboardCard title="Recent Spending" action={() => navigate('/spend')} actionLabel="View all">
            {recentSpend.map((e) => (
              <ExpenseEntry key={e.id} entry={e} />
            ))}
          </DashboardCard>
        </div>
      </div>
    </AppShell>
  )
}
