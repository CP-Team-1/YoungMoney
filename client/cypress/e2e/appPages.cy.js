describe('YoungMoney Main App Pages', () => {
  // TEST 1: Protected pages redirect logged-out users
  it('redirects a logged-out user to login', () => {
    cy.clearLocalStorage()

    cy.visit('http://localhost:5173/dashboard')

    cy.url().should('include', '/login')
  })

  // TEST 2: Dashboard loads for an authenticated user
  it('loads the dashboard', () => {
    cy.loginAsTestUser('/dashboard')

    cy.contains('Hey, Patty').should('be.visible')
    cy.contains('This Month').should('be.visible')
    cy.contains('Savings Goal').should('be.visible')
    cy.contains('Learning').should('be.visible')
    cy.contains('Recent Spending').should('be.visible')
  })

  // TEST 3: Sidebar navigation works
  it('navigates through the desktop sidebar', () => {
    cy.loginAsTestUser('/dashboard')

    cy.get('.sidebar').contains('Budget').click()
    cy.url().should('include', '/budget')
    cy.contains('h1', 'Budget').should('be.visible')

    cy.get('.sidebar').contains('Spend Log').click()
    cy.url().should('include', '/spend')
    cy.contains('h1', 'Spend Log').should('be.visible')

    cy.get('.sidebar').contains('Learn').click()
    cy.url().should('include', '/learn')
    cy.contains('h1', 'Learning Hub').should('be.visible')

    cy.get('.sidebar').contains('Cards').click()
    cy.url().should('include', '/cards')
    cy.contains('h1', 'Card Optimizer').should('be.visible')
  })

  // TEST 4: Today page loads and checklist works
  it('allows the user to check an item on the Today page', () => {
    cy.loginAsTestUser('/today')

    cy.contains('h1', 'Today').should('be.visible')
    cy.contains('Daily checklist').should('be.visible')
    cy.contains('Your streak').should('be.visible')

    cy.get('input[type="checkbox"]').first().check()
    cy.get('input[type="checkbox"]').first().should('be.checked')
  })

  // TEST 5: Budget page displays budget information
  it('loads budget information', () => {
    cy.loginAsTestUser('/budget')

    cy.contains('h1', 'Budget').should('be.visible')
    cy.contains('Monthly income').should('be.visible')
    cy.contains('$3,800').should('be.visible')
    cy.contains('Categories').should('be.visible')
    cy.contains('Housing').should('be.visible')
    cy.contains('Food').should('be.visible')
  })

  // TEST 6: Spend Log displays transactions
  it('loads spending transactions', () => {
    cy.loginAsTestUser('/spend')

    cy.contains('h1', 'Spend Log').should('be.visible')
    cy.contains('Whole Foods').should('be.visible')
    cy.contains('Uber').should('be.visible')
    cy.contains('Netflix').should('be.visible')
  })

  // TEST 7: Spend Log filters transactions by category
  it('filters spending by category', () => {
    cy.loginAsTestUser('/spend')

    cy.contains('button', 'food').click()

    cy.contains('Whole Foods').should('be.visible')
    cy.contains('Chipotle').should('be.visible')

    cy.contains('Uber').should('not.exist')
    cy.contains('Netflix').should('not.exist')
  })

  // TEST 8: Card Optimizer loads available cards
  it('loads credit card recommendations', () => {
    cy.loginAsTestUser('/cards')

    cy.contains('h1', 'Card Optimizer').should('be.visible')
    cy.contains('Chase Sapphire Preferred').should('be.visible')
    cy.contains('Blue Cash Preferred').should('be.visible')
    cy.contains('Citi Double Cash').should('be.visible')
  })

  // TEST 9: Card Optimizer filters cards
  it('filters cards by Travel', () => {
    cy.loginAsTestUser('/cards')

    cy.contains('button', 'Travel').click()

    cy.contains('Chase Sapphire Preferred').should('be.visible')
    cy.contains('Capital One Venture').should('be.visible')

    cy.contains('Citi Double Cash').should('not.exist')
  })

  // TEST 10: User can sign out
it('signs the user out', () => {
  cy.loginAsTestUser('/dashboard')

  cy.get('.sidebar')
    .contains('button', 'Sign out')
    .click({ force: true })

  cy.url().should('include', '/login')

  cy.window().then((win) => {
    expect(win.localStorage.getItem('access_token')).to.be.null
    expect(win.localStorage.getItem('refresh_token')).to.be.null
  })
})
})