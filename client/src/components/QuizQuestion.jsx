import './QuizQuestion.css'

export default function QuizQuestion({ question, number, total }) {
  return (
    <div className="quiz-q">
      <p className="quiz-q__counter">{number} / {total}</p>
      <h2 className="quiz-q__text">{question}</h2>
    </div>
  )
}
