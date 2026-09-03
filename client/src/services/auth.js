import api from './api'

export async function register({ email, password, first_name, last_name }) {
  const { data } = await api.post('/auth/register/', { email, password, first_name, last_name })
  return data
}

export async function login({ email, password }) {
  const { data } = await api.post('/auth/login/', { email, password })
  localStorage.setItem('access_token', data.access)
  localStorage.setItem('refresh_token', data.refresh)
  return data
}

export async function getMe() {
  const { data } = await api.get('/auth/me/')
  return data
}

export function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}
