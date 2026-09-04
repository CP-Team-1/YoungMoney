import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import AppShell from '../components/AppShell'
import QuizQuestion from '../components/QuizQuestion'
import QuizAnswer from '../components/QuizAnswer'
import LoadingState from '../components/LoadingState'
import { getLesson } from '../services/learning'
import { useLearning } from '../context/LearningContext'
import './Quiz.css'

export default function Quiz() {
  const { lessonId } = useParams()
  const navigate = useNavigate()
  const { recordQuizAttempt } = useLearning()
  const [lesson, setLesson] = useState(null)
  const [loading, setLoading] = useState(true)
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState(null)
  const [revealed, setRevealed] = useState(false)
  const [answers, setAnswers] = useState([])

  useEffect(() => {
    getLesson(lessonId).then(setLesson).finally(() => setLoading(false))
  }, [lessonId])

  if (loading) return <AppShell><LoadingState /></AppShell>
  if (!lesson?.quiz?.length) return (
    <AppShell>
      <p style={{ color: 'var(--color-muted)', padding: 'var(--space-8)' }}>No quiz available for this lesson.</p>
    </AppShell>
  )

  const q = lesson.quiz[current]
  const isLast = current === lesson.quiz.length - 1

  function handleSelect(idx) {
    if (revealed) return
    setSelected(idx)
  }

  function handleCheck() {
    if (selected === null) return
    setRevealed(true)
    setAnswers((a) => [...a, { questionId: q.id, selected, correct: q.correct }])
  }

  function handleNext() {
    if (isLast) {
      const finalAnswers = [...answers]
      const correctCount = finalAnswers.filter(
        (a) => a.selected === lesson.quiz.find((qq) => qq.id === a.questionId).correct
      ).length
      const score = Math.round((correctCount / lesson.quiz.length) * 100)
      // Record every quiz attempt regardless of score — does NOT touch Lessons or Articles counts
      // Retaking the same quiz updates best/latest score but does NOT increment unique-quiz count
      recordQuizAttempt(lessonId, score)
      navigate(`/learn/${lessonId}/result`, { state: { score, total: lesson.quiz.length, correct: correctCount } })
    } else {
      setCurrent(current + 1)
      setSelected(null)
      setRevealed(false)
    }
  }

  return (
    <AppShell>
      <div className="quiz-page">
        <div className="quiz-page__top">
          <Link to={`/learn/${lessonId}`} className="quiz-back">← Back to lesson</Link>
          <span className="quiz-page__category">{lesson.category}</span>
        </div>

        <div className="quiz-page__card">
          <QuizQuestion question={q.question} number={current + 1} total={lesson.quiz.length} />

          <div className="quiz-options">
            {q.options.map((opt, i) => (
              <QuizAnswer
                key={i}
                label={opt}
                selected={selected === i}
                correct={i === q.correct}
                revealed={revealed}
                onClick={() => handleSelect(i)}
              />
            ))}
          </div>

          {revealed && (
            <p className={`quiz-feedback${selected === q.correct ? ' quiz-feedback--correct' : ' quiz-feedback--wrong'}`}>
              {selected === q.correct ? '✓ Correct!' : `✗ The correct answer is: ${q.options[q.correct]}`}
            </p>
          )}

          <div className="quiz-page__actions">
            {!revealed ? (
              <button
                type="button"
                className={`quiz-btn quiz-btn--check${selected !== null ? ' quiz-btn--active' : ''}`}
                onClick={handleCheck}
                disabled={selected === null}
              >
                Check answer
              </button>
            ) : (
              <button type="button" className="quiz-btn quiz-btn--next" onClick={handleNext}>
                {isLast ? 'See results' : 'Next question'} →
              </button>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
