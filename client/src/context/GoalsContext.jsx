import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'

import * as goalService from '../services/goals'
import { useAuth } from './AuthContext'

const GoalsContext =
  createContext(null)

export const CUSTOM_GOAL_TYPE_ID =
  'custom'

function sortGoals(goals) {
  return [...goals].sort(
    (a, b) =>
      a.name.localeCompare(
        b.name
      )
  )
}

function normalizeGoal(goal) {
  return {
    ...goal,
    goal:
      goal.goal === null
        ? CUSTOM_GOAL_TYPE_ID
        : goal.goal,
    target: Number(
      goal.target
    ),
    current: Number(
      goal.current ?? 0
    ),
    notes:
      goal.notes ?? '',
    custom_goal_type:
      goal.custom_goal_type ??
      '',
  }
}

export function GoalsProvider({
  children,
}) {
  const { user } =
    useAuth()

  const [goals, setGoals] =
    useState([])

  const [
    goalTypes,
    setGoalTypes,
  ] = useState([])

  const [
    loading,
    setLoading,
  ] = useState(
    () =>
      !!localStorage.getItem(
        'access_token'
      )
  )

  useEffect(() => {
    if (!user) {
      
      return
    }

    Promise.all([
      goalService.getGoalTypes(),
      goalService.getGoals(),
    ])
      .then(
        ([
          types,
          savedGoals,
        ]) => {
          setGoalTypes(types)

          setGoals(
            sortGoals(
              savedGoals.map(
                normalizeGoal
              )
            )
          )
        }
      )
      .catch((err) => {
        console.error(
          'Failed to load goals',
          err
        )
      })
      .finally(() => {
        setLoading(false)
      })
  }, [user])

  const addGoal =
    useCallback(
      async ({
        goal:
          goalTypeId,
        name,
        target,
        notes = '',
        customGoalType = '',
      }) => {
        const isCustom =
          goalTypeId ===
          CUSTOM_GOAL_TYPE_ID

        const payload =
          isCustom
            ? {
                goal: null,
                custom_goal_type:
                  customGoalType.trim(),
                name:
                  name.trim(),
                target:
                  parseFloat(
                    target
                  ),
                current: 0,
                notes:
                  notes.trim(),
              }
            : {
                goal:
                  Number(
                    goalTypeId
                  ),
                custom_goal_type:
                  '',
                name:
                  name.trim(),
                target:
                  parseFloat(
                    target
                  ),
                current: 0,
                notes:
                  notes.trim(),
              }

        const created =
          normalizeGoal(
            await goalService.addGoal(
              payload
            )
          )

        setGoals(
          (previous) =>
            sortGoals([
              ...previous,
              created,
            ])
        )

        return created
      },
      []
    )

  const deleteGoal =
    useCallback(
      async (id) => {
        let removedGoal

        setGoals(
          (previous) => {
            removedGoal =
              previous.find(
                (goal) =>
                  goal.id === id
              )

            return previous.filter(
              (goal) =>
                goal.id !== id
            )
          }
        )

        try {
          await goalService.deleteGoal(
            id
          )
        } catch (err) {
          if (removedGoal) {
            setGoals(
              (previous) =>
                sortGoals([
                  ...previous,
                  removedGoal,
                ])
            )
          }

          throw err
        }
      },
      []
    )

  const updateGoal =
    useCallback(
      async (
        id,
        updates
      ) => {
        let previousGoal

        const goal =
          goals.find(
            (item) =>
              item.id === id
          )

        if (!goal) {
          return
        }

        const isCustom =
          goal.goal ===
          CUSTOM_GOAL_TYPE_ID

        const payload = {
          ...updates,
        }

        if (
          payload.target !==
          undefined
        ) {
          payload.target =
            parseFloat(
              payload.target
            )
        }

        if (
          payload.current !==
          undefined
        ) {
          payload.current =
            parseFloat(
              payload.current
            )
        }

        if (
          isCustom &&
          payload.goal_name !==
            undefined
        ) {
          payload.custom_goal_type =
            payload.goal_name.trim()

          delete payload.goal_name
        }

        setGoals(
          (previous) =>
            sortGoals(
              previous.map(
                (item) => {
                  if (
                    item.id !==
                    id
                  ) {
                    return item
                  }

                  previousGoal =
                    item

                  return {
                    ...item,
                    ...updates,
                    target:
                      updates.target !==
                      undefined
                        ? parseFloat(
                            updates.target
                          )
                        : item.target,
                    current:
                      updates.current !==
                      undefined
                        ? parseFloat(
                            updates.current
                          )
                        : item.current,
                    goal_name:
                      isCustom &&
                      updates.goal_name
                        ? updates.goal_name
                        : item.goal_name,
                  }
                }
              )
            )
        )

        try {
          const updated =
            normalizeGoal(
              await goalService.updateGoal(
                id,
                payload
              )
            )

          setGoals(
            (previous) =>
              sortGoals(
                previous.map(
                  (item) =>
                    item.id === id
                      ? updated
                      : item
                )
              )
          )

          return updated
        } catch (err) {
          if (previousGoal) {
            setGoals(
              (previous) =>
                sortGoals(
                  previous.map(
                    (item) =>
                      item.id === id
                        ? previousGoal
                        : item
                  )
                )
            )
          }

          throw err
        }
      },
      [goals]
    )

  const addToGoal =
    useCallback(
      async (
        id,
        amount
      ) => {
        const goal =
          goals.find(
            (item) =>
              item.id === id
          )

        if (!goal) {
          return
        }

        const newCurrent =
          Math.round(
            (
              goal.current +
              parseFloat(
                amount
              )
            ) *
              100
          ) / 100

        return updateGoal(
          id,
          {
            current:
              newCurrent,
          }
        )
      },
      [
        goals,
        updateGoal,
      ]
    )

  const withdrawFromGoal =
    useCallback(
      async (
        id,
        amount
      ) => {
        const goal =
          goals.find(
            (item) =>
              item.id === id
          )

        if (!goal) {
          return
        }

        const newCurrent =
          Math.round(
            Math.max(
              0,
              goal.current -
                parseFloat(
                  amount
                )
            ) * 100
          ) / 100

        return updateGoal(
          id,
          {
            current:
              newCurrent,
          }
        )
      },
      [
        goals,
        updateGoal,
      ]
    )

  const updateGoalTarget =
    useCallback(
      async (
        id,
        target
      ) =>
        updateGoal(
          id,
          {
            target:
              parseFloat(
                target
              ),
          }
        ),
      [updateGoal]
    )

  return (
    <GoalsContext.Provider
      value={{
        loading,
        goals,
        goalTypes,
        addGoal,
        deleteGoal,
        updateGoal,
        addToGoal,
        withdrawFromGoal,
        updateGoalTarget,
      }}
    >
      {children}
    </GoalsContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useGoals() {
  const ctx =
    useContext(
      GoalsContext
    )

  if (!ctx) {
    throw new Error(
      'useGoals must be used inside GoalsProvider'
    )
  }

  return ctx
}