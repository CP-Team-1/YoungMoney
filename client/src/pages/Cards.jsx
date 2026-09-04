import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import LoadingState from '../components/LoadingState'
import EmptyState from '../components/EmptyState'
import { getCards } from '../services/cards'
import { getCardAdvice } from '../services/advisor'
import './Cards.css'

const GOALS = ['All', 'Travel', 'Cashback', 'No annual fee', 'Groceries', 'Dining']

// ─── Add-card modal ──────────────────────────────────────────────────────────
function AddCardModal({ available, onAdd, onClose }) {
  return (
    <div className="sl-modal-overlay" onClick={onClose}>
      <div className="sl-modal" onClick={(e) => e.stopPropagation()}>
        <h2 className="sl-modal__title">Add Card to Your Wallet</h2>
        {available.length === 0 ? (
          <p style={{ color: 'var(--color-muted)', fontSize: 14 }}>
            You already own all available cards.
          </p>
        ) : (
          <ul className="add-card-list">
            {available.map((card) => (
              <li key={card.id} className="add-card-item">
                <div>
                  <p className="add-card-item__issuer">{card.issuer}</p>
                  <p className="add-card-item__name">{card.name}</p>
                </div>
                <button
                  type="button"
                  className="sl-btn sl-btn--primary"
                  onClick={() => onAdd(card.id)}
                >
                  Add
                </button>
              </li>
            ))}
          </ul>
        )}
        <div style={{ marginTop: 'var(--space-5)' }}>
          <button type="button" className="sl-btn sl-btn--ghost" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  )
}

// ─── Manage-card modal (edit / remove) ───────────────────────────────────────
function ManageCardModal({ card, onRemove, onClose }) {
  return (
    <div className="sl-modal-overlay" onClick={onClose}>
      <div className="sl-modal" onClick={(e) => e.stopPropagation()}>
        <h2 className="sl-modal__title">Manage Card</h2>
        <div className="manage-card-preview">
          <p className="card-item__issuer">{card.issuer}</p>
          <h3 className="card-item__name" style={{ marginBottom: 'var(--space-3)' }}>{card.name}</h3>
          <ul className="card-item__highlights">
            {card.highlights.map((h, i) => (
              <li key={i} className="card-item__highlight">{h}</li>
            ))}
          </ul>
        </div>
        <div className="sl-modal__actions" style={{ marginTop: 'var(--space-6)' }}>
          <button
            type="button"
            className="sl-btn sl-btn--danger-solid"
            onClick={() => { onRemove(card.id); onClose() }}
          >
            Remove from My Wallet
          </button>
          <button type="button" className="sl-btn sl-btn--ghost" onClick={onClose}>Cancel</button>
        </div>
      </div>
    </div>
  )
}

// ─── Card tile ───────────────────────────────────────────────────────────────
function CardItem({ card, owned, onEdit }) {
  const rewardColor = {
    cashback: 'var(--color-sage)',
    points: 'var(--color-orange)',
    miles: '#8fa8c8',
  }[card.rewardType] ?? 'var(--color-muted)'

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
        {owned && onEdit && (
          <button
            type="button"
            className="sl-btn sl-btn--ghost card-item__manage-btn"
            onClick={() => onEdit(card)}
            aria-label={`Manage ${card.name}`}
          >
            Manage
          </button>
        )}
      </div>
    </div>
  )
}

