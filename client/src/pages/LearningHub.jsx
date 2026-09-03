import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import LessonCard from '../components/LessonCard'
import ProgressBar from '../components/ProgressBar'
import LoadingState from '../components/LoadingState'
import { learningHubArticles } from '../features/learningHub'
import { getLessons } from '../services/learning'
import './LearningHub.css'

const ALL = 'All'
const LEVELS = [ALL, 'Beginner', 'Experienced']

export default function LearningHub() {
  const [lessons, setLessons] = useState([])
  const [topicFilter, setTopicFilter] = useState(ALL)
  const [levelFilter, setLevelFilter] = useState(ALL)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getLessons().then(setLessons).finally(() => setLoading(false))
  }, [])

  if (loading) return <AppShell><LoadingState /></AppShell>

  const categories = [
    ALL,
    ...new Set([
      ...learningHubArticles.map((article) => article.category),
      ...lessons.map((lesson) => lesson.category),
    ]),
  ]

  const articles = learningHubArticles.filter((article) => {
    const matchesTopic = topicFilter === ALL || article.category === topicFilter
    const matchesLevel = levelFilter === ALL || article.level === levelFilter
    return matchesTopic && matchesLevel
  })

  const interactiveLessons = topicFilter === ALL
    ? lessons
    : lessons.filter((lesson) => lesson.category === topicFilter)
  const completed = lessons.filter((lesson) => lesson.completed).length

  return (
    <AppShell>
      <div className="hub">
        <header className="hub__header">
          <div>
            <h1 className="hub__title">Learning Hub</h1>
            <p className="hub__sub">Build your financial knowledge, one lesson at a time.</p>
          </div>
          <div className="hub__progress">
            <span className="hub__progress-count">
              {completed}/{lessons.length} interactive lessons complete
            </span>
            <ProgressBar value={completed} max={lessons.length} color="sage" />
          </div>
        </header>

        <div className="hub__filter-group">
          <span className="hub__filter-label">Topic</span>
          <div className="hub__filters" role="group" aria-label="Filter by topic">
            {categories.map((category) => (
              <button
                key={category}
                type="button"
                className={`hub-filter${topicFilter === category ? ' hub-filter--active' : ''}`}
                onClick={() => setTopicFilter(category)}
                aria-pressed={topicFilter === category}
              >
                {category}
              </button>
            ))}
          </div>
        </div>

        <div className="hub__filter-group">
          <span className="hub__filter-label">Experience</span>
          <div className="hub__filters" role="group" aria-label="Filter articles by experience level">
            {LEVELS.map((level) => (
              <button
                key={level}
                type="button"
                className={`hub-filter${levelFilter === level ? ' hub-filter--active' : ''}`}
                onClick={() => setLevelFilter(level)}
                aria-pressed={levelFilter === level}
              >
                {level}
              </button>
            ))}
          </div>
        </div>

        <section className="hub__section" aria-labelledby="article-library-heading">
          <div className="hub__section-heading">
            <div>
              <p className="hub__section-kicker">Financial Education Library</p>
              <h2 id="article-library-heading">Articles for every experience level</h2>
            </div>
            <span className="hub__section-count">{articles.length} articles</span>
          </div>

          {articles.length > 0 ? (
            <div className="hub__grid">
              {articles.map((article) => (
                <LessonCard key={article.id} lesson={article} />
              ))}
            </div>
          ) : (
            <p className="hub__empty">No articles match these filters.</p>
          )}
        </section>

        {interactiveLessons.length > 0 && (
          <section className="hub__section" aria-labelledby="interactive-lessons-heading">
            <div className="hub__section-heading">
              <div>
                <p className="hub__section-kicker">Practice and Check Your Knowledge</p>
                <h2 id="interactive-lessons-heading">Interactive lessons</h2>
              </div>
              <span className="hub__section-count">{interactiveLessons.length} lessons</span>
            </div>

            <div className="hub__grid">
              {interactiveLessons.map((lesson) => (
                <LessonCard key={lesson.id} lesson={lesson} />
              ))}
            </div>
          </section>
        )}
      </div>
    </AppShell>
  )
}
