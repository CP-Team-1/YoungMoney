describe('YoungMoney Main App Pages', () => {
  beforeEach(() => {
    const cards = [
      { slug: 'sapphire', name: 'Chase Sapphire Preferred', issuer: { name: 'Chase' }, annual_fee: '95', card_type: 'personal' },
      { slug: 'blue-cash', name: 'Blue Cash Preferred', issuer: { name: 'Amex' }, annual_fee: '95', card_type: 'personal' },
      { slug: 'double-cash', name: 'Citi Double Cash', issuer: { name: 'Citi' }, annual_fee: '0', card_type: 'personal' },
    ]
    cy.intercept('GET', '/api/wallet/cards/', []).as('getOwnedCards')
    cy.intercept('GET', '/api/cards/?*', { results: cards }).as('getCards')
    cards.forEach((card) => {
      cy.intercept('GET', `/api/cards/${card.slug}/`, { ...card, max_effective_annual_fee: null })
    })
  })

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

    cy.get('input[type="checkbox"]')
      .first()
      .check()

    cy.get('input[type="checkbox"]')
      .first()
      .should('be.checked')
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


  // TEST 6: Spend Log page loads
  it('loads the Spend Log page', () => {
    cy.loginAsTestUser('/spend')

    cy.url().should('include', '/spend')

    cy.contains('h1', 'Spend Log')
      .should('be.visible')
  })


  // TEST 7: Spend Log is accessible to authenticated users
  it('allows an authenticated user to access the Spend Log', () => {
    cy.loginAsTestUser('/spend')

    cy.url().should('include', '/spend')

    cy.get('.sidebar')
      .contains('Spend Log')
      .should('be.visible')

    cy.contains('h1', 'Spend Log')
      .should('be.visible')
  })


  // TEST 8: Card Optimizer loads available cards
  it('loads credit card recommendations', () => {
    cy.loginAsTestUser('/cards')

    cy.contains('h1', 'Card Optimizer').should('be.visible')
    cy.contains('Sapphire Preferred').should('be.visible')
    cy.contains('Blue Cash Preferred').should('be.visible')
    cy.contains('Double Cash').should('be.visible')
  })


  // TEST 9: Card Optimizer filters cards
  it('filters cards by annual fee', () => {
    cy.loginAsTestUser('/cards')
    cy.contains('button', 'No annual fee').click()
    cy.contains('Double Cash').should('be.visible')
    cy.contains('Sapphire Preferred').should('not.exist')
    cy.contains('Blue Cash Preferred').should('not.exist')
  })

  it('keeps the AI advisor usable when card data is unavailable', () => {
    cy.intercept('GET', '/api/cards/?*', { statusCode: 502, body: { detail: 'Unavailable' } })
    cy.intercept('POST', '/api/advisor/suggest/', {
      suggestion: 'Compare annual fees and rewards before choosing a card.',
    }).as('getAdvice')
    cy.loginAsTestUser('/cards')
    cy.contains('Card data is temporarily unavailable.').should('be.visible')
    cy.contains('button', 'Get AI Recommendations').click()
    cy.wait('@getAdvice').its('request.body.owned_cards').should('deep.equal', [])
    cy.contains('Compare annual fees and rewards before choosing a card.').should('be.visible')
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