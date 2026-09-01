import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Onboarding.css'

const GOALS = [
  { id: 'travel',   label: 'Travel Rewards',  desc: 'Maximize airline miles, hotel points, and travel perks.',   icon: '✈' },
  { id: 'cashback', label: 'Cash Back',        desc: 'Get straightforward cash back on everyday spending.',        icon: '$' },
  { id: 'points',   label: 'Points Strategy', desc: 'Earn flexible points redeemable for travel, gift cards, and more.', icon: '◎' },
  { id: 'build',    label: 'Build Credit',     desc: 'Establish or repair credit with smart, low-risk card use.',  icon: '↑' },
]

export default function GoalSelect() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(null)

  function handleContinue() {
    if (!selected) return
    localStorage.setItem('ym_goal', selected)
    navigate('/onboarding/income')
  }

  return (
    <div className="onboarding">
      <div className="onboarding__inner">
        <div className="onboarding__step">Step 1 of 2</div>
        <h1 className="onboarding__title">What's your main goal?</h1>
        <p className="onboarding__sub">We'll optimize your card recommendations around this.</p>

        <div className="goal-grid">
          {GOALS.map((g) => (
            <button
              key={g.id}
              type="button"
              className={`goal-option${selected === g.id ? ' goal-option--selected' : ''}`}
              onClick={() => setSelected(g.id)}
              aria-pressed={selected === g.id}
            >
              <span className="goal-option__icon">{g.icon}</span>
              <strong className="goal-option__label">{g.label}</strong>
              <p className="goal-option__desc">{g.desc}</p>
            </button>
          ))}
        </div>

        <button
          type="button"
          className={`onboarding__cta${selected ? ' onboarding__cta--active' : ''}`}
          onClick={handleContinue}
          disabled={!selected}
        >
          Continue
        </button>
      </div>
    </div>
  )
}
