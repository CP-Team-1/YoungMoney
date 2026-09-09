import api from './api'

export async function getTasks(date) {
  const { data } = await api.get('/wallet/daily-tasks/', { params: { date } })
  return data
}

export async function createTask(title) {
  const { data } = await api.post('/wallet/daily-tasks/', { title })
  return data
}

export async function deleteTask(id) {
  await api.delete(`/wallet/daily-tasks/${id}/`)
}

export async function completeTask(id, date) {
  await api.post(`/wallet/daily-tasks/${id}/complete/`, { date })
}

export async function uncompleteTask(id, date) {
  await api.delete(`/wallet/daily-tasks/${id}/complete/`, { data: { date } })
}

export async function getStreak() {
  const { data } = await api.get('/wallet/daily-tasks/streak/')
  return data.streak
}
