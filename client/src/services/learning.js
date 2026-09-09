import api from './api'
import { mockLessons } from '../data/mockLessons'

export async function getLessons() {
  return mockLessons
}

export async function getLesson(id) {
  return mockLessons.find((l) => l.id === id) ?? null
}

export async function getArticleReads() {
  const { data } = await api.get('/wallet/article-reads/')
  return data.map((r) => r.article_id)
}

export async function markArticleReadApi(articleId) {
  await api.post('/wallet/article-reads/', { article_id: articleId })
}

export async function markArticleUnreadApi(articleId) {
  await api.delete('/wallet/article-reads/', { data: { article_id: articleId } })
}
