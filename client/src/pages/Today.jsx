import { useEffect, useRef, useState } from 'react'
import AppShell from '../components/AppShell'
import { completeTask, createTask, deleteTask, getStreak, getTasks, uncompleteTask } from '../services/today'
import './Today.css'

const TIPS = [
  { id: 1, category: 'Credit', tip: "Check your credit report for free at AnnualCreditReport.com — you're entitled to one free report per bureau per year." },
  { id: 2, category: 'Budgeting', tip: "Review last week's spending in three categories. Awareness is the first step to change." },
  { id: 3, category: 'Investing', tip: "If your employer offers a 401(k) match, contribute at least enough to get the full match — it's free money." },
]

function toIsoDate(d) {
  return d.toISOString().split('T')[0]
}

export default function Today() {
  const tip = TIPS[new Date().getDay() % TIPS.length]
  const today = toIsoDate(new Date())

  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [streak, setStreak] = useState(0)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const addInputRef = useRef(null)

  useEffect(() => {
    Promise.all([getTasks(today), getStreak()])
      .then(([taskData, streakCount]) => {
        setTasks(taskData)
        setStreak(streakCount)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [today])

  useEffect(() => {
    if (showAddForm && addInputRef.current) {
      addInputRef.current.focus()
    }
  }, [showAddForm])

  async function handleToggle(task) {
    const wasCompleted = task.completed
    setTasks((prev) => prev.map((t) => t.id === task.id ? { ...t, completed: !wasCompleted } : t))
    try {
      if (!wasCompleted) {
        await completeTask(task.id, today)
      } else {
        await uncompleteTask(task.id, today)
      }
      getStreak().then(setStreak).catch(() => {})
    } catch {
      setTasks((prev) => prev.map((t) => t.id === task.id ? { ...t, completed: wasCompleted } : t))
    }
  }

  async function handleAddTask(e) {
    e.preventDefault()
    const title = newTitle.trim()
    if (!title) return
    try {
      const created = await createTask(title)
      setTasks((prev) => [...prev, created])
      setNewTitle('')
      setShowAddForm(false)
    } catch {
      /* silent — server must be running */
    }
  }

  async function handleDeleteTask(id) {
    setTasks((prev) => prev.filter((t) => t.id !== id))
    try {
      await deleteTask(id)
    } catch {
      getTasks(today).then(setTasks).catch(() => {})
    }
  }

  return (
    <AppShell>
      <div className="today">
        <header className="today__header">
          <h1 className="today__title">Today</h1>
          <p className="today__date">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}
          </p>
        </header>

        <section className="today__tip">
          <span className="today__tip-label">{tip.category} tip</span>
          <p className="today__tip-text serif">{tip.tip}</p>
        </section>

        <section className="today__section">
          <h2 className="today__section-title">Daily checklist</h2>

          <div className="today__checklist">
            {loading ? (
              <p className="today__loading">Loading…</p>
            ) : (
              tasks.map((task) => (
                <div key={task.id} className="today__check-row">
                  <label className="today__check-item">
                    <input
                      type="checkbox"
                      className="today__checkbox"
                      checked={task.completed}
                      onChange={() => handleToggle(task)}
                    />
                    <span className={`today__check-label${task.completed ? ' today__check-label--done' : ''}`}>
                      {task.title}
                    </span>
                  </label>
                  <button
                    type="button"
                    className="today__delete-btn"
                    onClick={() => handleDeleteTask(task.id)}
                    aria-label={`Delete: ${task.title}`}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
          </div>

          {showAddForm ? (
            <form onSubmit={handleAddTask} className="today__add-form">
              <input
                ref={addInputRef}
                className="today__add-input"
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Task name…"
                maxLength={200}
              />
              <button type="submit" className="sl-btn sl-btn--primary">Add</button>
              <button
                type="button"
                className="sl-btn sl-btn--ghost"
                onClick={() => { setShowAddForm(false); setNewTitle('') }}
              >
                Cancel
              </button>
            </form>
          ) : (
            <button
              type="button"
              className="today__add-task-btn"
              onClick={() => setShowAddForm(true)}
            >
              + Add Task
            </button>
          )}
        </section>

        <section className="today__section">
          <h2 className="today__section-title">Your streak</h2>
          <div className="today__streak">
            <span className="today__streak-num">{streak}</span>
            <div>
              <p className="today__streak-label">day streak</p>
              <p className="today__streak-sub">Keep checking in daily to maintain it</p>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  )
}
