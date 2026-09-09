import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '../components/AppShell'
import DashboardCard from '../components/DashboardCard'
import GoalMeter from '../components/GoalMeter'
import ProgressBar from '../components/ProgressBar'
import ExpenseEntry from '../components/ExpenseEntry'
import { useAuth } from '../context/AuthContext'
import { useFinancial } from '../context/FinancialContext'
import { useGoals } from '../context/GoalsContext'
import { useLearning } from '../context/LearningContext'
import { learningHubArticles } from '../features/learningHub'
import { formatMoney } from '../utils/money'
import './Dashboard.css'

const TOTAL_ARTICLES =
  learningHubArticles.length

const UNCATEGORIZED_COLOR =
  '#6b5f54'

const STANDARD_CATEGORY_LABELS = {
  groceries: 'Groceries',
  transport: 'Transport',
  housing: 'Housing',
  utilities: 'Utilities',
  subscriptions: 'Subscriptions',
  fun: 'Fun',
  savings: 'Savings',
  other: 'Other',
}

function displayCategoryLabel(value) {
  if (
    STANDARD_CATEGORY_LABELS[
      value
    ]
  ) {
    return (
      STANDARD_CATEGORY_LABELS[
        value
      ]
    )
  }

  return String(value ?? '')
    .replace(/[-_]+/g, ' ')
    .replace(
      /\b\w/g,
      (letter) =>
        letter.toUpperCase()
    )
}

function SpendingDonut({
  categories,
  transactions,
  totalSpent,
  resolveBudgetCategory,
}) {
  const uncategorizedSpent =
    transactions.reduce(
      (sum, transaction) =>
        resolveBudgetCategory(
          transaction.category
        )
          ? sum
          : sum +
            transaction.amount,
      0
    )

  const slices = [
    ...categories.filter(
      (category) =>
        category.spent > 0
    ),
    ...(uncategorizedSpent >
    0
      ? [
          {
            id: '__uncategorized__',
            label:
              'Uncategorized',
            spent:
              uncategorizedSpent,
            color:
              UNCATEGORIZED_COLOR,
          },
        ]
      : []),
  ]

  if (totalSpent <= 0) {
    return (
      <div className="spend-donut spend-donut--empty">
        <div className="spend-donut__ring spend-donut__ring--empty">
          <div className="spend-donut__hole">
            <span className="spend-donut__total">
              {formatMoney(
                0
              )}
            </span>

            <span className="spend-donut__center-label">
              spent
            </span>
          </div>
        </div>

        <p className="spend-donut__empty-msg">
          No spending data yet.
        </p>
      </div>
    )
  }

  let cumulative = 0

  const computedSlices =
    slices.map(
      (slice) => {
        const pct =
          (slice.spent /
            totalSpent) *
          100

        const start =
          cumulative

        cumulative += pct

        return {
          ...slice,
          pct,
          start,
          end: cumulative,
        }
      }
    )

  const gradient =
    `conic-gradient(${computedSlices
      .map(
        (slice) =>
          `${slice.color} ${slice.start.toFixed(
            2
          )}% ${slice.end.toFixed(
            2
          )}%`
      )
      .join(', ')})`

  return (
    <div className="spend-donut">
      <div
        className="spend-donut__ring"
        style={{
          background:
            gradient,
        }}
      >
        <div className="spend-donut__hole">
          <span className="spend-donut__total">
            {formatMoney(
              totalSpent
            )}
          </span>

          <span className="spend-donut__center-label">
            spent
          </span>
        </div>
      </div>

      <div className="spend-donut__legend">
        {computedSlices.map(
          (slice) => (
            <div
              key={
                slice.id
              }
              className="spend-donut__legend-row"
            >
              <span
                className="spend-donut__legend-dot"
                style={{
                  background:
                    slice.color,
                }}
              />

              <span className="spend-donut__legend-name">
                {
                  slice.label
                }
              </span>

              <span className="spend-donut__legend-amt">
                {formatMoney(
                  slice.spent
                )}
              </span>

              <span className="spend-donut__legend-pct">
                {Math.round(
                  slice.pct
                )}
                %
              </span>
            </div>
          )
        )}
      </div>
    </div>
  )
}

