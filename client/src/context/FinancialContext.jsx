import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import * as budgetService from '../services/budget'
import * as spendingService from '../services/spending'

const FinancialContext = createContext(null)

let nextTempId = 1

export function FinancialProvider({ children }) {
  const [transactions, setTransactions] = useState([])
  const [income, setIncome] = useState(0)
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  // null = no goal created yet; backend integration point: replace with GET /api/savings-goal/
  const [savingsGoal, setSavingsGoalState] = useState(null)

  useEffect(() => {
    Promise.all([
      budgetService.getIncome(),
      budgetService.getBudgetCategories(),
      spendingService.getTransactions(),
    ])
      .then(([incomeVal, cats, txs]) => {
        setIncome(incomeVal)
        setCategories(cats)
        setTransactions(txs)
      })
      .catch((err) => {
        console.error('Failed to load financial data', err)
      })
      .finally(() => setLoading(false))
  }, [])

  const totalSpent = transactions.reduce((s, tx) => s + tx.amount, 0)
  const totalAllocated = categories.reduce((s, c) => s + c.allocated, 0)
  const remaining = income - totalSpent

  const budgetCategories = categories.map((cat) => ({
    ...cat,
    spent: Math.round(transactions.filter((tx) => tx.category === cat.id).reduce((s, tx) => s + tx.amount, 0) * 100) / 100,
  }))

  const addTransaction = useCallback(async (tx) => {
    const tempId = `temp-${nextTempId++}`
    const optimisticTx = { id: tempId, ...tx, amount: parseFloat(tx.amount) }
    setTransactions((prev) => [...prev, optimisticTx].sort((a, b) => b.date.localeCompare(a.date)))
    try {
      const created = await spendingService.addTransaction(tx)
      setTransactions((prev) =>
        prev.map((t) => (t.id === tempId ? created : t)).sort((a, b) => b.date.localeCompare(a.date))
      )
    } catch (err) {
      setTransactions((prev) => prev.filter((t) => t.id !== tempId))
      throw err
    }
  }, [])

  const updateTransaction = useCallback(async (id, updates) => {
    let prevTx
    setTransactions((prev) =>
      prev.map((tx) => {
        if (tx.id !== id) return tx
        prevTx = tx
        return { ...tx, ...updates, amount: parseFloat(updates.amount ?? tx.amount) }
      })
    )
    try {
      const updated = await spendingService.updateTransaction(id, updates)
      setTransactions((prev) => prev.map((tx) => (tx.id === id ? updated : tx)).sort((a, b) => b.date.localeCompare(a.date)))
    } catch (err) {
      if (prevTx) setTransactions((prev) => prev.map((tx) => (tx.id === id ? prevTx : tx)))
      throw err
    }
  }, [])

  const deleteTransaction = useCallback(async (id) => {
    let removed
    setTransactions((prev) => {
      removed = prev.find((tx) => tx.id === id)
      return prev.filter((tx) => tx.id !== id)
    })
    try {
      await spendingService.deleteTransaction(id)
    } catch (err) {
      if (removed) setTransactions((prev) => [...prev, removed].sort((a, b) => b.date.localeCompare(a.date)))
      throw err
    }
  }, [])

  const clearTransactions = useCallback(async () => {
    let prevTransactions
    setTransactions((prev) => {
      prevTransactions = prev
      return []
    })
    try {
      await spendingService.clearTransactions()
    } catch (err) {
      setTransactions(prevTransactions)
      throw err
    }
  }, [])

  const updateIncome = useCallback(async (amount) => {
    let prevIncome
    setIncome((prev) => {
      prevIncome = prev
      return parseFloat(amount)
    })
    try {
      const updated = await budgetService.updateIncome(amount)
      setIncome(updated)
    } catch (err) {
      setIncome(prevIncome)
      throw err
    }
  }, [])

  const addBudgetCategory = useCallback(async (cat) => {
    const tempId = `temp-${nextTempId++}`
    const optimisticCat = { id: tempId, label: cat.label, allocated: parseFloat(cat.allocated), color: cat.color }
    setCategories((prev) => [...prev, optimisticCat])
    try {
      const created = await budgetService.addBudgetCategory(cat)
      setCategories((prev) => prev.map((c) => (c.id === tempId ? created : c)))
    } catch (err) {
      setCategories((prev) => prev.filter((c) => c.id !== tempId))
      throw err
    }
  }, [])

  const updateBudgetCategory = useCallback(async (id, updates) => {
    let prevCat
    setCategories((prev) =>
      prev.map((cat) => {
        if (cat.id !== id) return cat
        prevCat = cat
        return { ...cat, ...updates, allocated: parseFloat(updates.allocated ?? cat.allocated) }
      })
    )
    try {
      const updated = await budgetService.updateBudgetCategory(id, updates)
      setCategories((prev) => prev.map((cat) => (cat.id === id ? updated : cat)))
    } catch (err) {
      if (prevCat) setCategories((prev) => prev.map((cat) => (cat.id === id ? prevCat : cat)))
      throw err
    }
  }, [])

  const deleteBudgetCategory = useCallback(async (id) => {
    let removed
    setCategories((prev) => {
      removed = prev.find((cat) => cat.id === id)
      return prev.filter((cat) => cat.id !== id)
    })
    try {
      await budgetService.deleteBudgetCategory(id)
    } catch (err) {
      if (removed) setCategories((prev) => [...prev, removed])
      throw err
    }
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
        loading,
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
