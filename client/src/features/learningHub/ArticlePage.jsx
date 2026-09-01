import { Link } from 'react-router-dom'
import AppShell from '../../components/AppShell.jsx'
import './learningHub.css'

function ArticlePage({ title, topic, level, children, takeaway, sources }) {
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
        </article>
      </div>
    </AppShell>
  )
}

export default ArticlePage
