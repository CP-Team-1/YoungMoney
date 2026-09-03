// MOCK — no backend endpoint yet
import { mockSpending } from '../data/mockSpending'

export async function getSpending() {
  return mockSpending
}

export async function addExpense(entry) {
  return { id: Date.now(), ...entry }
}
