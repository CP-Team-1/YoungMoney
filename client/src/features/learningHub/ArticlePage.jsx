import { Link, useParams } from 'react-router-dom'
import AppShell from '../../components/AppShell.jsx'
import { useLearning } from '../../context/LearningContext.jsx'
import './learningHub.css'

function ArticlePage({ title, topic, level, children, takeaway, sources }) {
  const { articleId } = useParams()
  const { completedArticleIds, markArticleRead, markArticleUnread } = useLearning()
  const isRead = articleId ? completedArticleIds.has(articleId) : false

  return (
    <AppShell>
      <div className="learning-article">
        <Link className="learning-article__back" to="/learn">
          ← Back to Learning Hub
        </Link>

        <article>
          <header className="learning-article__header">
            <div className="learning-article__meta">
              <span className="learning-article__topic">{topic}</span>
              <span className="learning-article__level">{level}</span>
              {isRead && <span className="learning-article__read-badge">✓ Read</span>}
            </div>
            <h1>{title}</h1>
          </header>

          <div className="learning-article__body">{children}</div>

          <aside className="learning-article__takeaway">
            <h2>Key takeaway</h2>
            <p>{takeaway}</p>
          </aside>

          <footer className="learning-article__footer">
            <h2>Learn more</h2>
            <ul>
              {sources.map((source) => (
                <li key={source.href}>
                  <a href={source.href} target="_blank" rel="noreferrer">
                    {source.label} ↗
                  </a>
                </li>
              ))}
            </ul>
            <p className="learning-article__disclaimer">
              This article provides general education, not individualized financial,
              investment, tax, or legal advice.
            </p>
          </footer>

          {/* Article read completion control — requires deliberate user action */}
          <div className="learning-article__complete">
            {isRead ? (
              <div className="article-complete-row">
                <span className="article-complete-check">✓ Marked as read</span>
                <button
                  type="button"
                  className="article-mark-btn article-mark-btn--undo"
                  onClick={() => markArticleUnread(articleId)}
                >
                  Undo
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="article-mark-btn article-mark-btn--read"
                onClick={() => markArticleRead(articleId)}
              >
                Mark Article Read
              </button>
            )}
          </div>
        </article>
      </div>
    </AppShell>
  )
}

export default ArticlePage
