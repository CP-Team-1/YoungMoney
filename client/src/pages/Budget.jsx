import { useState } from 'react'
import AppShell from '../components/AppShell'
import BudgetJar from '../components/BudgetJar'
import ProgressBar from '../components/ProgressBar'
import { useFinancial } from '../context/FinancialContext'
import { formatMoney } from '../utils/money'
import './Budget.css'

const PRESET_COLORS = [
  '#e8834a', '#e05050', '#e8c84a', '#c9a96e',
  '#7fa882', '#4ab07f', '#5ba0d0', '#8fa8c8',
  '#7070c8', '#b8829a', '#c060b0', '#a08060',
  '#6b8f6b', '#7090a0',
]
const EMPTY_CAT_FORM = { label: '', allocated: '', color: PRESET_COLORS[0] }

function CategoryModal({ initial, onSave, onClose }) {
  const [form, setForm] = useState(
    initial
      ? { label: initial.label, allocated: String(initial.allocated), color: initial.color }
      : EMPTY_CAT_FORM
  )
  const [errors, setErrors] = useState({})

  function validate() {
    const e = {}
    if (!form.label.trim()) e.label = 'Name is required'
    const amt = parseFloat(form.allocated)
    if (!form.allocated || isNaN(amt) || amt < 0) e.allocated = 'Enter a valid amount'
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
    onSave({ ...form, allocated: parseFloat(form.allocated) })
  }

  return (
    <div className="sl-modal-overlay" onClick={onClose}>
      <div className="sl-modal" onClick={(e) => e.stopPropagation()}>
        <h2 className="sl-modal__title">{initial ? 'Edit Category' : 'Add Category'}</h2>
        <form onSubmit={handleSubmit} noValidate className="sl-modal__form">
          <div className="sl-field">
            <label className="sl-field__label" htmlFor="cat-label">Name</label>
            <input
              className="sl-field__input"
              id="cat-label"
              name="label"
              value={form.label}
              onChange={handleChange}
              placeholder="e.g. Entertainment"
              disabled={!!initial}
            />
            {errors.label && <p className="sl-field__error">{errors.label}</p>}
          </div>
          <div className="sl-field">
            <label className="sl-field__label" htmlFor="cat-allocated">Monthly Budget ($)</label>
            <input
              className="sl-field__input"
              id="cat-allocated"
              name="allocated"
              type="number"
              min="0"
              step="1"
              value={form.allocated}
              onChange={handleChange}
              placeholder="0"
            />
            {errors.allocated && <p className="sl-field__error">{errors.allocated}</p>}
          </div>
          <div className="sl-field">
            <label className="sl-field__label">Color</label>
            <div className="budget-color-swatches">
              {PRESET_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  className={`budget-color-swatch${form.color === c ? ' budget-color-swatch--active' : ''}`}
                  style={{ background: c }}
                  onClick={() => setForm((f) => ({ ...f, color: c }))}
                  aria-label={c}
                />
              ))}
            </div>
          </div>
          <div className="sl-modal__actions">
            <button type="submit" className="sl-btn sl-btn--primary">{initial ? 'Save Changes' : 'Add Category'}</button>
            <button type="button" className="sl-btn sl-btn--ghost" onClick={onClose}>Cancel</button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Budget() {
  const {
    income,
    categories,
    totalSpent,
    totalAllocated,
    updateIncome,
    addBudgetCategory,
    updateBudgetCategory,
    deleteBudgetCategory,
  } = useFinancial()

  const [editingIncome, setEditingIncome] = useState(false)
  const [incomeInput, setIncomeInput] = useState('')
  const [showCatModal, setShowCatModal] = useState(false)
  const [editingCat, setEditingCat] = useState(null)

  const unallocated = income - totalAllocated

  function startEditIncome() {
    setIncomeInput(String(income))
    setEditingIncome(true)
  }

  function commitIncome() {
    const val = parseFloat(incomeInput)
    if (!isNaN(val) && val >= 0) updateIncome(val)
    setEditingIncome(false)
  }

  function handleIncomeKey(ev) {
    if (ev.key === 'Enter') commitIncome()
    if (ev.key === 'Escape') setEditingIncome(false)
  }

  function openAddCat() { setEditingCat(null); setShowCatModal(true) }
  function openEditCat(cat) { setEditingCat(cat); setShowCatModal(true) }
  function closeCatModal() { setShowCatModal(false); setEditingCat(null) }

  function handleCatSave(form) {
    if (editingCat) {
      updateBudgetCategory(editingCat.id, { label: editingCat.label, allocated: form.allocated, color: form.color })
    } else {
      addBudgetCategory(form)
    }
    closeCatModal()
  }

  function handleDeleteCat(id) {
    if (window.confirm('Delete this budget category?')) {
      deleteBudgetCategory(id)
    }
  }

  return (
    <AppShell>
      <div className="budget-page">
        <header className="budget-page__header">
          <h1 className="budget-page__title">Budget</h1>
          <div className="budget-page__income">
            <span className="budget-page__income-label">Monthly income</span>
            {editingIncome ? (
              <input
                className="budget-income-input"
                type="number"
                min="0"
                step="1"
                value={incomeInput}
                onChange={(e) => setIncomeInput(e.target.value)}
                onBlur={commitIncome}
                onKeyDown={handleIncomeKey}
                autoFocus
              />
            ) : (
              <span className="budget-page__income-val budget-income-editable" onClick={startEditIncome}>
                {formatMoney(income)} <span className="budget-edit-icon">✎</span>
              </span>
            )}
          </div>
        </header>

        <div className="budget-summary">
          <div className="budget-summary__item">
            <span className="budget-summary__val">{formatMoney(totalAllocated)}</span>
            <span className="budget-summary__label">Allocated</span>
          </div>
          <div className="budget-summary__item">
            <span className="budget-summary__val budget-summary__val--spent">{formatMoney(totalSpent)}</span>
            <span className="budget-summary__label">Spent</span>
          </div>
          <div className="budget-summary__item">
            <span className={`budget-summary__val${unallocated < 0 ? ' budget-summary__val--over' : ' budget-summary__val--free'}`}>
              {formatMoney(Math.abs(unallocated))}
            </span>
            <span className="budget-summary__label">{unallocated < 0 ? 'Over-allocated' : 'Unallocated'}</span>
          </div>
        </div>

        <div className="budget-page__bar">
          <ProgressBar value={totalSpent} max={income} color="orange" label="Spent vs income" showPercent />
        </div>

        <section className="budget-jars-section">
          <div className="budget-section-header">
            <h2 className="budget-jars-title">Categories</h2>
            <button type="button" className="sl-btn sl-btn--primary" onClick={openAddCat}>+ Add Category</button>
          </div>
          <div className="budget-jars">
            {categories.map((cat) => (
              <div key={cat.id} className="budget-jar-wrap">
                <BudgetJar category={cat} />
                <div className="budget-jar-actions">
                  <button
                    type="button"
                    className="expense-entry__action-btn"
                    onClick={() => openEditCat(cat)}
                    aria-label={`Edit ${cat.label}`}
                  >
                    ✎
                  </button>
                  <button
                    type="button"
                    className="expense-entry__action-btn expense-entry__action-btn--del"
                    onClick={() => handleDeleteCat(cat.id)}
                    aria-label={`Delete ${cat.label}`}
                  >
                    ×
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="budget-table-section">
          <h2 className="budget-table-title">Breakdown</h2>
          <div className="budget-table">
            {categories.map((cat) => {
              const pct = cat.allocated > 0 ? Math.round((cat.spent / cat.allocated) * 100) : 0
              return (
                <div key={cat.id} className="budget-row">
                  <div className="budget-row__left">
                    <span className="budget-row__dot" style={{ background: cat.color }} />
                    <span className="budget-row__label">{cat.label}</span>
                  </div>
                  <div className="budget-row__right">
                    <span className="budget-row__spent">{formatMoney(cat.spent)}</span>
                    <span className="budget-row__alloc"> / {formatMoney(cat.allocated)}</span>
                    <span className={`budget-row__pct${pct > 100 ? ' budget-row__pct--over' : ''}`}>{pct}%</span>
                    <button
                      type="button"
                      className="expense-entry__action-btn"
                      onClick={() => openEditCat(cat)}
                      aria-label={`Edit ${cat.label}`}
                    >
                      ✎
                    </button>
                    <button
                      type="button"
                      className="expense-entry__action-btn expense-entry__action-btn--del"
                      onClick={() => handleDeleteCat(cat.id)}
                      aria-label={`Delete ${cat.label}`}
                    >
                      ×
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      </div>

      {showCatModal && (
        <CategoryModal
          initial={editingCat}
          onSave={handleCatSave}
          onClose={closeCatModal}
        />
      )}
    </AppShell>
  )
}
