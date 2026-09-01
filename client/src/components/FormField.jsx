import './FormField.css'

export default function FormField({ label, id, type = 'text', value, onChange, placeholder, error, required, hint }) {
  return (
    <div className="form-field">
      {label && (
        <label className="form-field__label" htmlFor={id}>
          {label}{required && <span className="form-field__required" aria-hidden="true"> *</span>}
        </label>
      )}
      <input
        id={id}
        type={type}
        className={`form-field__input${error ? ' form-field__input--error' : ''}`}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        aria-invalid={!!error}
      />
      {hint && !error && <p id={`${id}-hint`} className="form-field__hint">{hint}</p>}
      {error && <p id={`${id}-error`} className="form-field__error" role="alert">{error}</p>}
    </div>
  )
}
