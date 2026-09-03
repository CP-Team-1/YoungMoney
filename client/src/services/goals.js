import api from './api'

export async function getGoalTypes() {
  const { data } = await api.get('/goals/types/')
  return data
}

export async function getGoals() {
  const { data } = await api.get('/goals/')
  return data
}

export async function createGoal(goal) {
  const { data } = await api.post('/goals/', goal)
  return data
}

export async function deleteGoal(id) {
  await api.delete(`/goals/${id}/`)
}
