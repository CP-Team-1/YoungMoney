import { useState } from 'react'
import AppShell from '../components/AppShell'
import ExpenseEntry from '../components/ExpenseEntry'
import EmptyState from '../components/EmptyState'
import LoadingState from '../components/LoadingState'
import { useFinancial } from '../context/FinancialContext'
import { formatMoney } from '../utils/money'
import './SpendLog.css'

const ALL = 'all'
const CUSTOM = '__custom__'

const STANDARD_CATEGORIES = [
  {
    id: 'groceries',
    label: 'Groceries',
  },
  {
    id: 'transport',
    label: 'Transport',
  },
  {
    id: 'housing',
    label: 'Housing',
  },
  {
    id: 'utilities',
    label: 'Utilities',
  },
  {
    id: 'subscriptions',
    label: 'Subscriptions',
  },
  {
    id: 'fun',
    label: 'Fun',
  },
  {
    id: 'savings',
    label: 'Savings',
  },
  {
    id: 'other',
    label: 'Other',
  },
]

function normalizeLabel(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .replace(/\s+/g, '-')
}

function makeEmptyForm() {
  return {
    merchant: '',
    category:
      STANDARD_CATEGORIES[0].id,
    customCategory: '',
    amount: '',
    date: new Date()
      .toISOString()
      .slice(0, 10),
  }
}

function makeInitialForm(
  initial,
  resolveBudgetCategory
) {
  if (!initial) {
    return makeEmptyForm()
  }

  const standard =
    STANDARD_CATEGORIES.find(
      (category) =>
        category.id ===
        initial.category
    )

  if (standard) {
    return {
      merchant:
        initial.merchant,
      category:
        standard.id,
      customCategory: '',
      amount: String(
        initial.amount
      ),
      date: initial.date,
    }
  }

  const matchedBudget =
    resolveBudgetCategory(
      initial.category
    )

  if (matchedBudget) {
    return {
      merchant:
        initial.merchant,
      category:
        matchedBudget.id,
      customCategory: '',
      amount: String(
        initial.amount
      ),
      date: initial.date,
    }
  }

  return {
    merchant:
      initial.merchant,
    category: CUSTOM,
    customCategory:
      initial.category,
    amount: String(
      initial.amount
    ),
    date: initial.date,
  }
}

