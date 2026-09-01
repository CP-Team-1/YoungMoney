import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import FormField from '../components/FormField'
import './Onboarding.css'

export default function IncomeSetup() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ income: '', rent: '', food: '', transport: '' })

  function handleChange(e) {
    setForm((f) => ({ ...f, [e.target.id]: e.target.value }))
  }

  function handleContinue(e) {
    e.preventDefault()
    localStorage.setItem('ym_income', JSON.stringify(form))
    navigate('/dashboard')
  }

  return (
    <div className="onboarding">
      <div className="onboarding__inner">
        <div className="onboarding__step">Step 2 of 2</div>
        <h1 className="onboarding__title">Tell us about your finances</h1>
        <p className="onboarding__sub">
          Rough estimates are fine — you can update these anytime.
        </p>

        <form onSubmit={handleContinue} className="income-form">
          <FormField
            id="income"
            label="Monthly take-home income"
            type="number"
            value={form.income}
            onChange={handleChange}
            placeholder="e.g. 3500"
            hint="After taxes"
          />
          <FormField
            id="rent"
            label="Monthly rent / mortgage"
            type="number"
            value={form.rent}
            onChange={handleChange}
            placeholder="e.g. 1200"
          />
          <FormField
            id="food"
            label="Monthly food spending"
            type="number"
            value={form.food}
            onChange={handleChange}
            placeholder="e.g. 400"
          />
          <FormField
            id="transport"
            label="Monthly transport"
            type="number"
            value={form.transport}
            onChange={handleChange}
            placeholder="e.g. 150"
          />
          <button type="submit" className="onboarding__cta onboarding__cta--active">
            Go to my dashboard
          </button>
        </form>
      </div>
    </div>
  )
}
