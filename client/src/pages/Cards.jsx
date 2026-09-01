import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import LoadingState from '../components/LoadingState'
import EmptyState from '../components/EmptyState'
import { getCards } from '../services/cards'
import './Cards.css'

const GOALS = ['All', 'Travel', 'Cashback', 'No annual fee', 'Groceries', 'Dining']

export default function Cards() {
  const [cards, setCards] = useState([])
  const [filter, setFilter] = useState('All')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCards().then(setCards).finally(() => setLoading(false))
  }, [])

  if (loading) return <AppShell><LoadingState /></AppShell>

  const filtered = filter === 'All'
    ? cards
    : cards.filter((c) => c.bestFor.some((b) => b.toLowerCase() === filter.toLowerCase()))

  const owned = cards.filter((c) => c.owned)

  return (
    <AppShell>
      <div className="cards-page">
        <header className="cards-page__header">
          <h1 className="cards-page__title">Card Optimizer</h1>
          <p className="cards-page__sub">
            Find the best credit cards for your spending. AI analysis coming soon.
          </p>
        </header>

        {owned.length > 0 && (
          <section className="cards-section">
            <h2 className="cards-section__title">Your cards</h2>
            <div className="cards-grid">
              {owned.map((card) => <CardItem key={card.id} card={card} owned />)}
            </div>
          </section>
        )}

        <section className="cards-section">
          <div className="cards-section__top">
            <h2 className="cards-section__title">Browse cards</h2>
            <div className="cards-filters">
              {GOALS.map((g) => (
                <button
                  key={g}
                  type="button"
                  className={`cards-filter${filter === g ? ' cards-filter--active' : ''}`}
                  onClick={() => setFilter(g)}
                >
                  {g}
                </button>
              ))}
            </div>
          </div>

          {filtered.length === 0 ? (
            <EmptyState title="No cards match" message="Try a different filter." />
          ) : (
            <div className="cards-grid">
              {filtered.map((card) => <CardItem key={card.id} card={card} />)}
            </div>
          )}
        </section>
      </div>
    </AppShell>
  )
}

function CardItem({ card, owned }) {
  const rewardColor = { cashback: 'var(--color-sage)', points: 'var(--color-orange)', miles: '#8fa8c8' }[card.rewardType] ?? 'var(--color-muted)'

  return (
    <div className={`card-item${owned ? ' card-item--owned' : ''}`}>
      <div className="card-item__top">
        <div>
          <p className="card-item__issuer">{card.issuer}</p>
          <h3 className="card-item__name">{card.name}</h3>
        </div>
        <div className="card-item__right">
          <span className="card-item__reward" style={{ color: rewardColor }}>
            {card.rewardType}
          </span>
          {owned && <span className="card-item__owned-tag">Owned</span>}
        </div>
      </div>

      <ul className="card-item__highlights">
        {card.highlights.map((h, i) => (
          <li key={i} className="card-item__highlight">{h}</li>
        ))}
      </ul>

      {card.signupBonus !== 'None' && (
        <div className="card-item__bonus">
          <span className="card-item__bonus-label">Sign-up bonus</span>
          <p className="card-item__bonus-text">{card.signupBonus}</p>
        </div>
      )}

      <div className="card-item__foot">
        <span className="card-item__fee">{card.annualFee === 0 ? 'No annual fee' : `$${card.annualFee}/yr`}</span>
        <span className="card-item__rating">★ {card.rating}</span>
      </div>
    </div>
  )
}
