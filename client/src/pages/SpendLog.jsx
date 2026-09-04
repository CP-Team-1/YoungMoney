import { useState } from 'react'
import AppShell from '../components/AppShell'
import ExpenseEntry from '../components/ExpenseEntry'
import EmptyState from '../components/EmptyState'
import { useFinancial } from '../context/FinancialContext'
import { mockSpendingCategories } from '../data/mockSpending'
import { formatMoney } from '../utils/money'
import './SpendLog.css'

const ALL = 'all'
const EMPTY_FORM = { merchant: '', category: 'food', amount: '', date: new Date().toISOString().slice(0, 10) }

function TransactionModal({ initial, onSave, onClose }) {
  const [form, setForm] = useState(
    initial
      ? { merchant: initial.merchant, category: initial.category, amount: String(initial.amount), date: initial.date }
      : EMPTY_FORM
  )
  const [errors, setErrors] = useState({})

  function validate() {
    const e = {}
    if (!form.merchant.trim()) e.merchant = 'Merchant is required'
    if (!form.category) e.category = 'Category is required'
    const amt = parseFloat(form.amount)
    if (!form.amount || isNaN(amt) || amt <= 0) e.amount = 'Enter a positive amount'
    if (!form.date) e.date = 'Date is required'
    return e
  }

  function handleChange(ev) {
    const { name, value } = ev.target
    setForm((f) => ({ ...f, [name]: value }))
    setErrors((e) => ({ ...e, [name]: undefined }))
  }

  function handleSubmit(ev) {
    ev.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    onSave({ ...form, amount: parseFloat(form.amount) })
  }

  return (
    <div className="sl-modal-overlay" onClick={onClose}>
      <div className="sl-modal" onClick={(e) => e.stopPropagation()}>
        <h2 className="sl-modal__title">{initial ? 'Edit Transaction' : 'Add Transaction'}</h2>
        <form onSubmit={handleSubmit} noValidate className="sl-modal__form">
          <div className="sl-field">
            <label className="sl-field__label" htmlFor="merchant">Merchant</label>
            <input className="sl-field__input" id="merchant" name="merchant" value={form.merchant} onChange={handleChange} placeholder="e.g. Whole Foods" />
            {errors.merchant && <p className="sl-field__error">{errors.merchant}</p>}
          </div>
          <div className="sl-field">
            <label className="sl-field__label" htmlFor="category">Category</label>
            <select className="sl-field__input" id="category" name="category" value={form.category} onChange={handleChange}>
              {mockSpendingCategories.map((c) => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
            </select>
            {errors.category && <p className="sl-field__error">{errors.category}</p>}
          </div>
          <div className="sl-field">
            <label className="sl-field__label" htmlFor="amount">Amount ($)</label>
            <input className="sl-field__input" id="amount" name="amount" type="number" min="0.01" step="0.01" value={form.amount} onChange={handleChange} placeholder="0.00" />
            {errors.amount && <p className="sl-field__error">{errors.amount}</p>}
          </div>
          <div className="sl-field">
            <label className="sl-field__label" htmlFor="date">Date</label>
            <input className="sl-field__input" id="date" name="date" type="date" value={form.date} onChange={handleChange} />
            {errors.date && <p className="sl-field__error">{errors.date}</p>}
          </div>
          <div className="sl-modal__actions">
            <button type="submit" className="sl-btn sl-btn--primary">{initial ? 'Save Changes' : 'Add Transaction'}</button>
            <button type="button" className="sl-btn sl-btn--ghost" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function SpendLog() {
  const { transactions, categories: budgetCategories, addTransaction, updateTransaction, deleteTransaction, clearTransactions } = useFinancial()
  const [filter, setFilter] = useState(ALL)
  const [showModal, setShowModal] = useState(false)
  const [editingTx, setEditingTx] = useState(null)

  const categories = [ALL, ...new Set(transactions.map((s) => s.category))]
  const filtered = filter === ALL ? transactions : transactions.filter((s) => s.category === filter)
  const total = filtered.reduce((s, e) => s + e.amount, 0)

  function openAdd() { setEditingTx(null); setShowModal(true) }
  function openEdit(entry) { setEditingTx(entry); setShowModal(true) }
  function closeModal() { setShowModal(false); setEditingTx(null) }

  function handleSave(form) {
    if (editingTx) {
      updateTransaction(editingTx.id, form)
    } else {
      addTransaction(form)
    }
    closeModal()
  }

  function handleDelete(id) {
    deleteTransaction(id)
  }

  function handleClearAll() {
    if (window.confirm('Clear all transactions? This cannot be undone.')) {
      clearTransactions()
      setFilter(ALL)
    }
  }

  return (
    <AppShell>
      <div className="spend-log">
        <header className="spend-log__header">
          <h1 className="spend-log__title">Spend Log</h1>
          <span className="spend-log__total">{formatMoney(total)}</span>
        </header>

        <div className="spend-log__controls">
          <button type="button" className="sl-btn sl-btn--primary" onClick={openAdd}>+ Add Transaction</button>
          {transactions.length > 0 && (
            <button type="button" className="sl-btn sl-btn--danger" onClick={handleClearAll}>Clear All</button>
          )}
        </div>

        <div className="spend-log__filters" role="group" aria-label="Filter by category">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              className={`spend-filter${filter === cat ? ' spend-filter--active' : ''}`}
              onClick={() => setFilter(cat)}
            >
              {cat === ALL ? 'All' : cat}
            </button>
          ))}
        </div>

        <div className="spend-log__list">
          {filtered.length === 0 ? (
            <EmptyState title="No transactions" message="Transactions will appear here as you log spending." />
          ) : (
            filtered.map((e) => (
              <ExpenseEntry
                key={e.id}
                entry={e}
                color={budgetCategories.find((c) => c.id === e.category)?.color}
                onEdit={openEdit}
                onDelete={handleDelete}
              />
            ))
          )}
        </div>
      </div>

      {showModal && (
        <TransactionModal
          initial={editingTx}
          onSave={handleSave}
          onClose={closeModal}
        />
      )}
    </AppShell>
  )
}
