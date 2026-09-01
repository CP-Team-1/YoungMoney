import './ErrorMessage.css'

export default function ErrorMessage({ message }) {
  return (
    <div className="error-msg" role="alert">
      <span className="error-msg__icon">!</span>
      <p className="error-msg__text">{message}</p>
    </div>
  )
}
