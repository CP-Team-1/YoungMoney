import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { getMe, login as loginService, logout as logoutService, register as registerService } from '../services/auth'

const AuthContext = createContext(null)

// ─── DEMO MODE (DEV only) ────────────────────────────────────────────────────
// Activated by Demo.jsx via sessionStorage. Never ships to production because
// import.meta.env.DEV is replaced with `false` at build time.
const DEMO_FLAG = 'ym_demo'
const DEMO_USER = { id: 0, email: 'demo@youngmoney.dev', first_name: 'Demo', last_name: 'User' }
const isDemoActive = () => import.meta.env.DEV && sessionStorage.getItem(DEMO_FLAG) === '1'
// ─────────────────────────────────────────────────────────────────────────────

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => isDemoActive() ? DEMO_USER : null)
  // Initialize to true only when a real token exists (skip in demo mode)
  const [loading, setLoading] = useState(() => !isDemoActive() && !!localStorage.getItem('access_token'))

  useEffect(() => {
    if (isDemoActive()) return
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
    if (import.meta.env.DEV) sessionStorage.removeItem(DEMO_FLAG)
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
