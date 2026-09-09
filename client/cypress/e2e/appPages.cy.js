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

  // TEST 6: Spend Log page loads
  it('loads the Spend Log page', () => {
    cy.loginAsTestUser('/spend')
    cy.url().should('include', '/spend')
    cy.contains('h1', 'Spend Log').should('be.visible')
  })

  // TEST 7: Spend Log is accessible to authenticated users
  it('allows an authenticated user to access the Spend Log', () => {
    cy.loginAsTestUser('/spend')
    cy.url().should('include', '/spend')
    cy.get('.sidebar').contains('Spend Log').should('be.visible')
    cy.contains('h1', 'Spend Log').should('be.visible')
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
    cy.get('.sidebar').contains('button', 'Sign out').click({ force: true })
    cy.url().should('include', '/login')
    cy.window().then((win) => {
      expect(win.localStorage.getItem('access_token')).to.be.null
      expect(win.localStorage.getItem('refresh_token')).to.be.null
    })
  })

  // ── Cards page ───────────────────────────────────────────────────────────────

  // TEST 11: Add Card button is visible
  it('shows the Add Card button on the Cards page', () => {
    cy.loginAsTestUser('/cards')
    cy.contains('button', '+ Add Card').should('be.visible')
  })

  // TEST 12: Recommended cards display and browse section exists
  it('shows recommended/browse cards section alongside user cards', () => {
    cy.loginAsTestUser('/cards')
    cy.contains('h2', 'Your cards').should('be.visible')
    cy.contains('h2', 'Browse cards').should('be.visible')
    cy.contains('Sapphire Preferred').should('be.visible')
  })

  // ── Daily checklist ──────────────────────────────────────────────────────────

  // TEST 13: Daily tasks load from API and are displayed
  it('loads daily tasks from the API', () => {
    cy.loginAsTestUser('/today')
    cy.wait('@getDailyTasks')
    cy.contains('Review your budget').should('be.visible')
    cy.contains("Log today's spending").should('be.visible')
    cy.contains('Complete a lesson').should('be.visible')
  })

  // TEST 14: Checking a task calls the complete API
  it('persists daily task completion via API', () => {
    cy.loginAsTestUser('/today')
    cy.wait('@getDailyTasks')
    cy.get('input[type="checkbox"]').first().check()
    cy.wait('@completeTask')
    cy.get('input[type="checkbox"]').first().should('be.checked')
  })

  // TEST 15: Previously completed tasks load as checked
  it('displays previously completed daily tasks on load', () => {
    cy.loginAsTestUser('/today', {
      tasks: [
        { id: 1, title: 'Review your budget', completed: true, order: 0 },
        { id: 2, title: "Log today's spending", completed: false, order: 1 },
        { id: 3, title: 'Complete a lesson', completed: false, order: 2 },
      ],
    })
    cy.wait('@getDailyTasks')
    cy.get('input[type="checkbox"]').first().should('be.checked')
    cy.get('input[type="checkbox"]').eq(1).should('not.be.checked')
  })

  // TEST 16: User can add a custom task
  it('allows user to add a new task', () => {
    cy.loginAsTestUser('/today')
    cy.wait('@getDailyTasks')
    cy.contains('button', '+ Add Task').click()
    cy.get('.today__add-input').type('Check credit card balance')
    cy.contains('button', 'Add').click()
    cy.wait('@createDailyTask')
    cy.contains('New task').should('be.visible')
  })

  // TEST 17: User can delete a task
  it('allows user to delete a task', () => {
    cy.loginAsTestUser('/today')
    cy.wait('@getDailyTasks')
    cy.contains('Review your budget')
      .closest('.today__check-row')
      .find('.today__delete-btn')
      .click()
    cy.wait('@deleteDailyTask')
    cy.contains('Review your budget').should('not.exist')
  })

  // ── Article reads ────────────────────────────────────────────────────────────

  // TEST 18: Mark Article Read calls the API and updates the UI
  it('persists article read status via API', () => {
    cy.loginAsTestUser('/learn/articles/budgeting-every-dollar')
    cy.wait('@getArticleReads')
    cy.contains('button', 'Mark Article Read').click()
    cy.wait('@postArticleRead').its('request.body.article_id').should('equal', 'budgeting-every-dollar')
    cy.contains('Marked as read').should('be.visible')
  })

  // TEST 19: Previously read articles load as completed
  it('displays previously read articles as completed', () => {
    cy.loginAsTestUser('/learn/articles/budgeting-every-dollar', {
      articleReads: [{ article_id: 'budgeting-every-dollar' }],
    })
    cy.wait('@getArticleReads')
    cy.contains('Marked as read').should('be.visible')
    cy.contains('button', 'Mark Article Read').should('not.exist')
  })

  // ── Budget prompt ────────────────────────────────────────────────────────────

  // TEST 20: Budget prompt appears when user has no budget data
  it('shows budget prompt when user has no income or categories', () => {
    cy.loginAsTestUser('/dashboard', { income: { amount: '0.00' }, categories: [] })
    cy.contains('Set Up Your Starting Budget').should('be.visible')
    cy.contains('Set My Budget').should('be.visible')
    cy.contains('Maybe Later').should('be.visible')
  })

  // TEST 21: Budget prompt does not appear when budget data exists
  it('does not show budget prompt when user has existing budget data', () => {
    cy.loginAsTestUser('/dashboard')
    // loginAsTestUser returns income=$3800 and 2 categories by default, so prompt is hidden
    cy.contains('Set Up Your Starting Budget').should('not.exist')
  })

  // TEST 22: "Set My Budget" navigates to the budget page
  it('navigates to budget page when Set My Budget is clicked', () => {
    cy.loginAsTestUser('/dashboard', { income: { amount: '0.00' }, categories: [] })
    cy.contains('Set My Budget').click()
    cy.url().should('include', '/budget')
  })

  // TEST 23: Budget prompt reappears after refresh when still no budget
  it('budget prompt reappears after a simulated refresh if no budget exists', () => {
    cy.loginAsTestUser('/dashboard', { income: { amount: '0.00' }, categories: [] })
    cy.contains('Set Up Your Starting Budget').should('be.visible')
    cy.contains('Maybe Later').click()
    cy.contains('Set Up Your Starting Budget').should('not.exist')

    // Simulate refresh — the intercepts from loginAsTestUser persist for the test lifetime,
    // so re-visiting still gets zero income/no categories and React state resets to default (false).
    cy.visit('http://localhost:5173/dashboard')
    cy.wait('@getMe')
    cy.contains('Set Up Your Starting Budget').should('be.visible')
  })

  // ── Streak ───────────────────────────────────────────────────────────────────

  // TEST 24: New user sees streak of 0
  it('shows streak of 0 for a user with no completed tasks', () => {
    cy.loginAsTestUser('/today')
    cy.wait('@getStreak')
    cy.get('.today__streak-num').should('have.text', '0')
  })

  // TEST 25: User who has prior completions loads with streak of 1
  it('displays streak of 1 when the API reports a one-day streak', () => {
    cy.loginAsTestUser('/today', { streak: 1 })
    cy.wait('@getStreak')
    cy.get('.today__streak-num').should('have.text', '1')
  })

  // TEST 26: Multiple completions on the same day do not inflate streak above what the API returns
  it('does not show a streak higher than what the API returns', () => {
    cy.loginAsTestUser('/today', { streak: 1 })
    cy.wait('@getDailyTasks')
    cy.wait('@getStreak')
    // After two completions on the same day the API still returns 1
    cy.get('input[type="checkbox"]').first().check()
    cy.wait('@completeTask')
    cy.get('input[type="checkbox"]').eq(1).check()
    cy.wait('@completeTask')
    cy.get('.today__streak-num').should('have.text', '1')
  })

  // ── Cards — per-card Add ──────────────────────────────────────────────────────

  // TEST 27: Each unowned Browse Card has an Add Card button
  it('shows Add Card button on each unowned browse card', () => {
    cy.loginAsTestUser('/cards')
    cy.contains('h2', 'Browse cards').should('be.visible')
    cy.contains('Sapphire Preferred')
      .closest('.card-item')
      .find('button')
      .contains('+ Add Card')
      .should('be.visible')
  })

  // TEST 28: Clicking per-card Add adds it to Your Cards
  it('adds a browse card to Your Cards when its Add Card button is clicked', () => {
    cy.intercept('POST', '/api/wallet/cards/', {
      statusCode: 201,
      body: {
        card_slug: 'sapphire',
        effective_annual_fee: '95',
        used_credit_ids: [],
      },
    }).as('addCard')
    cy.loginAsTestUser('/cards')
    cy.contains('Sapphire Preferred')
      .closest('.card-item')
      .find('button')
      .contains('+ Add Card')
      .click()
    cy.wait('@addCard')
    cy.contains('h2', 'Your cards')
      .closest('section')
      .contains('Sapphire Preferred')
      .should('be.visible')
  })
})
