import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './context/AuthContext.jsx'
import { FinancialProvider } from './context/FinancialContext.jsx'
import { GoalsProvider } from './context/GoalsContext.jsx'
import { LearningProvider } from './context/LearningContext.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <FinancialProvider>
          <GoalsProvider>
            <LearningProvider>
              <App />
            </LearningProvider>
          </GoalsProvider>
        </FinancialProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
