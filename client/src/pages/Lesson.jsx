import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import AppShell from '../components/AppShell'
import LessonProgress from '../components/LessonProgress'
import LoadingState from '../components/LoadingState'
import { getLesson } from '../services/learning'
import { useLearning } from '../context/LearningContext'
import './Lesson.css'

export default function Lesson() {
  const { lessonId } = useParams()
  const navigate = useNavigate()
  const [lesson, setLesson] = useState(null)
  const [step, setStep] = useState(0)
  const [loading, setLoading] = useState(true)
  const { lessons, markLessonComplete, markLessonIncomplete } = useLearning()

  useEffect(() => {
    getLesson(lessonId).then(setLesson).finally(() => setLoading(false))
  }, [lessonId])

  if (loading) return <AppShell><LoadingState /></AppShell>
  if (!lesson) return <AppShell><p style={{ color: 'var(--color-muted)', padding: 'var(--space-8)' }}>Lesson not found.</p></AppShell>

  const block = lesson.content[step]
  const isLast = step === lesson.content.length - 1
  const liveLesson = lessons.find((l) => l.id === lessonId)
  const isCompleted = liveLesson?.completed ?? false

  return (
    <AppShell>
      <div className="lesson-page">
        <div className="lesson-page__top">
          <Link to="/learn" className="lesson-back">← Back to lessons</Link>
          <LessonProgress current={step} total={lesson.content.length} />
        </div>

        <div className="lesson-page__meta">
          <span className="lesson-page__category">{lesson.category}</span>
          <span className="lesson-page__duration">{lesson.duration}</span>
          {isCompleted && <span className="lesson-page__done-badge">✓ Completed</span>}
        </div>

        <h1 className="lesson-page__title">{lesson.title}</h1>

        <div className="lesson-block">
          {block.type === 'text' && (
            <p className="lesson-block__text">{block.body}</p>
          )}
          {block.type === 'callout' && (
            <div className="lesson-block__callout">
              <span className="lesson-block__callout-label">{block.label}</span>
              <p className="lesson-block__callout-body">{block.body}</p>
            </div>
          )}
        </div>

        <div className="lesson-page__nav">
          {step > 0 && (
            <button type="button" className="lesson-nav-btn lesson-nav-btn--back" onClick={() => setStep(step - 1)}>
              ← Previous
            </button>
          )}
          {!isLast ? (
            <button type="button" className="lesson-nav-btn lesson-nav-btn--next" onClick={() => setStep(step + 1)}>
              Next →
            </button>
          ) : (
            <button type="button" className="lesson-nav-btn lesson-nav-btn--quiz" onClick={() => navigate(`/learn/${lessonId}/quiz`)}>
              Take the quiz →
            </button>
          )}
        </div>

        {isLast && (
          <div className="lesson-page__complete">
            {isCompleted ? (
              <div className="lesson-complete-row">
                <span className="lesson-complete-check">✓ Marked as complete</span>
                <button
                  type="button"
                  className="lesson-mark-btn lesson-mark-btn--undo"
                  onClick={() => markLessonIncomplete(lessonId)}
                >
                  Undo
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="lesson-mark-btn lesson-mark-btn--complete"
                onClick={() => markLessonComplete(lessonId)}
              >
                Mark lesson complete
              </button>
            )}
          </div>
        )}
      </div>
    </AppShell>
  )
}
