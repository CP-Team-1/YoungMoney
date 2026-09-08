import api from './api'

function mapTransaction(row) {
  return { id: row.id, merchant: row.merchant, category: row.category, amount: Number(row.amount), date: row.date }
}

export async function getTransactions() {
  const { data } = await api.get('/wallet/spend-log/')
  return data.map(mapTransaction)
}

export async function addTransaction(tx) {
  const { data } = await api.post('/wallet/spend-log/', tx)
  return mapTransaction(data)
}

export async function updateTransaction(id, updates) {
  const { data } = await api.patch(`/wallet/spend-log/${id}/`, updates)
  return mapTransaction(data)
}

export async function deleteTransaction(id) {
  await api.delete(`/wallet/spend-log/${id}/`)
}

export async function clearTransactions() {
  await api.delete('/wallet/spend-log/clear/')
}
