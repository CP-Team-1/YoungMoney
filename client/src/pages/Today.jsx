import AppShell from '../components/AppShell'
import './Today.css'

const TIPS = [
  { id: 1, category: 'Credit', tip: "Check your credit report for free at AnnualCreditReport.com — you're entitled to one free report per bureau per year." },
  { id: 2, category: 'Budgeting', tip: "Review last week's spending in three categories. Awareness is the first step to change." },
  { id: 3, category: 'Investing', tip: "If your employer offers a 401(k) match, contribute at least enough to get the full match — it's free money." },
]

const CHECKLIST = [
  { id: 'check-budget', label: 'Review your budget' },
  { id: 'log-expense',  label: "Log today's spending" },
  { id: 'learn-lesson', label: 'Complete a lesson' },
]

export default function Today() {
  const tip = TIPS[new Date().getDay() % TIPS.length]

  return (
    <AppShell>
      <div className="today">
        <header className="today__header">
          <h1 className="today__title">Today</h1>
          <p className="today__date">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
        </header>

        <section className="today__tip">
          <span className="today__tip-label">{tip.category} tip</span>
          <p className="today__tip-text serif">{tip.tip}</p>
        </section>

        <section className="today__section">
          <h2 className="today__section-title">Daily checklist</h2>
          <div className="today__checklist">
            {CHECKLIST.map(({ id, label }) => (
              <label key={id} className="today__check-item">
                <input type="checkbox" className="today__checkbox" />
                <span className="today__check-label">{label}</span>
              </label>
            ))}
          </div>
        </section>

        <section className="today__section">
          <h2 className="today__section-title">Your streak</h2>
          <div className="today__streak">
            <span className="today__streak-num">7</span>
            <div>
              <p className="today__streak-label">day streak</p>
              <p className="today__streak-sub">Keep checking in daily to maintain it</p>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  )
}
