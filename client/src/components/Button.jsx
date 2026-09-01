import './Button.css'

export default function Button({ children, variant = 'primary', size = 'md', fullWidth = false, disabled = false, type = 'button', onClick }) {
  return (
    <button
      type={type}
      className={`btn btn--${variant} btn--${size}${fullWidth ? ' btn--full' : ''}`}
      disabled={disabled}
      onClick={onClick}
    >
      {children}
    </button>
  )
}
