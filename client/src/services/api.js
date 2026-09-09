import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Serialize token refresh — prevents multiple simultaneous 401s from each attempting
// to refresh with the same (soon-to-be-blacklisted) rotating refresh token.
let refreshing = false
let refreshQueue = []

function drainQueue(err, token) {
  refreshQueue.forEach(({ resolve, reject }) => (err ? reject(err) : resolve(token)))
  refreshQueue = []
}

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config
    if (err.response?.status !== 401 || original._retry) {
      return Promise.reject(err)
    }

    // While a refresh is already in-flight, queue this request and retry when done
    if (refreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject })
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`
        return api(original)
      })
    }

    original._retry = true
    refreshing = true
    const refresh = localStorage.getItem('refresh_token')

    if (!refresh) {
      refreshing = false
      drainQueue(err, null)
      return Promise.reject(err)
    }

    try {
      const { data } = await axios.post('/api/auth/refresh/', { refresh })
      localStorage.setItem('access_token', data.access)
      // Save the rotated refresh token so future refreshes succeed
      if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
      original.headers.Authorization = `Bearer ${data.access}`
      drainQueue(null, data.access)
      refreshing = false
      return api(original)
    } catch (refreshErr) {
      drainQueue(refreshErr, null)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      refreshing = false
      window.location.href = '/login'
      return Promise.reject(refreshErr)
    }
  }
)

export default api