function SavingsModal({
  action,
  goal,
  onSave,
  onClose,
}) {
  const [
    amount,
    setAmount,
  ] = useState('')

  const [
    error,
    setError,
  ] = useState('')

  const isTarget =
    action ===
    'edit-target'

  const TITLES = {
    add: '+ Add Money',
    withdraw:
      '− Withdraw',
    'edit-target':
      'Edit Goal Target',
  }

  function validate() {
    const val =
      parseFloat(amount)

    if (
      !amount ||
      isNaN(val) ||
      val <= 0
    ) {
      return 'Enter a positive amount'
    }

    if (
      action ===
        'withdraw' &&
      val > goal.current
    ) {
      return `Cannot withdraw more than your current balance of ${formatMoney(
        goal.current
      )}`
    }

    return null
  }

  function handleSubmit(ev) {
    ev.preventDefault()

    const err =
      validate()

    if (err) {
      setError(err)
      return
    }

    onSave(
      parseFloat(amount)
    )
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
          {TITLES[action]}
        </h2>

        <div className="savings-modal__context">
          <span className="savings-modal__context-label">
            {isTarget
              ? 'Current target'
              : 'Currently saved'}
          </span>

          <span className="savings-modal__context-val">
            {isTarget
              ? formatMoney(
                  goal.target
                )
              : formatMoney(
                  goal.current
                )}
          </span>
        </div>

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
              htmlFor="savings-amount"
            >
              {isTarget
                ? 'New target ($)'
                : 'Amount ($)'}
            </label>

            <input
              className="sl-field__input"
              id="savings-amount"
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(e) => {
                setAmount(
                  e.target.value
                )
                setError('')
              }}
              placeholder="0.00"
              autoFocus
            />

            {error && (
              <p className="sl-field__error">
                {error}
              </p>
            )}
          </div>

          <div className="sl-modal__actions">
            <button
              type="submit"
              className="sl-btn sl-btn--primary"
            >
              {isTarget
                ? 'Update Target'
                : action ===
                    'add'
                  ? 'Add to Savings'
                  : 'Withdraw'}
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

function GoalCard({
  goal,
  onSavingsAction,
}) {
  const toGo =
    Math.max(
      0,
      goal.target -
        goal.current
    )

  return (
    <div className="dash-goal-card dash-goal-card--savings">
      <span className="dash-goal-card__type">
        {goal.goal_name}
      </span>

      <GoalMeter
        label={goal.name}
        current={
          goal.current
        }
        target={
          goal.target
        }
      />

      <p className="dash-goal-card__hint">
        {toGo > 0
          ? `${formatMoney(
              toGo
            )} to go`
          : 'Goal reached! 🎉'}
      </p>

      <div className="dash-goal__controls">
        <button
          type="button"
          className="dash-goal__btn dash-goal__btn--add"
          onClick={() =>
            onSavingsAction(
              'add',
              goal.id
            )
          }
        >
          + Add Money
        </button>

        <button
          type="button"
          className="dash-goal__btn dash-goal__btn--withdraw"
          onClick={() =>
            onSavingsAction(
              'withdraw',
              goal.id
            )
          }
          disabled={
            goal.current <=
            0
          }
        >
          − Withdraw
        </button>
      </div>

      <button
        type="button"
        className="dash-goal__edit-target"
        onClick={() =>
          onSavingsAction(
            'edit-target',
            goal.id
          )
        }
      >
        Edit target
      </button>
    </div>
  )
}

function BudgetPromptModal({
  onSetBudget,
  onDismiss,
}) {
  return (
    <div
      className="sl-modal-overlay"
      onClick={
        onDismiss
      }
    >
      <div
        className="sl-modal"
        onClick={(e) =>
          e.stopPropagation()
        }
      >
        <h2 className="sl-modal__title">
          Set Up Your Starting Budget
        </h2>

        <p
          style={{
            color:
              'var(--color-muted)',
            fontSize: 14,
            marginBottom:
              'var(--space-4)',
          }}
        >
          Add your monthly
          budget so YoungMoney
          can help track your
          spending and progress.
        </p>

        <div className="sl-modal__actions">
          <button
            type="button"
            className="sl-btn sl-btn--primary"
            onClick={
              onSetBudget
            }
          >
            Set My Budget
          </button>

          <button
            type="button"
            className="sl-btn sl-btn--ghost"
            onClick={
              onDismiss
            }
          >
            Maybe Later
          </button>
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user } =
    useAuth()

  const navigate =
    useNavigate()

  const {
    income,
    totalSpent,
    transactions,
    categories,
    resolveBudgetCategory,
    loading:
      financialLoading,
  } = useFinancial()

  const {
    goals,
    addToGoal,
    withdrawFromGoal,
    updateGoalTarget,
  } = useGoals()

  const {
    lessons,
    completedArticleIds,
    completedLessonIds,
    quizAttempts,
    resetQuizProgress,
  } = useLearning()

  const [
    savingsAction,
    setSavingsAction,
  ] = useState(null)

  const [
    budgetPromptDismissed,
    setBudgetPromptDismissed,
  ] = useState(false)

  const showBudgetPrompt =
    !budgetPromptDismissed &&
    !financialLoading &&
    income === 0 &&
    categories.length ===
      0

  function handleBudgetSet() {
    setBudgetPromptDismissed(
      true
    )

    navigate('/budget')
  }

  function handleBudgetDismiss() {
    setBudgetPromptDismissed(
      true
    )
  }

  const completedArticlesCount =
    completedArticleIds.size

  const completedLessonsCount =
    completedLessonIds.size

  const attemptedQuizIds =
    Object.keys(
      quizAttempts
    )

  const attemptedQuizzesCount =
    attemptedQuizIds.length

  const nextLesson =
    lessons.find(
      (lesson) =>
        !lesson.completed
    )

  const nextQuiz =
    lessons.find(
      (lesson) =>
        !quizAttempts[
          lesson.id
        ]
    )

  const knowledgeScore =
    attemptedQuizzesCount >
    0
      ? Math.round(
          attemptedQuizIds.reduce(
            (
              sum,
              id
            ) =>
              sum +
              quizAttempts[id]
                .bestScore,
            0
          ) /
            attemptedQuizzesCount
        )
      : null

  function handleResetQuizProgress() {
    if (
      window.confirm(
        'Reset all quiz progress? This clears quiz scores and Knowledge Score. Articles and lessons are not affected.'
      )
    ) {
      resetQuizProgress()
    }
  }

  const recentSpend = [
    ...transactions,
  ]
    .sort((a, b) =>
      b.date.localeCompare(
        a.date
      )
    )
    .slice(0, 5)

  const activeGoal =
    savingsAction
      ? goals.find(
          (goal) =>
            goal.id ===
            savingsAction.goalId
        )
      : null

  const totalGoalCommitted =
    goals.reduce(
      (sum, goal) =>
        sum +
        goal.current,
      0
    )

  const availableAfterGoals =
    income -
    totalSpent -
    totalGoalCommitted

  function handleSavingsAction(
    amount
  ) {
    if (!savingsAction) {
      return
    }

    const {
      type,
      goalId,
    } = savingsAction

    if (type === 'add') {
      addToGoal(
        goalId,
        amount
      )
    } else if (
      type ===
      'withdraw'
    ) {
      withdrawFromGoal(
        goalId,
        amount
      )
    } else if (
      type ===
      'edit-target'
    ) {
      updateGoalTarget(
        goalId,
        amount
      )
    }

    setSavingsAction(null)
  }

  return (
    <AppShell>
      <div className="dashboard">
        <header className="dashboard__header">
          <h1 className="dashboard__greeting">
            Hey
            {user?.first_name
              ? `, ${user.first_name}`
              : ''}{' '}
            👋
          </h1>

          <p className="dashboard__date">
            {new Date().toLocaleDateString(
              'en-US',
              {
                weekday:
                  'long',
                month:
                  'long',
                day: 'numeric',
              }
            )}
          </p>
        </header>

        <div className="dashboard__grid">
          <DashboardCard
            title="This Month"
            accent="orange"
          >
            <div className="dash-summary">
              <div className="dash-summary__stat">
                <span className="dash-summary__value">
                  {formatMoney(
                    income
                  )}
                </span>

                <span className="dash-summary__label">
                  Income
                </span>
              </div>

              <div className="dash-summary__stat">
                <span className="dash-summary__value dash-summary__value--spent">
                  {formatMoney(
                    totalSpent
                  )}
                </span>

                <span className="dash-summary__label">
                  Spent
                </span>
              </div>

              {totalGoalCommitted >
                0 && (
                <div className="dash-summary__stat">
                  <span className="dash-summary__value dash-summary__value--spent">
                    {formatMoney(
                      totalGoalCommitted
                    )}
                  </span>

                  <span className="dash-summary__label">
                    Goals
                  </span>
                </div>
              )}

              <div className="dash-summary__stat">
                <span
                  className={
                    `dash-summary__value${
                      availableAfterGoals <
                      0
                        ? ' dash-summary__value--over'
                        : ' dash-summary__value--left'
                    }`
                  }
                >
                  {formatMoney(
                    Math.abs(
                      availableAfterGoals
                    )
                  )}
                </span>

                <span className="dash-summary__label">
                  {availableAfterGoals <
                  0
                    ? 'Over budget'
                    : 'Available'}
                </span>
              </div>
            </div>

            <ProgressBar
              value={Math.max(
                0,
                availableAfterGoals
              )}
              max={
                income > 0
                  ? income
                  : 1
              }
              color="sage"
              label="Available"
              showPercent
            />
          </DashboardCard>

          <DashboardCard
            title="Spending Breakdown"
            action={() =>
              navigate(
                '/spend'
              )
            }
            actionLabel="View all"
          >
            <SpendingDonut
              categories={
                categories
              }
              transactions={
                transactions
              }
              totalSpent={
                totalSpent
              }
              resolveBudgetCategory={
                resolveBudgetCategory
              }
            />
          </DashboardCard>

          <div className="dashboard__full-row">
            <DashboardCard
              title="Goals"
              action={() =>
                navigate(
                  '/goals'
                )
              }
              actionLabel="Manage goals"
            >
              {goals.length ===
              0 ? (
                <div className="dash-goals__empty">
                  <p className="dash-goals__empty-label">
                    No goals yet
                  </p>

                  <p className="dash-goals__empty-hint">
                    Create your
                    first financial
                    goal to start
                    tracking your
                    progress.
                  </p>

                  <button
                    type="button"
                    className="dash-goal__create-btn"
                    onClick={() =>
                      navigate(
                        '/goals'
                      )
                    }
                  >
                    + Create a goal
                  </button>
                </div>
              ) : (
                <div className="dash-goals__grid">
                  {goals.map(
                    (
                      goal
                    ) => (
                      <GoalCard
                        key={
                          goal.id
                        }
                        goal={
                          goal
                        }
                        onSavingsAction={(
                          type,
                          goalId
                        ) =>
                          setSavingsAction(
                            {
                              type,
                              goalId,
                            }
                          )
                        }
                      />
                    )
                  )}
                </div>
              )}
            </DashboardCard>
          </div>

          <DashboardCard
            title="Learning"
            action={() =>
              navigate(
                '/learn'
              )
            }
            actionLabel="All lessons"
          >
            <p className="dash-learn__section-label">
              Articles
            </p>

            {completedArticlesCount ===
            0 ? (
              <div className="dash-learn dash-learn--sub">
                <p className="dash-learn__empty">
                  You haven&apos;t
                  read any articles
                  yet.
                </p>

                <button
                  type="button"
                  className="dash-learn__next"
                  onClick={() =>
                    navigate(
                      '/learn'
                    )
                  }
                >
                  Browse articles
                </button>
              </div>
            ) : (
              <div className="dash-learn dash-learn--sub">
                <div className="dash-learn__stat">
                  <span className="dash-learn__num">
                    {
                      completedArticlesCount
                    }
                  </span>

                  <span className="dash-learn__den">
                    {' '}
                    /{' '}
                    {
                      TOTAL_ARTICLES
                    }
                  </span>
                </div>

                <p className="dash-learn__label">
                  articles read
                </p>

                <ProgressBar
                  value={
                    completedArticlesCount
                  }
                  max={
                    TOTAL_ARTICLES
                  }
                  color="sage"
                  showPercent
                />
              </div>
            )}

            <div className="dash-learn__divider" />

            <p className="dash-learn__section-label">
              Lessons
            </p>

            {completedLessonsCount ===
            0 ? (
              <div className="dash-learn dash-learn--sub">
                <p className="dash-learn__empty">
                  You haven&apos;t
                  completed any
                  lessons yet.
                </p>

                <button
                  type="button"
                  className="dash-learn__next"
                  onClick={() =>
                    navigate(
                      '/learn'
                    )
                  }
                >
                  Start your first
                  lesson
                </button>
              </div>
            ) : (
              <div className="dash-learn dash-learn--sub">
                <div className="dash-learn__stat">
                  <span className="dash-learn__num">
                    {
                      completedLessonsCount
                    }
                  </span>

                  <span className="dash-learn__den">
                    {' '}
                    /{' '}
                    {
                      lessons.length
                    }
                  </span>
                </div>

                <p className="dash-learn__label">
                  lessons completed
                </p>

                <ProgressBar
                  value={
                    completedLessonsCount
                  }
                  max={
                    lessons.length
                  }
                  color="sage"
                  showPercent
                />

                {nextLesson && (
                  <button
                    type="button"
                    className="dash-learn__next"
                    onClick={() =>
                      navigate(
                        `/learn/${nextLesson.id}`
                      )
                    }
                  >
                    Continue:{' '}
                    {
                      nextLesson.title
                    }
                  </button>
                )}
              </div>
            )}

            <div className="dash-learn__divider" />

            <p className="dash-learn__section-label">
              Quizzes
            </p>

            {attemptedQuizzesCount ===
            0 ? (
              <div className="dash-learn dash-learn--sub">
                <p className="dash-learn__empty">
                  You haven&apos;t
                  attempted any
                  quizzes yet.
                </p>

                <button
                  type="button"
                  className="dash-learn__next"
                  onClick={() =>
                    navigate(
                      '/learn'
                    )
                  }
                >
                  Take your first
                  quiz
                </button>
              </div>
            ) : (
              <div className="dash-learn dash-learn--sub">
                <div className="dash-learn__stat">
                  <span className="dash-learn__num">
                    {
                      attemptedQuizzesCount
                    }
                  </span>

                  <span className="dash-learn__den">
                    {' '}
                    /{' '}
                    {
                      lessons.length
                    }
                  </span>
                </div>

                <p className="dash-learn__label">
                  unique quizzes
                  attempted
                </p>

                <ProgressBar
                  value={
                    attemptedQuizzesCount
                  }
                  max={
                    lessons.length
                  }
                  color="orange"
                  showPercent
                />

                <div className="dash-iq">
                  <span className="dash-iq__label">
                    Knowledge Score
                  </span>

                  <span className="dash-iq__value">
                    {knowledgeScore !==
                    null
                      ? `${knowledgeScore}%`
                      : '—'}
                  </span>
                </div>

                {nextQuiz && (
                  <button
                    type="button"
                    className="dash-learn__next"
                    onClick={() =>
                      navigate(
                        `/learn/${nextQuiz.id}/quiz`
                      )
                    }
                  >
                    Next quiz:{' '}
                    {
                      nextQuiz.title
                    }
                  </button>
                )}

                <button
                  type="button"
                  className="dash-reset-quiz"
                  onClick={
                    handleResetQuizProgress
                  }
                >
                  Reset quiz progress
                </button>
              </div>
            )}
          </DashboardCard>

          <DashboardCard
            title="Recent Spending"
            action={() =>
              navigate(
                '/spend'
              )
            }
            actionLabel="View all"
          >
            {recentSpend.length ===
            0 ? (
              <p className="dash-spend__empty">
                No transactions yet.
              </p>
            ) : (
              recentSpend.map(
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
                        matchedBudget?.label ??
                        displayCategoryLabel(
                          entry.category
                        )
                      }
                    />
                  )
                }
              )
            )}
          </DashboardCard>
        </div>
      </div>

      {savingsAction &&
        activeGoal && (
        <SavingsModal
          action={
            savingsAction.type
          }
          goal={
            activeGoal
          }
          onSave={
            handleSavingsAction
          }
          onClose={() =>
            setSavingsAction(
              null
            )
          }
        />
      )}

      {showBudgetPrompt && (
        <BudgetPromptModal
          onSetBudget={
            handleBudgetSet
          }
          onDismiss={
            handleBudgetDismiss
          }
        />
      )}
    </AppShell>
  )
}