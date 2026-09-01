export { default as BudgetingBeginnerPage } from './pages/BudgetingBeginnerPage.jsx'
export { default as BudgetingExperiencedPage } from './pages/BudgetingExperiencedPage.jsx'
export { default as CreditBeginnerPage } from './pages/CreditBeginnerPage.jsx'
export { default as CreditExperiencedPage } from './pages/CreditExperiencedPage.jsx'
export { default as CreditCardsBeginnerPage } from './pages/CreditCardsBeginnerPage.jsx'
export { default as CreditCardsExperiencedPage } from './pages/CreditCardsExperiencedPage.jsx'
export { default as DebtBeginnerPage } from './pages/DebtBeginnerPage.jsx'
export { default as DebtExperiencedPage } from './pages/DebtExperiencedPage.jsx'
export { default as InvestingBeginnerPage } from './pages/InvestingBeginnerPage.jsx'
export { default as InvestingExperiencedPage } from './pages/InvestingExperiencedPage.jsx'
export { default as TaxesBeginnerPage } from './pages/TaxesBeginnerPage.jsx'
export { default as TaxesExperiencedPage } from './pages/TaxesExperiencedPage.jsx'

export const learningHubRoutes = [
  { path: '/learn/credit/beginner', page: 'CreditBeginnerPage' },
  { path: '/learn/credit/experienced', page: 'CreditExperiencedPage' },
  { path: '/learn/budgeting/beginner', page: 'BudgetingBeginnerPage' },
  { path: '/learn/budgeting/experienced', page: 'BudgetingExperiencedPage' },
  { path: '/learn/investing/beginner', page: 'InvestingBeginnerPage' },
  { path: '/learn/investing/experienced', page: 'InvestingExperiencedPage' },
  { path: '/learn/debt/beginner', page: 'DebtBeginnerPage' },
  { path: '/learn/debt/experienced', page: 'DebtExperiencedPage' },
  { path: '/learn/taxes/beginner', page: 'TaxesBeginnerPage' },
  { path: '/learn/taxes/experienced', page: 'TaxesExperiencedPage' },
  { path: '/learn/cards-and-rewards/beginner', page: 'CreditCardsBeginnerPage' },
  { path: '/learn/cards-and-rewards/experienced', page: 'CreditCardsExperiencedPage' },
]
