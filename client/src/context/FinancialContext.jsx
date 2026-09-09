import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from 'react'

import * as budgetService from '../services/budget'
import * as spendingService from '../services/spending'
import { useAuth } from './AuthContext'

const FinancialContext = createContext(null)

let nextTempId = 1

function normalizeCategoryLabel(value) {
  return String(value ?? '')
    .trim()
    .toLowerCase()
    .replace(/&/g, ' and ')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
    .replace(/\s+/g, '-')
}

function findMatchingBudgetCategory(categoryValue, categories) {
  if (!categoryValue) {
    return null
  }

  const rawValue = String(categoryValue).trim()

  // First: exact internal key match.
  //
  // This preserves transactions that were explicitly linked to a
  // budget category by its backend key.
  const exactKeyMatch = categories.find(
    (category) => category.id === rawValue
  )

  if (exactKeyMatch) {
    return exactKeyMatch
  }

  // Second: visible-name match.
  //
  // This lets a custom Spend Log category such as "Pet Food"
  // automatically connect to a later-created Budget category
  // named "Pet Food".
  const normalizedValue =
    normalizeCategoryLabel(rawValue)

  return (
    categories.find(
      (category) =>
        normalizeCategoryLabel(category.label) ===
        normalizedValue
    ) ?? null
  )
}

