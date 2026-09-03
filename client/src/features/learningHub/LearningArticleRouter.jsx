import { Navigate, useParams } from 'react-router-dom'
import { getLearningHubArticle } from './index.js'

function LearningArticleRouter() {
  const { articleId } = useParams()
  const article = getLearningHubArticle(articleId)

  if (!article) return <Navigate to="/learn" replace />

  const ArticleComponent = article.component
  return <ArticleComponent />
}

export default LearningArticleRouter
