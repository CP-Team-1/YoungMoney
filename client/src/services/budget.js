import api from './api'

function mapCategory(row) {
  return { id: row.key, label: row.label, allocated: Number(row.allocated), color: row.color }
}

export async function getIncome() {
  const { data } = await api.get('/wallet/income/')
  return Number(data.amount)
}

export async function updateIncome(amount) {
  const { data } = await api.put('/wallet/income/', { amount })
  return Number(data.amount)
}

export async function getBudgetCategories() {
  const { data } = await api.get('/wallet/budget-categories/')
  return data.map(mapCategory)
}

export async function addBudgetCategory({ label, allocated, color }) {
  const { data } = await api.post('/wallet/budget-categories/', { label, allocated, color })
  return mapCategory(data)
}

export async function updateBudgetCategory(id, updates) {
  const { data } = await api.patch(`/wallet/budget-categories/${id}/`, updates)
  return mapCategory(data)
}

export async function deleteBudgetCategory(id) {
  await api.delete(`/wallet/budget-categories/${id}/`)
}
