import { createContext, useCallback, useContext, useState } from 'react'

const GoalsContext = createContext(null)

// backend integration point: replace with GET /api/goals/types/
// Custom goal type note for backend developer: the 'custom' sentinel is frontend-only.
// When persisting, the backend will need either a free-text goal_type field or a
// dedicated "Other" GoalType record that allows a user-supplied label.
export const CUSTOM_GOAL_TYPE_ID = 'custom'

const GOAL_TYPES = [
  { id: 1, goal: 'Emergency Fund', is_savings: true },
  { id: 2, goal: 'Savings', is_savings: true },
  { id: 3, goal: 'First Home', is_savings: false },
  { id: 4, goal: 'New Car', is_savings: false },
  { id: 5, goal: 'Vacation', is_savings: false },
  { id: 6, goal: 'Debt Payoff', is_savings: false },
  { id: 7, goal: 'Investment', is_savings: false },
  { id: 8, goal: 'Education', is_savings: false },
]

let nextGoalId = 1

export function GoalsProvider({ children }) {
  // backend integration point: initialize from GET /api/goals/ and persist mutations
  const [goals, setGoals] = useState([])

  const addGoal = useCallback(({ goal: goalTypeId, name, target, notes = '', customGoalType = '' }) => {
    const isCustom = goalTypeId === CUSTOM_GOAL_TYPE_ID
    const type = isCustom ? null : GOAL_TYPES.find((t) => t.id === Number(goalTypeId))
    const newGoal = {
      id: nextGoalId++,
      goal: isCustom ? CUSTOM_GOAL_TYPE_ID : Number(goalTypeId),
      goal_name: isCustom ? customGoalType.trim() : (type?.goal ?? 'Goal'),
      is_savings: isCustom ? false : (type?.is_savings ?? false),
      name,
      target: parseFloat(target),
      notes,
      current: 0,
    }
    setGoals((prev) => [...prev, newGoal].sort((a, b) => a.name.localeCompare(b.name)))
    return newGoal
  }, [])

  const deleteGoal = useCallback((id) => {
    setGoals((prev) => prev.filter((g) => g.id !== id))
  }, [])

  // backend integration point: persist via PATCH /api/goals/:id/ { current }
  const addToGoal = useCallback((id, amount) => {
    setGoals((prev) =>
      prev.map((g) =>
        g.id === id
          ? { ...g, current: Math.round((g.current + amount) * 100) / 100 }
          : g
      )
    )
  }, [])

  const withdrawFromGoal = useCallback((id, amount) => {
    setGoals((prev) =>
      prev.map((g) =>
        g.id === id
          ? { ...g, current: Math.round(Math.max(0, g.current - amount) * 100) / 100 }
          : g
      )
    )
  }, [])

  const updateGoalTarget = useCallback((id, target) => {
    setGoals((prev) =>
      prev.map((g) => (g.id === id ? { ...g, target: parseFloat(target) } : g))
    )
  }, [])

  // backend integration point: persist via PATCH /api/goals/:id/
  const updateGoal = useCallback((id, updates) => {
    setGoals((prev) =>
      prev.map((g) => {
        if (g.id !== id) return g
        return {
          ...g,
          ...updates,
          target: updates.target !== undefined ? parseFloat(updates.target) : g.target,
        }
      })
    )
  }, [])

  return (
    <GoalsContext.Provider
      value={{
        goals,
        goalTypes: GOAL_TYPES,
        addGoal,
        deleteGoal,
        addToGoal,
        withdrawFromGoal,
        updateGoalTarget,
        updateGoal,
      }}
    >
      {children}
    </GoalsContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useGoals() {
  const ctx = useContext(GoalsContext)
  if (!ctx) throw new Error('useGoals must be used inside GoalsProvider')
  return ctx
}
