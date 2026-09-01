import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'

import Welcome from './pages/Welcome'
import Login from './pages/Login'
import Register from './pages/Register'
import GoalSelect from './pages/GoalSelect'
import IncomeSetup from './pages/IncomeSetup'
import Dashboard from './pages/Dashboard'
import Today from './pages/Today'
import Budget from './pages/Budget'
import SpendLog from './pages/SpendLog'
import LearningHub from './pages/LearningHub'
import Lesson from './pages/Lesson'
import Quiz from './pages/Quiz'
import QuizResult from './pages/QuizResult'
import Cards from './pages/Cards'
// DEMO ONLY — remove this import before production deployment
import Demo from './pages/Demo'

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return null
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) return null
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Welcome />} />
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />
      <Route path="/onboarding/goals" element={<GoalSelect />} />
      <Route path="/onboarding/income" element={<IncomeSetup />} />
      <Route path="/dashboard" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
      <Route path="/today" element={<PrivateRoute><Today /></PrivateRoute>} />
      <Route path="/budget" element={<PrivateRoute><Budget /></PrivateRoute>} />
      <Route path="/spend" element={<PrivateRoute><SpendLog /></PrivateRoute>} />
      <Route path="/learn" element={<PrivateRoute><LearningHub /></PrivateRoute>} />
      <Route path="/learn/:lessonId" element={<PrivateRoute><Lesson /></PrivateRoute>} />
      <Route path="/learn/:lessonId/quiz" element={<PrivateRoute><Quiz /></PrivateRoute>} />
      <Route path="/learn/:lessonId/result" element={<PrivateRoute><QuizResult /></PrivateRoute>} />
      <Route path="/cards" element={<PrivateRoute><Cards /></PrivateRoute>} />
      {import.meta.env.DEV && <Route path="/demo" element={<Demo />} />}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
