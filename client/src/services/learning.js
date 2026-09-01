// MOCK — no backend endpoint yet
import { mockLessons } from '../data/mockLessons'

export async function getLessons() {
  return mockLessons
}

export async function getLesson(id) {
  return mockLessons.find((l) => l.id === id) ?? null
}
