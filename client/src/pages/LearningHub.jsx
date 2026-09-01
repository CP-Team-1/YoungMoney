import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import LessonCard from '../components/LessonCard'
import ProgressBar from '../components/ProgressBar'
import LoadingState from '../components/LoadingState'
import { getLessons } from '../services/learning'
import './LearningHub.css'

const ALL = 'All'

export default function LearningHub() {
  const [lessons, setLessons] = useState([])
  const [filter, setFilter] = useState(ALL)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getLessons().then(setLessons).finally(() => setLoading(false))
  }, [])

  if (loading) return <AppShell><LoadingState /></AppShell>

  const categories = [ALL, ...new Set(lessons.map((l) => l.category))]
  const filtered = filter === ALL ? lessons : lessons.filter((l) => l.category === filter)
  const completed = lessons.filter((l) => l.completed).length

  return (
    <AppShell>
      <div className="hub">
        <header className="hub__header">
          <div>
            <h1 className="hub__title">Learning Hub</h1>
            <p className="hub__sub">Build your financial knowledge, one lesson at a time.</p>
          </div>
          <div className="hub__progress">
            <span className="hub__progress-count">{completed}/{lessons.length}</span>
            <ProgressBar value={completed} max={lessons.length} color="sage" />
          </div>
        </header>

        <div className="hub__filters" role="group" aria-label="Filter by topic">
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              className={`hub-filter${filter === cat ? ' hub-filter--active' : ''}`}
              onClick={() => setFilter(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="hub__grid">
          {filtered.map((lesson) => (
            <LessonCard key={lesson.id} lesson={lesson} />
          ))}
        </div>
      </div>
    </AppShell>
  )
}