export function FinancialProvider({ children }) {
  const { user } = useAuth()

  const [transactions, setTransactions] =
    useState([])

  const [income, setIncome] =
    useState(0)

  const [categories, setCategories] =
    useState([])

  const [loading, setLoading] = useState(
    () =>
      !!localStorage.getItem(
        'access_token'
      )
  )

  const [
    savingsGoal,
    setSavingsGoalState,
  ] = useState(null)

  useEffect(() => {
    if (!user) {
      return
    }

    setLoading(true)

    Promise.all([
      budgetService.getIncome(),
      budgetService.getBudgetCategories(),
      spendingService.getTransactions(),
    ])
      .then(
        ([
          incomeVal,
          cats,
          txs,
        ]) => {
          setIncome(incomeVal)
          setCategories(cats)
          setTransactions(txs)
        }
      )
      .catch((err) => {
        console.error(
          'Failed to load financial data',
          err
        )
      })
      .finally(() => {
        setLoading(false)
      })
  }, [user])

  const resolveBudgetCategory =
    useCallback(
      (categoryValue) =>
        findMatchingBudgetCategory(
          categoryValue,
          categories
        ),
      [categories]
    )

  const totalSpent =
    transactions.reduce(
      (sum, transaction) =>
        sum + transaction.amount,
      0
    )

  const totalAllocated =
    categories.reduce(
      (sum, category) =>
        sum + category.allocated,
      0
    )

  const remaining =
    income - totalSpent

  const budgetCategories =
    categories.map((category) => {
      const spent =
        transactions
          .filter((transaction) => {
            const matched =
              findMatchingBudgetCategory(
                transaction.category,
                categories
              )

            return (
              matched?.id ===
              category.id
            )
          })
          .reduce(
            (sum, transaction) =>
              sum +
              transaction.amount,
            0
          )

      return {
        ...category,
        spent:
          Math.round(
            spent * 100
          ) / 100,
      }
    })

  const addTransaction =
    useCallback(async (tx) => {
      const tempId =
        `temp-${nextTempId++}`

      const optimisticTx = {
        id: tempId,
        ...tx,
        amount: parseFloat(
          tx.amount
        ),
      }

      setTransactions(
        (prev) =>
          [
            ...prev,
            optimisticTx,
          ].sort(
            (a, b) =>
              b.date.localeCompare(
                a.date
              )
          )
      )

      try {
        const created =
          await spendingService
            .addTransaction(tx)

        setTransactions(
          (prev) =>
            prev
              .map((transaction) =>
                transaction.id ===
                tempId
                  ? created
                  : transaction
              )
              .sort(
                (a, b) =>
                  b.date.localeCompare(
                    a.date
                  )
              )
        )
      } catch (err) {
        setTransactions(
          (prev) =>
            prev.filter(
              (transaction) =>
                transaction.id !==
                tempId
            )
        )

        throw err
      }
    }, [])

  const updateTransaction =
    useCallback(
      async (id, updates) => {
        let previousTransaction

        setTransactions(
          (prev) =>
            prev.map(
              (transaction) => {
                if (
                  transaction.id !==
                  id
                ) {
                  return transaction
                }

                previousTransaction =
                  transaction

                return {
                  ...transaction,
                  ...updates,
                  amount: parseFloat(
                    updates.amount ??
                      transaction.amount
                  ),
                }
              }
            )
        )

        try {
          const updated =
            await spendingService
              .updateTransaction(
                id,
                updates
              )

          setTransactions(
            (prev) =>
              prev
                .map(
                  (transaction) =>
                    transaction.id ===
                    id
                      ? updated
                      : transaction
                )
                .sort(
                  (a, b) =>
                    b.date.localeCompare(
                      a.date
                    )
                )
          )
        } catch (err) {
          if (
            previousTransaction
          ) {
            setTransactions(
              (prev) =>
                prev.map(
                  (transaction) =>
                    transaction.id ===
                    id
                      ? previousTransaction
                      : transaction
                )
            )
          }

          throw err
        }
      },
      []
    )

  const deleteTransaction =
    useCallback(async (id) => {
      let removed

      setTransactions(
        (prev) => {
          removed = prev.find(
            (transaction) =>
              transaction.id === id
          )

          return prev.filter(
            (transaction) =>
              transaction.id !== id
          )
        }
      )

      try {
        await spendingService
          .deleteTransaction(id)
      } catch (err) {
        if (removed) {
          setTransactions(
            (prev) =>
              [
                ...prev,
                removed,
              ].sort(
                (a, b) =>
                  b.date.localeCompare(
                    a.date
                  )
              )
          )
        }

        throw err
      }
    }, [])

  const clearTransactions =
    useCallback(async () => {
      let previousTransactions

      setTransactions(
        (prev) => {
          previousTransactions =
            prev

          return []
        }
      )

      try {
        await spendingService
          .clearTransactions()
      } catch (err) {
        setTransactions(
          previousTransactions
        )

        throw err
      }
    }, [])

  const updateIncome =
    useCallback(
      async (amount) => {
        let previousIncome

        setIncome((prev) => {
          previousIncome = prev

          return parseFloat(
            amount
          )
        })

        try {
          const updated =
            await budgetService
              .updateIncome(
                amount
              )

          setIncome(updated)
        } catch (err) {
          setIncome(
            previousIncome
          )

          throw err
        }
      },
      []
    )

  const addBudgetCategory =
    useCallback(
      async (category) => {
        const tempId =
          `temp-${nextTempId++}`

        const optimisticCategory = {
          id: tempId,
          label: category.label,
          allocated: parseFloat(
            category.allocated
          ),
          color: category.color,
        }

        setCategories(
          (prev) => [
            ...prev,
            optimisticCategory,
          ]
        )

        try {
          const created =
            await budgetService
              .addBudgetCategory(
                category
              )

          setCategories(
            (prev) =>
              prev.map(
                (existing) =>
                  existing.id ===
                  tempId
                    ? created
                    : existing
              )
          )
        } catch (err) {
          setCategories(
            (prev) =>
              prev.filter(
                (existing) =>
                  existing.id !==
                  tempId
              )
          )

          throw err
        }
      },
      []
    )

  const updateBudgetCategory =
    useCallback(
      async (id, updates) => {
        let previousCategory

        setCategories(
          (prev) =>
            prev.map(
              (category) => {
                if (
                  category.id !==
                  id
                ) {
                  return category
                }

                previousCategory =
                  category

                return {
                  ...category,
                  ...updates,
                  allocated:
                    parseFloat(
                      updates.allocated ??
                        category.allocated
                    ),
                }
              }
            )
        )

        try {
          const updated =
            await budgetService
              .updateBudgetCategory(
                id,
                updates
              )

          setCategories(
            (prev) =>
              prev.map(
                (category) =>
                  category.id ===
                  id
                    ? updated
                    : category
              )
          )
        } catch (err) {
          if (
            previousCategory
          ) {
            setCategories(
              (prev) =>
                prev.map(
                  (category) =>
                    category.id ===
                    id
                      ? previousCategory
                      : category
                )
            )
          }

          throw err
        }
      },
      []
    )

  const deleteBudgetCategory =
    useCallback(
      async (id) => {
        let removed

        setCategories(
          (prev) => {
            removed = prev.find(
              (category) =>
                category.id === id
            )

            return prev.filter(
              (category) =>
                category.id !== id
            )
          }
        )

        try {
          await budgetService
            .deleteBudgetCategory(
              id
            )
        } catch (err) {
          if (removed) {
            setCategories(
              (prev) => [
                ...prev,
                removed,
              ]
            )
          }

          throw err
        }
      },
      []
    )

  const createSavingsGoal =
    useCallback(
      ({
        label,
        target,
      }) => {
        setSavingsGoalState({
          label,
          target:
            parseFloat(target),
          current: 0,
        })
      },
      []
    )

  const updateSavingsGoal =
    useCallback(
      (updates) => {
        setSavingsGoalState(
          (prev) => ({
            ...(prev ?? {}),
            ...updates,
          })
        )
      },
      []
    )

  const addToSavings =
    useCallback(
      (amount) => {
        setSavingsGoalState(
          (prev) => ({
            ...prev,
            current:
              Math.round(
                (
                  prev.current +
                  amount
                ) * 100
              ) / 100,
          })
        )
      },
      []
    )

  const withdrawFromSavings =
    useCallback(
      (amount) => {
        setSavingsGoalState(
          (prev) => ({
            ...prev,
            current:
              Math.round(
                Math.max(
                  0,
                  prev.current -
                    amount
                ) * 100
              ) / 100,
          })
        )
      },
      []
    )

  return (
    <FinancialContext.Provider
      value={{
        loading,
        transactions,
        income,
        categories:
          budgetCategories,
        savingsGoal,
        totalSpent,
        totalAllocated,
        remaining,
        resolveBudgetCategory,
        addTransaction,
        updateTransaction,
        deleteTransaction,
        clearTransactions,
        updateIncome,
        addBudgetCategory,
        updateBudgetCategory,
        deleteBudgetCategory,
        createSavingsGoal,
        updateSavingsGoal,
        addToSavings,
        withdrawFromSavings,
      }}
    >
      {children}
    </FinancialContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useFinancial() {
  const ctx =
    useContext(
      FinancialContext
    )

  if (!ctx) {
    throw new Error(
      'useFinancial must be used inside FinancialProvider'
    )
  }

  return ctx
}