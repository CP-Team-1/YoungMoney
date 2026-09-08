// FinancialProvider (client/src/context/FinancialContext.jsx) wraps the whole
// app and fetches income/budget-categories/spend-log on every page mount, so
// every authenticated page needs these mocked or a real 401 trips the axios
// interceptor's refresh-then-redirect-to-login logic.
Cypress.Commands.add('loginAsTestUser', (path = '/dashboard') => {
  cy.intercept('GET', '/api/auth/me/', {
    statusCode: 200,
    body: {
      id: 1,
      email: 'test@youngmoney.com',
      first_name: 'Patty',
      last_name: 'Tester',
    },
  }).as('getMe')

  cy.intercept('GET', '/api/wallet/income/', { amount: '3800.00' }).as('getIncome')
  cy.intercept('GET', '/api/wallet/budget-categories/', [
    { id: 'housing', key: 'housing', label: 'Housing', allocated: '1200.00', color: '#e8834a' },
    { id: 'food', key: 'food', label: 'Food', allocated: '500.00', color: '#7fa882' },
  ]).as('getBudgetCategories')
  cy.intercept('GET', '/api/wallet/spend-log/', []).as('getSpendLog')

  cy.visit(`http://localhost:5173${path}`, {
    onBeforeLoad(win) {
      win.localStorage.setItem('access_token', 'fake-access-token')
      win.localStorage.setItem('refresh_token', 'fake-refresh-token')
    },
  })

  cy.wait('@getMe')
})