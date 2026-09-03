import BudgetingBeginnerPage from './pages/BudgetingBeginnerPage.jsx'
import BudgetingExperiencedPage from './pages/BudgetingExperiencedPage.jsx'
import CreditBeginnerPage from './pages/CreditBeginnerPage.jsx'
import CreditExperiencedPage from './pages/CreditExperiencedPage.jsx'
import CreditCardsBeginnerPage from './pages/CreditCardsBeginnerPage.jsx'
import CreditCardsExperiencedPage from './pages/CreditCardsExperiencedPage.jsx'
import DebtBeginnerPage from './pages/DebtBeginnerPage.jsx'
import DebtExperiencedPage from './pages/DebtExperiencedPage.jsx'
import InvestingBeginnerPage from './pages/InvestingBeginnerPage.jsx'
import InvestingExperiencedPage from './pages/InvestingExperiencedPage.jsx'
import TaxesBeginnerPage from './pages/TaxesBeginnerPage.jsx'
import TaxesExperiencedPage from './pages/TaxesExperiencedPage.jsx'

export const learningHubArticles = [
  {
    id: 'credit-borrowing-report-card',
    path: '/learn/articles/credit-borrowing-report-card',
    category: 'Credit',
    level: 'Beginner',
    title: 'Credit: Your Borrowing Report Card',
    description: 'Learn what credit reports and scores represent and which everyday habits help build credit.',
    duration: '3 min',
    component: CreditBeginnerPage,
  },
  {
    id: 'credit-whole-profile',
    path: '/learn/articles/credit-whole-profile',
    category: 'Credit',
    level: 'Experienced',
    title: 'Credit: Read the Whole Profile, Not One Score',
    description: 'Look beyond one score to manage utilization, applications, and the underlying report data.',
    duration: '3 min',
    component: CreditExperiencedPage,
  },
  {
    id: 'budgeting-every-dollar',
    path: '/learn/articles/budgeting-every-dollar',
    category: 'Budgeting',
    level: 'Beginner',
    title: 'Budgeting: Give Every Dollar a Job',
    description: 'Create a realistic plan that covers bills, flexible spending, savings, and future costs.',
    duration: '3 min',
    component: BudgetingBeginnerPage,
  },
  {
    id: 'budgeting-resilient-cash-flow',
    path: '/learn/articles/budgeting-resilient-cash-flow',
    category: 'Budgeting',
    level: 'Experienced',
    title: 'Budgeting: Build a Resilient Cash-Flow System',
    description: 'Coordinate paydays, sinking funds, variable income, and emergency reserves.',
    duration: '3 min',
    component: BudgetingExperiencedPage,
  },
  {
    id: 'investing-goals-time-risk',
    path: '/learn/articles/investing-goals-time-risk',
    category: 'Investing',
    level: 'Beginner',
    title: 'Investing: Start With Goals, Time, and Risk',
    description: 'Understand time horizon, compound growth, diversification, and consistent contributions.',
    duration: '3 min',
    component: InvestingBeginnerPage,
  },
  {
    id: 'investing-allocation-rebalancing',
    path: '/learn/articles/investing-allocation-rebalancing',
    category: 'Investing',
    level: 'Experienced',
    title: 'Investing: Allocation, Costs, and Rebalancing',
    description: 'Build a portfolio policy around risk, diversification, costs, and disciplined rebalancing.',
    duration: '3 min',
    component: InvestingExperiencedPage,
  },
  {
    id: 'debt-repayment-map',
    path: '/learn/articles/debt-repayment-map',
    category: 'Debt',
    level: 'Beginner',
    title: 'Debt: Make a Repayment Map',
    description: 'Organize what you owe and choose a sustainable avalanche or snowball payoff strategy.',
    duration: '3 min',
    component: DebtBeginnerPage,
  },
  {
    id: 'debt-real-repayment-cost',
    path: '/learn/articles/debt-real-repayment-cost',
    category: 'Debt',
    level: 'Experienced',
    title: 'Debt: Compare the Real Cost of Repayment Options',
    description: 'Compare refinancing and consolidation using total cost, fees, timing, and risk.',
    duration: '3 min',
    component: DebtExperiencedPage,
  },
  {
    id: 'taxes-paycheck-return',
    path: '/learn/articles/taxes-paycheck-return',
    category: 'Taxes',
    level: 'Beginner',
    title: 'Taxes: Understand Your Paycheck and Return',
    description: 'See how withholding, tax returns, refunds, and recordkeeping fit together.',
    duration: '3 min',
    component: TaxesBeginnerPage,
  },
  {
    id: 'taxes-income-beyond-paycheck',
    path: '/learn/articles/taxes-income-beyond-paycheck',
    category: 'Taxes',
    level: 'Experienced',
    title: 'Taxes: Plan for Income Beyond a Paycheck',
    description: 'Plan for estimated payments and changing income with regular tax projections.',
    duration: '3 min',
    component: TaxesExperiencedPage,
  },
  {
    id: 'cards-rewards-secondary',
    path: '/learn/articles/cards-rewards-secondary',
    category: 'Credit Cards',
    level: 'Beginner',
    title: 'Credit Cards: Make Rewards Secondary',
    description: 'Understand statements and grace periods before evaluating points or cash back.',
    duration: '3 min',
    component: CreditCardsBeginnerPage,
  },
  {
    id: 'cards-rewards-net-value',
    path: '/learn/articles/cards-rewards-net-value',
    category: 'Credit Cards',
    level: 'Experienced',
    title: 'Rewards: Calculate Net Value, Not Points',
    description: 'Measure realistic reward value after annual fees, interest, restrictions, and extra spending.',
    duration: '3 min',
    component: CreditCardsExperiencedPage,
  },
]

export function getLearningHubArticle(id) {
  return learningHubArticles.find((article) => article.id === id) ?? null
}
