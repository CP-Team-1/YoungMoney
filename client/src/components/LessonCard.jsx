import { Link } from 'react-router-dom'
import './LessonCard.css'

export default function LessonCard({ lesson }) {
  const { id, path, category, level, title, description, duration, completed, quizScore } = lesson
  return (
    <Link to={path ?? `/learn/${id}`} className={`lesson-card${completed ? ' lesson-card--done' : ''}`}>
      <div className="lesson-card__top">
        <span className="lesson-card__category">{category}</span>
        {level && <span className="lesson-card__level">{level}</span>}
        {!level && completed && <span className="lesson-card__badge">✓ Done</span>}
      </div>
      <h3 className="lesson-card__title">{title}</h3>
      <p className="lesson-card__desc">{description}</p>
      <div className="lesson-card__foot">
        <span className="lesson-card__duration">{duration}</span>
        {quizScore !== null && quizScore !== undefined && (
          <span className="lesson-card__score">{quizScore}% quiz</span>
        )}
      </div>
    </Link>
  )
}
