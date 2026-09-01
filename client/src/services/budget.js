// MOCK — no backend endpoint yet
import { mockBudget } from '../data/mockBudget'

export async function getBudget() {
  return mockBudget
}

export async function updateBudget(updated) {
  return { ...mockBudget, ...updated }
}
