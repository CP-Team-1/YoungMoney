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

  cy.visit(`http://localhost:5173${path}`, {
    onBeforeLoad(win) {
      win.localStorage.setItem('access_token', 'fake-access-token')
      win.localStorage.setItem('refresh_token', 'fake-refresh-token')
    },
  })

  cy.wait('@getMe')
})