function TransactionModal({
  initial,
  budgetCategories,
  resolveBudgetCategory,
  onSave,
  onClose,
}) {
  const [form, setForm] =
    useState(() =>
      makeInitialForm(
        initial,
        resolveBudgetCategory
      )
    )

  const [errors, setErrors] =
    useState({})

  const standardLabels =
    new Set(
      STANDARD_CATEGORIES.map(
        (category) =>
          normalizeLabel(
            category.label
          )
      )
    )

  const standardIds =
    new Set(
      STANDARD_CATEGORIES.map(
        (category) =>
          category.id
      )
    )

  const extraBudgetCategories =
    budgetCategories.filter(
      (category) =>
        !standardIds.has(
          category.id
        ) &&
        !standardLabels.has(
          normalizeLabel(
            category.label
          )
        )
    )

  function validate() {
    const e = {}

    if (
      !form.merchant.trim()
    ) {
      e.merchant =
        'Merchant is required'
    }

    if (!form.category) {
      e.category =
        'Category is required'
    }

    if (
      form.category ===
        CUSTOM &&
      !form.customCategory.trim()
    ) {
      e.customCategory =
        'Enter a custom category'
    }

    if (
      form.category ===
        CUSTOM &&
      form.customCategory
        .trim().length > 64
    ) {
      e.customCategory =
        'Custom category must be 64 characters or fewer'
    }

    const amt =
      parseFloat(
        form.amount
      )

    if (
      !form.amount ||
      isNaN(amt) ||
      amt <= 0
    ) {
      e.amount =
        'Enter a positive amount'
    }

    if (!form.date) {
      e.date =
        'Date is required'
    }

    return e
  }

  function handleChange(ev) {
    const {
      name,
      value,
    } = ev.target

    setForm(
      (current) => ({
        ...current,
        [name]: value,
      })
    )

    setErrors(
      (current) => ({
        ...current,
        [name]: undefined,
      })
    )
  }

  function handleCategoryChange(
    ev
  ) {
    const value =
      ev.target.value

    setForm(
      (current) => ({
        ...current,
        category: value,
        customCategory:
          value === CUSTOM
            ? current.customCategory
            : '',
      })
    )

    setErrors(
      (current) => ({
        ...current,
        category: undefined,
        customCategory:
          undefined,
      })
    )
  }

  function handleSubmit(ev) {
    ev.preventDefault()

    const errs =
      validate()

    if (
      Object.keys(errs)
        .length
    ) {
      setErrors(errs)
      return
    }

    const finalCategory =
      form.category ===
      CUSTOM
        ? form.customCategory.trim()
        : form.category

    onSave({
      merchant:
        form.merchant.trim(),
      category:
        finalCategory,
      amount:
        parseFloat(
          form.amount
        ),
      date: form.date,
    })
  }

  return (
    <div
      className="sl-modal-overlay"
      onClick={onClose}
    >
      <div
        className="sl-modal"
        onClick={(e) =>
          e.stopPropagation()
        }
      >
        <h2 className="sl-modal__title">
          {initial
            ? 'Edit Transaction'
            : 'Add Transaction'}
        </h2>

        <form
          onSubmit={
            handleSubmit
          }
          noValidate
          className="sl-modal__form"
        >
          <div className="sl-field">
            <label
              className="sl-field__label"
              htmlFor="merchant"
            >
              Merchant
            </label>

            <input
              className="sl-field__input"
              id="merchant"
              name="merchant"
              value={
                form.merchant
              }
              onChange={
                handleChange
              }
              placeholder="e.g. Whole Foods"
            />

            {errors.merchant && (
              <p className="sl-field__error">
                {
                  errors.merchant
                }
              </p>
            )}
          </div>

          <div className="sl-field">
            <label
              className="sl-field__label"
              htmlFor="category"
            >
              Category
            </label>

            <select
              className="sl-field__input"
              id="category"
              name="category"
              value={
                form.category
              }
              onChange={
                handleCategoryChange
              }
            >
              <optgroup label="Spending Categories">
                {STANDARD_CATEGORIES.map(
                  (
                    category
                  ) => (
                    <option
                      key={
                        category.id
                      }
                      value={
                        category.id
                      }
                    >
                      {
                        category.label
                      }
                    </option>
                  )
                )}
              </optgroup>

              {extraBudgetCategories.length >
                0 && (
                <optgroup label="Your Budget Categories">
                  {extraBudgetCategories.map(
                    (
                      category
                    ) => (
                      <option
                        key={
                          category.id
                        }
                        value={
                          category.id
                        }
                      >
                        {
                          category.label
                        }
                      </option>
                    )
                  )}
                </optgroup>
              )}

              <option
                value={CUSTOM}
              >
                Custom...
              </option>
            </select>

            {errors.category && (
              <p className="sl-field__error">
                {
                  errors.category
                }
              </p>
            )}
          </div>

          {form.category ===
            CUSTOM && (
            <div className="sl-field">
              <label
                className="sl-field__label"
                htmlFor="customCategory"
              >
                Custom Category
              </label>

              <input
                className="sl-field__input"
                id="customCategory"
                name="customCategory"
                value={
                  form.customCategory
                }
                onChange={
                  handleChange
                }
                maxLength={64}
                placeholder="e.g. Pet Food"
                autoFocus
              />

              {errors.customCategory && (
                <p className="sl-field__error">
                  {
                    errors.customCategory
                  }
                </p>
              )}
            </div>
          )}

          <div className="sl-field">
            <label
              className="sl-field__label"
              htmlFor="amount"
            >
              Amount ($)
            </label>

            <input
              className="sl-field__input"
              id="amount"
              name="amount"
              type="number"
              min="0.01"
              step="0.01"
              value={
                form.amount
              }
              onChange={
                handleChange
              }
              placeholder="0.00"
            />

            {errors.amount && (
              <p className="sl-field__error">
                {errors.amount}
              </p>
            )}
          </div>

          <div className="sl-field">
            <label
              className="sl-field__label"
              htmlFor="date"
            >
              Date
            </label>

            <input
              className="sl-field__input"
              id="date"
              name="date"
              type="date"
              value={
                form.date
              }
              onChange={
                handleChange
              }
            />

            {errors.date && (
              <p className="sl-field__error">
                {errors.date}
              </p>
            )}
          </div>

          <div className="sl-modal__actions">
            <button
              type="submit"
              className="sl-btn sl-btn--primary"
            >
              {initial
                ? 'Save Changes'
                : 'Add Transaction'}
            </button>

            <button
              type="button"
              className="sl-btn sl-btn--ghost"
              onClick={
                onClose
              }
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function SpendLog() {
  const {
    loading,
    transactions,
    categories:
      budgetCategories,
    resolveBudgetCategory,
    addTransaction,
    updateTransaction,
    deleteTransaction,
    clearTransactions,
  } = useFinancial()

  const [filter, setFilter] =
    useState(ALL)

  const [
    showModal,
    setShowModal,
  ] = useState(false)

  const [
    editingTx,
    setEditingTx,
  ] = useState(null)

  if (loading) {
    return (
      <AppShell>
        <LoadingState />
      </AppShell>
    )
  }

  const txCategoryValues = [
    ...new Set(
      transactions.map(
        (transaction) =>
          transaction.category
      )
    ),
  ]

  function resolveCategoryLabel(
    value
  ) {
    const matchedBudget =
      resolveBudgetCategory(
        value
      )

    if (matchedBudget) {
      return matchedBudget.label
    }

    const standardCategory =
      STANDARD_CATEGORIES.find(
        (category) =>
          category.id ===
          value
      )

    if (
      standardCategory
    ) {
      return (
        standardCategory.label
      )
    }

    return value
  }

  const filtered =
    filter === ALL
      ? transactions
      : transactions.filter(
          (transaction) =>
            transaction.category ===
            filter
        )

  const total =
    filtered.reduce(
      (sum, entry) =>
        sum + entry.amount,
      0
    )

  function openAdd() {
    setEditingTx(null)
    setShowModal(true)
  }

  function openEdit(entry) {
    setEditingTx(entry)
    setShowModal(true)
  }

  function closeModal() {
    setShowModal(false)
    setEditingTx(null)
  }

  async function handleSave(
    form
  ) {
    try {
      if (editingTx) {
        await updateTransaction(
          editingTx.id,
          form
        )
      } else {
        await addTransaction(
          form
        )
      }

      closeModal()
    } catch (err) {
      console.error(
        'Failed to save transaction',
        err
      )
    }
  }

  async function handleDelete(
    id
  ) {
    try {
      await deleteTransaction(
        id
      )
    } catch (err) {
      console.error(
        'Failed to delete transaction',
        err
      )
    }
  }

  async function handleClearAll() {
    if (
      !window.confirm(
        'Clear all transactions? This cannot be undone.'
      )
    ) {
      return
    }

    try {
      await clearTransactions()
      setFilter(ALL)
    } catch (err) {
      console.error(
        'Failed to clear transactions',
        err
      )
    }
  }

  return (
    <AppShell>
      <div className="spend-log">
        <header className="spend-log__header">
          <h1 className="spend-log__title">
            Spend Log
          </h1>

          <span className="spend-log__total">
            {formatMoney(
              total
            )}
          </span>
        </header>

        <div className="spend-log__controls">
          <button
            type="button"
            className="sl-btn sl-btn--primary"
            onClick={
              openAdd
            }
          >
            + Add Transaction
          </button>

          {transactions.length >
            0 && (
            <button
              type="button"
              className="sl-btn sl-btn--danger"
              onClick={
                handleClearAll
              }
            >
              Clear All
            </button>
          )}
        </div>

        <div
          className="spend-log__filters"
          role="group"
          aria-label="Filter by category"
        >
          <button
            type="button"
            className={
              `spend-filter${
                filter === ALL
                  ? ' spend-filter--active'
                  : ''
              }`
            }
            onClick={() =>
              setFilter(ALL)
            }
          >
            All
          </button>

          {txCategoryValues.map(
            (value) => (
              <button
                key={value}
                type="button"
                className={
                  `spend-filter${
                    filter ===
                    value
                      ? ' spend-filter--active'
                      : ''
                  }`
                }
                onClick={() =>
                  setFilter(
                    value
                  )
                }
              >
                {resolveCategoryLabel(
                  value
                )}
              </button>
            )
          )}
        </div>

        <div className="spend-log__list">
          {filtered.length ===
          0 ? (
            <EmptyState
              title="No transactions"
              message="Transactions will appear here as you log spending."
            />
          ) : (
            filtered.map(
              (entry) => {
                const matchedBudget =
                  resolveBudgetCategory(
                    entry.category
                  )

                return (
                  <ExpenseEntry
                    key={
                      entry.id
                    }
                    entry={
                      entry
                    }
                    color={
                      matchedBudget?.color
                    }
                    categoryLabel={
                      resolveCategoryLabel(
                        entry.category
                      )
                    }
                    onEdit={
                      openEdit
                    }
                    onDelete={
                      handleDelete
                    }
                  />
                )
              }
            )
          )}
        </div>
      </div>

      {showModal && (
        <TransactionModal
          initial={
            editingTx
          }
          budgetCategories={
            budgetCategories
          }
          resolveBudgetCategory={
            resolveBudgetCategory
          }
          onSave={
            handleSave
          }
          onClose={
            closeModal
          }
        />
      )}
    </AppShell>
  )
}