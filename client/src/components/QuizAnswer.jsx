import './QuizAnswer.css'

export default function QuizAnswer({ label, selected, correct, revealed, onClick }) {
  let state = ''
  if (revealed) {
    state = correct ? ' quiz-ans--correct' : selected ? ' quiz-ans--wrong' : ''
  } else if (selected) {
    state = ' quiz-ans--selected'
  }

  return (
    <button type="button" className={`quiz-ans${state}`} onClick={onClick} disabled={revealed}>
      {label}
    </button>
  )
}
