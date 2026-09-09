import api from './api'

function mapGoal(row) {
  return {
    id: row.id,
    goal: row.goal,
    goal_name:
      row.goal_name,
    custom_goal_type:
      row.custom_goal_type ?? '',
    name: row.name,
    target: Number(
      row.target
    ),
    current: Number(
      row.current ?? 0
    ),
    notes:
      row.notes ?? '',
  }
}

export async function getGoalTypes() {
  const { data } =
    await api.get(
      '/goals/types/'
    )

  return data
}

export async function getGoals() {
  const { data } =
    await api.get(
      '/goals/'
    )

  return data.map(
    mapGoal
  )
}

export async function addGoal(goal) {
  const { data } =
    await api.post(
      '/goals/',
      goal
    )

  return mapGoal(data)
}

export async function updateGoal(
  id,
  updates
) {
  const { data } =
    await api.patch(
      `/goals/${id}/`,
      updates
    )

  return mapGoal(data)
}

export async function deleteGoal(id) {
  await api.delete(
    `/goals/${id}/`
  )
}