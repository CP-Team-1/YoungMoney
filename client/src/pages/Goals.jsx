import { useState } from 'react'
import AppShell from '../components/AppShell'
import {
  CUSTOM_GOAL_TYPE_ID,
  useGoals,
} from '../context/GoalsContext'
import { formatMoney } from '../utils/money'
import './Goals.css'

const EMPTY_FORM = {
  goal: '',
  name: '',
  target: '',
  notes: '',
  customGoalType: '',
}

function EditGoalModal({
  goal,
  onSave,
  onClose,
}) {
  const [name, setName] =
    useState(goal.name)

  const [target, setTarget] =
    useState(
      String(goal.target)
    )

  const [notes, setNotes] =
    useState(
      goal.notes ?? ''
    )

  const [
    goalName,
    setGoalName,
  ] = useState(
    goal.goal_name ?? ''
  )

  const [errors, setErrors] =
    useState({})

  const [saving, setSaving] =
    useState(false)

  const isCustom =
    goal.goal ===
    CUSTOM_GOAL_TYPE_ID

  function validate() {
    const e = {}

    if (!name.trim()) {
      e.name =
        'Goal name is required'
    }

    if (
      isCustom &&
      !goalName.trim()
    ) {
      e.goalName =
        'Custom goal type is required'
    }

    const t =
      parseFloat(target)

    if (
      !target ||
      isNaN(t) ||
      t <= 0
    ) {
      e.target =
        'Enter a positive target amount'
    }

    return e
  }

  async function handleSubmit(
    event
  ) {
    event.preventDefault()

    const errs =
      validate()

    if (
      Object.keys(errs)
        .length
    ) {
      setErrors(errs)
      return
    }

    setSaving(true)

    try {
      await onSave({
        name:
          name.trim(),
        target:
          parseFloat(
            target
          ),
        notes:
          notes.trim(),
        ...(isCustom
          ? {
              goal_name:
                goalName.trim(),
            }
          : {}),
      })
    } catch (err) {
      console.error(
        'Failed to update goal',
        err
      )

      setErrors({
        form:
          'Could not save changes. Please try again.',
      })
    } finally {
      setSaving(false)
    }
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
          Edit Goal
        </h2>

        <form
          onSubmit={
            handleSubmit
          }
          className="sl-modal__form"
          noValidate
        >
          {isCustom && (
            <div className="sl-field">
              <label
                className="sl-field__label"
                htmlFor="edit-goal-name"
              >
                Goal type
              </label>

              <input
                className="sl-field__input"
                id="edit-goal-name"
                value={
                  goalName
                }
                onChange={(e) => {
                  setGoalName(
                    e.target.value
                  )

                  setErrors(
                    (previous) => ({
                      ...previous,
                      goalName:
                        undefined,
                      form:
                        undefined,
                    })
                  )
                }}
                maxLength="80"
                placeholder="e.g. Wedding, Business, Travel"
              />

              {errors.goalName && (
                <p className="sl-field__error">
                  {
                    errors.goalName
                  }
                </p>
              )}
            </div>
          )}

          <div className="sl-field">
            <label
              className="sl-field__label"
              htmlFor="edit-name"
            >
              Goal name
            </label>

            <input
              className="sl-field__input"
              id="edit-name"
              value={name}
              onChange={(e) => {
                setName(
                  e.target.value
                )

                setErrors(
                  (previous) => ({
                    ...previous,
                    name:
                      undefined,
                    form:
                      undefined,
                  })
                )
              }}
              maxLength="150"
              autoFocus={
                !isCustom
              }
            />

            {errors.name && (
              <p className="sl-field__error">
                {errors.name}
              </p>
            )}
          </div>

          <div className="sl-field">
            <label
              className="sl-field__label"
              htmlFor="edit-target"
            >
              Target amount ($)
            </label>

            <input
              className="sl-field__input"
              id="edit-target"
              type="number"
              min="0.01"
              step="0.01"
              value={target}
              onChange={(e) => {
                setTarget(
                  e.target.value
                )

                setErrors(
                  (previous) => ({
                    ...previous,
                    target:
                      undefined,
                    form:
                      undefined,
                  })
                )
              }}
              placeholder="0.00"
            />

            {errors.target && (
              <p className="sl-field__error">
                {errors.target}
              </p>
            )}
          </div>

          <div className="sl-field">
            <label
              className="sl-field__label"
              htmlFor="edit-notes"
            >
              Notes
            </label>

            <textarea
              className="sl-field__input"
              id="edit-notes"
              value={notes}
              onChange={(e) =>
                setNotes(
                  e.target.value
                )
              }
              rows="3"
              placeholder="Add a timeline, motivation, or other details"
            />
          </div>

          {errors.form && (
            <p className="sl-field__error">
              {errors.form}
            </p>
          )}

          <div className="sl-modal__actions">
            <button
              type="submit"
              className="sl-btn sl-btn--primary"
              disabled={saving}
            >
              {saving
                ? 'Saving…'
                : 'Save changes'}
            </button>

            <button
              type="button"
              className="sl-btn sl-btn--ghost"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Goals() {
  const {
    loading,
    goals,
    goalTypes,
    addGoal,
    deleteGoal,
    updateGoal,
  } = useGoals()

  const [form, setForm] =
    useState(EMPTY_FORM)

  const [errors, setErrors] =
    useState({})

  const [
    deletingId,
    setDeletingId,
  ] = useState(null)

  const [
    editingGoal,
    setEditingGoal,
  ] = useState(null)

  const [saving, setSaving] =
    useState(false)

  const isCustomType =
    form.goal ===
    CUSTOM_GOAL_TYPE_ID

  function handleChange(
    event
  ) {
    const {
      id,
      value,
    } = event.target

    setForm(
      (current) => ({
        ...current,
        [id]: value,
      })
    )

    setErrors(
      (current) => ({
        ...current,
        [id]: undefined,
        form: undefined,
      })
    )
  }

  function validate() {
    const e = {}

    if (!form.goal) {
      e.goal =
        'Choose a goal type'
    }

    if (
      isCustomType &&
      !form.customGoalType.trim()
    ) {
      e.customGoalType =
        'Enter a custom goal type'
    }

    if (!form.name.trim()) {
      e.name =
        'Goal name is required'
    }

    const t =
      parseFloat(
        form.target
      )

    if (
      !form.target ||
      isNaN(t) ||
      t <= 0
    ) {
      e.target =
        'Enter a positive target amount'
    }

    return e
  }

  async function handleSubmit(
    event
  ) {
    event.preventDefault()

    const errs =
      validate()

    if (
      Object.keys(errs)
        .length
    ) {
      setErrors(errs)
      return
    }

    setSaving(true)

    try {
      await addGoal({
        ...form,
        target:
          parseFloat(
            form.target
          ),
      })

      setForm(
        EMPTY_FORM
      )

      setErrors({})
    } catch (err) {
      console.error(
        'Failed to save goal',
        err
      )

      setErrors({
        form:
          'Could not save goal. Please try again.',
      })
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(
    id
  ) {
    setDeletingId(id)

    try {
      await deleteGoal(id)
    } catch (err) {
      console.error(
        'Failed to delete goal',
        err
      )

      setErrors({
        form:
          'Could not delete goal. Please try again.',
      })
    } finally {
      setDeletingId(null)
    }
  }

  async function handleEditSave(
    updates
  ) {
    if (!editingGoal) {
      return
    }

    await updateGoal(
      editingGoal.id,
      updates
    )

    setEditingGoal(null)
  }

  return (
    <AppShell>
      <div className="goals-page">
        <header className="goals-page__header">
          <p className="goals-page__eyebrow">
            Plan your next milestone
          </p>

          <h1>
            Financial goals
          </h1>

          <p>
            Set a target and keep
            the details that matter
            to you in one place.
          </p>
        </header>

        <div className="goals-layout">
          <section
            className="goal-form-card"
            aria-labelledby="new-goal-title"
          >
            <h2 id="new-goal-title">
              Add a goal
            </h2>

            <form
              onSubmit={
                handleSubmit
              }
              className="goal-form"
              noValidate
            >
              <div className="goal-input">
                <label htmlFor="goal">
                  Goal type{' '}
                  <span aria-hidden="true">
                    *
                  </span>
                </label>

                <select
                  id="goal"
                  value={
                    form.goal
                  }
                  onChange={
                    handleChange
                  }
                  required
                  aria-invalid={
                    !!errors.goal
                  }
                >
                  <option value="">
                    Choose a goal type
                  </option>

                  {goalTypes.map(
                    (type) => (
                      <option
                        key={
                          type.id
                        }
                        value={
                          type.id
                        }
                      >
                        {
                          type.goal
                        }
                      </option>
                    )
                  )}

                  <option
                    value={
                      CUSTOM_GOAL_TYPE_ID
                    }
                  >
                    Other / Custom
                  </option>
                </select>

                {errors.goal && (
                  <p role="alert">
                    {
                      errors.goal
                    }
                  </p>
                )}
              </div>

              {isCustomType && (
                <div className="goal-input">
                  <label htmlFor="customGoalType">
                    Custom goal type{' '}
                    <span aria-hidden="true">
                      *
                    </span>
                  </label>

                  <input
                    id="customGoalType"
                    value={
                      form.customGoalType
                    }
                    onChange={
                      handleChange
                    }
                    maxLength="80"
                    placeholder="e.g. Wedding, Business, Travel"
                    required
                    aria-invalid={
                      !!errors.customGoalType
                    }
                    autoFocus
                  />

                  {errors.customGoalType && (
                    <p role="alert">
                      {
                        errors.customGoalType
                      }
                    </p>
                  )}
                </div>
              )}

              <div className="goal-input">
                <label htmlFor="name">
                  Goal name{' '}
                  <span aria-hidden="true">
                    *
                  </span>
                </label>

                <input
                  id="name"
                  value={
                    form.name
                  }
                  onChange={
                    handleChange
                  }
                  maxLength="150"
                  placeholder="e.g. Emergency fund"
                  required
                  aria-invalid={
                    !!errors.name
                  }
                />

                {errors.name && (
                  <p role="alert">
                    {
                      errors.name
                    }
                  </p>
                )}
              </div>

              <div className="goal-input">
                <label htmlFor="target">
                  Target amount{' '}
                  <span aria-hidden="true">
                    *
                  </span>
                </label>

                <input
                  id="target"
                  type="number"
                  value={
                    form.target
                  }
                  onChange={
                    handleChange
                  }
                  min="0.01"
                  step="0.01"
                  placeholder="5000.00"
                  required
                  aria-invalid={
                    !!errors.target
                  }
                />

                {errors.target && (
                  <p role="alert">
                    {
                      errors.target
                    }
                  </p>
                )}
              </div>

              <div className="goal-input">
                <label htmlFor="notes">
                  Notes{' '}
                  <small>
                    Optional
                  </small>
                </label>

                <textarea
                  id="notes"
                  value={
                    form.notes
                  }
                  onChange={
                    handleChange
                  }
                  rows="4"
                  placeholder="Add a timeline, motivation, or other details"
                />
              </div>

              {errors.form && (
                <p role="alert">
                  {errors.form}
                </p>
              )}

              <button
                type="submit"
                disabled={saving}
              >
                {saving
                  ? 'Saving…'
                  : 'Save goal'}
              </button>
            </form>
          </section>

          <section
            className="saved-goals"
            aria-labelledby="saved-goals-title"
          >
            <h2 id="saved-goals-title">
              Your goals
            </h2>

            {loading ? (
              <div className="saved-goals__empty">
                Loading goals…
              </div>
            ) : goals.length ===
              0 ? (
              <div className="saved-goals__empty">
                Your saved goals
                will appear here.
              </div>
            ) : (
              goals.map(
                (goal) => (
                  <article
                    className="saved-goal"
                    key={
                      goal.id
                    }
                  >
                    <div>
                      <span className="saved-goal__type">
                        {
                          goal.goal_name
                        }
                      </span>

                      <h3>
                        {goal.name}
                      </h3>

                      <strong>
                        {formatMoney(
                          goal.target
                        )}
                      </strong>

                      {goal.current >
                        0 && (
                        <p>
                          Saved:{' '}
                          {formatMoney(
                            goal.current
                          )}
                        </p>
                      )}

                      {goal.notes && (
                        <p>
                          {
                            goal.notes
                          }
                        </p>
                      )}
                    </div>

                    <div className="saved-goal__actions">
                      <button
                        type="button"
                        className="saved-goal__edit-btn"
                        onClick={() =>
                          setEditingGoal(
                            goal
                          )
                        }
                        aria-label={`Edit ${goal.name}`}
                      >
                        Edit
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          handleDelete(
                            goal.id
                          )
                        }
                        disabled={
                          deletingId ===
                          goal.id
                        }
                        aria-label={`Delete ${goal.name}`}
                      >
                        {deletingId ===
                        goal.id
                          ? 'Deleting…'
                          : 'Delete'}
                      </button>
                    </div>
                  </article>
                )
              )
            )}
          </section>
        </div>
      </div>

      {editingGoal && (
        <EditGoalModal
          goal={
            editingGoal
          }
          onSave={
            handleEditSave
          }
          onClose={() =>
            setEditingGoal(
              null
            )
          }
        />
      )}
    </AppShell>
  )
}