// ─── AI advice panel ─────────────────────────────────────────────────────────
function AiAdvisorPanel({ ownedCards }) {
  const [status, setStatus] = useState('idle') // idle | loading | success | empty | error
  const [suggestion, setSuggestion] = useState('')
  const [errorMsg, setErrorMsg] = useState('')

  async function handleGetAdvice() {
    setStatus('loading')
    setErrorMsg('')
    try {
      const ownedNames = ownedCards.map((c) => c.name)
      const text = await getCardAdvice({ ownedCards: ownedNames })
      setSuggestion(text || '')
      setStatus(text ? 'success' : 'empty')
    } catch {
      setErrorMsg('Could not reach the AI advisor. Please try again later.')
      setStatus('error')
    }
  }

  return (
    <div className="cards-ai-panel">
      <div className="cards-ai-panel__header">
        <div>
          <h2 className="cards-ai-panel__title">✦ AI Card Advisor</h2>
          <p className="cards-ai-panel__desc">
            Based on the cards in your wallet, our AI suggests what to add, replace,
            or how to combine cards for better rewards.
          </p>
        </div>
        <button
          type="button"
          className="sl-btn sl-btn--primary cards-ai-panel__cta"
          onClick={handleGetAdvice}
          disabled={status === 'loading'}
        >
          {status === 'loading' ? 'Analyzing…' : 'Get AI Recommendations'}
        </button>
      </div>

      {status === 'loading' && (
        <div className="cards-ai-loading">
          <span className="cards-ai-loading__dot" />
          <span className="cards-ai-loading__dot" />
          <span className="cards-ai-loading__dot" />
          <p className="cards-ai-loading__text">Analyzing your card portfolio…</p>
        </div>
      )}

      {status === 'success' && (
        <div className="cards-ai-result">
          <div className="cards-ai-result__text">{suggestion}</div>
          <button
            type="button"
            className="sl-btn sl-btn--ghost"
            style={{ marginTop: 'var(--space-4)', fontSize: 12 }}
            onClick={handleGetAdvice}
          >
            Refresh
          </button>
        </div>
      )}

      {status === 'empty' && (
        <p className="cards-ai-empty">
          No recommendations returned. Try adding cards to your wallet first.
        </p>
      )}

      {status === 'error' && (
        <p className="cards-ai-error">{errorMsg}</p>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function Cards() {
  const [cards, setCards] = useState([])
  const [ownedIds, setOwnedIds] = useState(null) // null until cards load
  const [filter, setFilter] = useState('All')
  const [loading, setLoading] = useState(true)
  const [showAddModal, setShowAddModal] = useState(false)
  const [managingCard, setManagingCard] = useState(null)

  useEffect(() => {
    getCards().then((data) => {
      setCards(data)
      setOwnedIds(new Set(data.filter((c) => c.owned).map((c) => c.id)))
    }).finally(() => setLoading(false))
  }, [])

  if (loading) return <AppShell><LoadingState /></AppShell>

  const owned = cards.filter((c) => ownedIds.has(c.id))
  const notOwned = cards.filter((c) => !ownedIds.has(c.id))

  const filtered = filter === 'All'
    ? cards
    : cards.filter((c) => c.bestFor.some((b) => b.toLowerCase() === filter.toLowerCase()))

  function addCard(id) {
    setOwnedIds((prev) => new Set([...prev, id]))
    setShowAddModal(false)
  }

  function removeCard(id) {
    setOwnedIds((prev) => { const next = new Set(prev); next.delete(id); return next })
  }

  return (
    <AppShell>
      <div className="cards-page">
        <header className="cards-page__header">
          <h1 className="cards-page__title">Card Optimizer</h1>
          <p className="cards-page__sub">
            Find the best credit cards for your spending and get personalized AI advice.
          </p>
        </header>

        {/* Your Cards */}
        <section className="cards-section">
          <div className="cards-section__top cards-section__top--row">
            <h2 className="cards-section__title">Your cards</h2>
            <button
              type="button"
              className="sl-btn sl-btn--primary"
              onClick={() => setShowAddModal(true)}
            >
              + Add Card
            </button>
          </div>

          {owned.length === 0 ? (
            <EmptyState title="No cards yet" message="Add a card to your wallet to get started." />
          ) : (
            <div className="cards-grid">
              {owned.map((card) => (
                <CardItem
                  key={card.id}
                  card={card}
                  owned
                  onEdit={setManagingCard}
                />
              ))}
            </div>
          )}
        </section>

        {/* Browse Cards */}
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
              {filtered.map((card) => (
                <CardItem key={card.id} card={card} owned={ownedIds.has(card.id)} />
              ))}
            </div>
          )}
        </section>

        {/* Recommended for You — AI section */}
        <section className="cards-section">
          <h2 className="cards-section__title">Recommended for You</h2>
          <AiAdvisorPanel ownedCards={owned} />
        </section>
      </div>

      {showAddModal && (
        <AddCardModal
          available={notOwned}
          onAdd={addCard}
          onClose={() => setShowAddModal(false)}
        />
      )}

      {managingCard && (
        <ManageCardModal
          card={managingCard}
          onRemove={removeCard}
          onClose={() => setManagingCard(null)}
        />
      )}
    </AppShell>
  )
}
