describe('YoungMoney Learning Hub', () => {
  // TEST 1: Learning Hub loads
  it('loads the Learning Hub', () => {
    cy.loginAsTestUser('/learn')

    cy.contains('h1', 'Learning Hub').should('be.visible')
    cy.contains('Financial Education Library').should('be.visible')
    cy.contains('Interactive lessons').should('be.visible')
  })

  // TEST 2: Interactive lessons are displayed
  it('shows available interactive lessons', () => {
    cy.loginAsTestUser('/learn')

    cy.contains('How Credit Scores Work').should('be.visible')
    cy.contains('The 50/30/20 Rule').should('be.visible')
    cy.contains('Investing 101: Start Here').should('be.visible')
  })

  // TEST 3: Topic filter can be selected
  it('filters the Learning Hub by topic', () => {
    cy.loginAsTestUser('/learn')

    cy.get('[aria-label="Filter by topic"]')
      .contains('button', 'Credit')
      .click()

    cy.get('[aria-label="Filter by topic"]')
      .contains('button', 'Credit')
      .should('have.attr', 'aria-pressed', 'true')
  })

  // TEST 4: Lesson page loads
  it('opens an interactive lesson', () => {
    cy.loginAsTestUser('/learn/credit-basics')

    cy.contains('h1', 'How Credit Scores Work').should('be.visible')
    cy.contains('8 min').should('be.visible')
    cy.contains('Next →').should('be.visible')
  })

  // TEST 5: User can move through a lesson
  it('moves through lesson sections and reaches the quiz', () => {
    cy.loginAsTestUser('/learn/credit-basics')

    cy.contains('button', 'Next →').click()
    cy.contains('button', 'Next →').click()
    cy.contains('button', 'Next →').click()

    cy.contains('button', 'Take the quiz →').should('be.visible')

    cy.contains('button', 'Take the quiz →').click()

    cy.url().should('include', '/learn/credit-basics/quiz')
  })

  // TEST 6: Quiz checks a correct answer
  it('shows correct feedback for a correct quiz answer', () => {
    cy.loginAsTestUser('/learn/credit-basics/quiz')

    cy.contains('Payment history').click()
    cy.contains('button', 'Check answer').click()

    cy.contains('✓ Correct!').should('be.visible')
    cy.contains('button', 'Next question').should('be.visible')
  })

  // TEST 7: User can complete the quiz and see results
  it('completes the credit lesson quiz', () => {
    cy.loginAsTestUser('/learn/credit-basics/quiz')

    cy.contains('Payment history').click()
    cy.contains('button', 'Check answer').click()
    cy.contains('button', 'Next question').click()

    cy.contains('Below 30%').click()
    cy.contains('button', 'Check answer').click()
    cy.contains('button', 'Next question').click()

    cy.contains('300–850').click()
    cy.contains('button', 'Check answer').click()
    cy.contains('button', 'See results').click()

    cy.url().should('include', '/learn/credit-basics/result')

    cy.contains('Excellent').should('be.visible')
    cy.contains('3 out of 3').should('be.visible')
    cy.contains('100').should('be.visible')
  })
})