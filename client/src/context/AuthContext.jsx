import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getMe, login as loginService, logout as logoutService, register as registerService } from '../services/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  // Initialize to true only when a token already exists — avoids a synchronous setState in the effect else-branch
  const [loading, setLoading] = useState(() => !!localStorage.getItem('access_token'))

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      getMe()
        .then(setUser)
        .catch(() => {
          logoutService()
          setUser(null)
        })
        .finally(() => setLoading(false))
    }
  }, [])

  const login = useCallback(async (credentials) => {
    await loginService(credentials)
    const me = await getMe()
    setUser(me)
    return me
  }, [])

  const register = useCallback(async (data) => {
    await registerService(data)
    await loginService({ email: data.email, password: data.password })
    const me = await getMe()
    setUser(me)
    return me
  }, [])

  const logout = useCallback(() => {
    logoutService()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
