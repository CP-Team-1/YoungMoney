import { createContext, useCallback, useContext, useState } from 'react'
import { mockBudget } from '../data/mockBudget'

const FinancialContext = createContext(null)

let nextId = 1

export function FinancialProvider({ children }) {
  const [transactions, setTransactions] = useState([])
  const [income, setIncome] = useState(mockBudget.income)
  const [categories, setCategories] = useState(
    mockBudget.categories.map(({ id, label, allocated, color }) => ({ id, label, allocated, color }))
  )
  // null = no goal created yet; backend integration point: replace with GET /api/savings-goal/
  const [savingsGoal, setSavingsGoalState] = useState(null)

  const totalSpent = transactions.reduce((s, tx) => s + tx.amount, 0)
  const totalAllocated = categories.reduce((s, c) => s + c.allocated, 0)
  const remaining = income - totalSpent

  const budgetCategories = categories.map((cat) => ({
    ...cat,
    spent: Math.round(transactions.filter((tx) => tx.category === cat.id).reduce((s, tx) => s + tx.amount, 0) * 100) / 100,
  }))

  const addTransaction = useCallback((tx) => {
    const newTx = { id: nextId++, ...tx, amount: parseFloat(tx.amount) }
    setTransactions((prev) => [...prev, newTx].sort((a, b) => b.date.localeCompare(a.date)))
  }, [])

  const updateTransaction = useCallback((id, updates) => {
    setTransactions((prev) =>
      prev.map((tx) =>
        tx.id === id
          ? { ...tx, ...updates, amount: parseFloat(updates.amount ?? tx.amount) }
          : tx
      )
    )
  }, [])

  const deleteTransaction = useCallback((id) => {
    setTransactions((prev) => prev.filter((tx) => tx.id !== id))
  }, [])

  const clearTransactions = useCallback(() => {
    setTransactions([])
  }, [])

  const updateIncome = useCallback((amount) => {
    setIncome(parseFloat(amount))
  }, [])

  const addBudgetCategory = useCallback((cat) => {
    const id = cat.label.toLowerCase().replace(/\s+/g, '-')
    setCategories((prev) => [...prev, { id, label: cat.label, allocated: parseFloat(cat.allocated), color: cat.color }])
  }, [])

  const updateBudgetCategory = useCallback((id, updates) => {
    setCategories((prev) =>
      prev.map((cat) =>
        cat.id === id
          ? { ...cat, ...updates, allocated: parseFloat(updates.allocated ?? cat.allocated) }
          : cat
      )
    )
  }, [])

  const deleteBudgetCategory = useCallback((id) => {
    setCategories((prev) => prev.filter((cat) => cat.id !== id))
  }, [])

  // Create the initial savings goal (first-time setup)
  // backend integration point: POST /api/savings-goal/ { label, target }
  const createSavingsGoal = useCallback(({ label, target }) => {
    setSavingsGoalState({ label, target: parseFloat(target), current: 0 })
  }, [])

  const updateSavingsGoal = useCallback((updates) => {
    setSavingsGoalState((prev) => ({ ...(prev ?? {}), ...updates }))
  }, [])

  // Deposit: add amount to current saved balance
  const addToSavings = useCallback((amount) => {
    setSavingsGoalState((prev) => ({
      ...prev,
      current: Math.round((prev.current + amount) * 100) / 100,
    }))
  }, [])

  // Withdrawal: subtract amount, floor at 0
  const withdrawFromSavings = useCallback((amount) => {
    setSavingsGoalState((prev) => ({
      ...prev,
      current: Math.round(Math.max(0, prev.current - amount) * 100) / 100,
    }))
  }, [])

  return (
    <FinancialContext.Provider
      value={{
        transactions,
        income,
        categories: budgetCategories,
        savingsGoal,
        totalSpent,
        totalAllocated,
        remaining,
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
  const ctx = useContext(FinancialContext)
  if (!ctx) throw new Error('useFinancial must be used inside FinancialProvider')
  return ctx
}
