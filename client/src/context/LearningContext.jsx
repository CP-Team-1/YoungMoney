import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { mockLessons } from '../data/mockLessons'
import { getArticleReads, markArticleReadApi, markArticleUnreadApi } from '../services/learning'
import { useAuth } from './AuthContext'

const LearningContext = createContext(null)

export function LearningProvider({ children }) {
  const { user } = useAuth()
  const [completedArticleIds, setCompletedArticleIds] = useState(new Set())

  // persist lesson completions via POST /api/lessons/:id/complete/
  const [completedLessonIds, setCompletedLessonIds] = useState(new Set())

  // persist quiz attempts via POST /api/lessons/:id/quiz-attempt/ { score }
  // quizAttempts shape: { [lessonId]: { attempts: number, bestScore: number, latestScore: number } }
  const [quizAttempts, setQuizAttempts] = useState({})

  // Re-fetch article reads whenever the authenticated user changes.
  // The [] dep array meant the effect only ran once on mount — a 401 during the
  // logged-out phase was silently swallowed and never retried after login.
  // setState is only called inside the async .then() callback, satisfying the lint rule.
  useEffect(() => {
    if (!user) return
    getArticleReads()
      .then((ids) => setCompletedArticleIds(new Set(ids)))
      .catch(() => {})
  }, [user])

  // Derive lessons array so LessonCard and LearningHub get reactive completed/quizScore fields
  const lessons = mockLessons.map((l) => ({
    ...l,
    completed: completedLessonIds.has(l.id),
    quizScore: quizAttempts[l.id]?.bestScore ?? null,
  }))

  // ── Articles ──────────────────────────────────────────────────────────────
  // Optimistic update — do NOT roll back on API failure so the UI stays usable
  // even if the backend is temporarily unreachable. True state is loaded on next mount.
  const markArticleRead = useCallback(async (id) => {
    setCompletedArticleIds((p) => new Set([...p, id]))
    try {
      await markArticleReadApi(id)
    } catch {
      /* keep optimistic update */
    }
  }, [])

  const markArticleUnread = useCallback(async (id) => {
    setCompletedArticleIds((p) => {
      const next = new Set(p)
      next.delete(id)
      return next
    })
    try {
      await markArticleUnreadApi(id)
    } catch {
      /* keep optimistic update */
    }
  }, [])

  // ── Lessons ───────────────────────────────────────────────────────────────
  // Called by Lesson.jsx "Mark Lesson Complete" — does NOT affect quiz or article counts
  const markLessonComplete = useCallback((id) => {
    setCompletedLessonIds((prev) => new Set([...prev, id]))
  }, [])

  const markLessonIncomplete = useCallback((id) => {
    setCompletedLessonIds((prev) => {
      const next = new Set(prev)
      next.delete(id)
      return next
    })
  }, [])

  // ── Quizzes ───────────────────────────────────────────────────────────────
  // Called for EVERY quiz submission regardless of score — does NOT affect lesson or article counts
  // Retaking the same quiz updates best/latest score but does NOT increment unique-quiz count
  const recordQuizAttempt = useCallback((id, score) => {
    setQuizAttempts((prev) => {
      const existing = prev[id]
      if (!existing) {
        return { ...prev, [id]: { attempts: 1, bestScore: score, latestScore: score } }
      }
      return {
        ...prev,
        [id]: {
          attempts: existing.attempts + 1,
          bestScore: Math.max(existing.bestScore, score),
          latestScore: score,
        },
      }
    })
  }, [])

  // Clears quiz data only — articles and lessons are unaffected
  const resetQuizProgress = useCallback(() => {
    setQuizAttempts({})
  }, [])

  return (
    <LearningContext.Provider
      value={{
        lessons,
        completedArticleIds,
        completedLessonIds,
        quizAttempts,
        markArticleRead,
        markArticleUnread,
        markLessonComplete,
        markLessonIncomplete,
        recordQuizAttempt,
        resetQuizProgress,
      }}
    >
      {children}
    </LearningContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useLearning() {
  const ctx = useContext(LearningContext)
  if (!ctx) throw new Error('useLearning must be used inside LearningProvider')
  return ctx
}
