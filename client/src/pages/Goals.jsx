import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import ErrorMessage from '../components/ErrorMessage'
import LoadingState from '../components/LoadingState'
import { createGoal, deleteGoal, getGoals, getGoalTypes } from '../services/goals'
import './Goals.css'

const EMPTY_FORM = { goal: '', name: '', target: '', notes: '' }

function firstError(value) {
  return Array.isArray(value) ? value[0] : value
}

export default function Goals() {
  const [goalTypes, setGoalTypes] = useState([])
  const [goals, setGoals] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [errors, setErrors] = useState({})
  const [pageError, setPageError] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    Promise.all([getGoalTypes(), getGoals()])
      .then(([types, savedGoals]) => {
        setGoalTypes(types)
        setGoals(savedGoals)
      })
      .catch(() => setPageError('Could not load your goals. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  function handleChange(event) {
    const { id, value } = event.target
    setForm((current) => ({ ...current, [id]: value }))
    setErrors((current) => ({ ...current, [id]: undefined }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setErrors({})
    setPageError('')
    setSaving(true)

    try {
      const savedGoal = await createGoal({
        ...form,
        goal: Number(form.goal),
        notes: form.notes || '',
      })
      setGoals((current) => [...current, savedGoal].sort((a, b) => a.name.localeCompare(b.name)))
      setForm(EMPTY_FORM)
    } catch (error) {
      const data = error?.response?.data
      if (data && typeof data === 'object') {
        setErrors(Object.fromEntries(Object.entries(data).map(([key, value]) => [key, firstError(value)])))
      } else {
        setPageError('Could not save your goal. Please try again.')
      }
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id) {
    setDeletingId(id)
    setPageError('')
    try {
      await deleteGoal(id)
      setGoals((current) => current.filter((goal) => goal.id !== id))
    } catch {
      setPageError('Could not delete that goal. Please try again.')
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) return <AppShell><LoadingState /></AppShell>

  return (
    <AppShell>
      <div className="goals-page">
        <header className="goals-page__header">
          <p className="goals-page__eyebrow">Plan your next milestone</p>
          <h1>Financial goals</h1>
          <p>Set a target and keep the details that matter to you in one place.</p>
        </header>

        {pageError && <ErrorMessage message={pageError} />}

        <div className="goals-layout">
          <section className="goal-form-card" aria-labelledby="new-goal-title">
            <h2 id="new-goal-title">Add a goal</h2>
            <form onSubmit={handleSubmit} className="goal-form" noValidate>
              <div className="goal-input">
                <label htmlFor="goal">Goal type <span aria-hidden="true">*</span></label>
                <select id="goal" value={form.goal} onChange={handleChange} required aria-invalid={!!errors.goal}>
                  <option value="">Choose a goal type</option>
                  {goalTypes.map((type) => <option key={type.id} value={type.id}>{type.goal}</option>)}
                </select>
                {errors.goal && <p role="alert">{errors.goal}</p>}
              </div>

              <div className="goal-input">
                <label htmlFor="name">Goal name <span aria-hidden="true">*</span></label>
                <input id="name" value={form.name} onChange={handleChange} maxLength="150" placeholder="e.g. Emergency fund" required aria-invalid={!!errors.name} />
                {errors.name && <p role="alert">{errors.name}</p>}
              </div>

              <div className="goal-input">
                <label htmlFor="target">Target amount <span aria-hidden="true">*</span></label>
                <input id="target" type="number" value={form.target} onChange={handleChange} min="0.01" step="0.01" placeholder="5000.00" required aria-invalid={!!errors.target} />
                {errors.target && <p role="alert">{errors.target}</p>}
              </div>

              <div className="goal-input">
                <label htmlFor="notes">Notes <small>Optional</small></label>
                <textarea id="notes" value={form.notes} onChange={handleChange} rows="4" placeholder="Add a timeline, motivation, or other details" aria-invalid={!!errors.notes} />
                {errors.notes && <p role="alert">{errors.notes}</p>}
              </div>

              {errors.non_field_errors && <p className="goal-form__error" role="alert">{errors.non_field_errors}</p>}
              <button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save goal'}</button>
            </form>
          </section>

          <section className="saved-goals" aria-labelledby="saved-goals-title">
            <h2 id="saved-goals-title">Your goals</h2>
            {goals.length === 0 ? (
              <div className="saved-goals__empty">Your saved goals will appear here.</div>
            ) : goals.map((goal) => (
              <article className="saved-goal" key={goal.id}>
                <div>
                  <span className="saved-goal__type">{goal.goal_name}</span>
                  <h3>{goal.name}</h3>
                  <strong>${Number(goal.target).toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong>
                  {goal.notes && <p>{goal.notes}</p>}
                </div>
                <button type="button" onClick={() => handleDelete(goal.id)} disabled={deletingId === goal.id} aria-label={`Delete ${goal.name}`}>
                  {deletingId === goal.id ? 'Deleting…' : 'Delete'}
                </button>
              </article>
            ))}
          </section>
        </div>
      </div>
    </AppShell>
  )
}
