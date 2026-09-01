import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import FormField from '../components/FormField'
import ErrorMessage from '../components/ErrorMessage'
import './AuthPage.css'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.id]: e.target.value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    try {
      await register(form)
      navigate('/onboarding/goals')
    } catch (err) {
      const msg = err?.response?.data
      if (msg?.email) setError(`Email: ${msg.email[0]}`)
      else if (msg?.password) setError(`Password: ${msg.password[0]}`)
      else setError('Could not create account. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <Link to="/" className="auth-logo">
          <span className="auth-logo__mark">Y</span>
          <span className="auth-logo__text serif">YoungMoney</span>
        </Link>
        <h1 className="auth-heading">Create your account</h1>
        <p className="auth-sub">Free forever. No credit card required.</p>

        {error && <ErrorMessage message={error} />}

        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          <div className="auth-form__row">
            <FormField
              id="first_name"
              label="First name"
              value={form.first_name}
              onChange={handleChange}
              placeholder="Jane"
              required
            />
            <FormField
              id="last_name"
              label="Last name"
              value={form.last_name}
              onChange={handleChange}
              placeholder="Doe"
            />
          </div>
          <FormField
            id="email"
            label="Email"
            type="email"
            value={form.email}
            onChange={handleChange}
            placeholder="you@example.com"
            required
          />
          <FormField
            id="password"
            label="Password"
            type="password"
            value={form.password}
            onChange={handleChange}
            placeholder="At least 8 characters"
            required
            hint="Minimum 8 characters"
          />
          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account?{' '}
          <Link to="/login" className="auth-switch__link">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
