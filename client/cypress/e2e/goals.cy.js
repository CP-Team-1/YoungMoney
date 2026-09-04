describe('YoungMoney Financial Goals', () => {

  beforeEach(() => {
    cy.loginAsTestUser('/goals')
  })


  // TEST 1: Goals page loads
  it('loads the financial goals page', () => {
    cy.contains('h1', 'Financial goals').should('be.visible')
    cy.contains('Add a goal').should('be.visible')
    cy.contains('Your goals').should('be.visible')
  })


  // TEST 2: New user sees an empty goals state
  it('shows an empty state when there are no saved goals', () => {
    cy.contains('Your saved goals will appear here.')
      .should('be.visible')
  })


  // TEST 3: User can create a predefined financial goal
  it('creates a predefined financial goal', () => {
    cy.get('#goal').select('Emergency Fund')

    cy.get('#name')
      .clear()
      .type('Emergency Savings')

    cy.get('#target')
      .clear()
      .type('5000')

    cy.get('#notes')
      .clear()
      .type('Six months of expenses')

    cy.contains('button', 'Save goal').click()

    cy.contains('Emergency Savings')
      .should('be.visible')

    cy.contains('$5,000.00')
      .should('be.visible')

    cy.contains('Six months of expenses')
      .should('be.visible')
  })


  // TEST 4: User can create a custom financial goal type
  it('creates a custom financial goal', () => {
    cy.get('#goal').select('Other / Custom')

    cy.contains(/custom goal type/i)
      .should('be.visible')

    cy.get('input')
      .filter(':visible')
      .first()
      .clear()
      .type('Computer Accessories')

    cy.get('#name')
      .clear()
      .type('Big Monitor')

    cy.get('#target')
      .clear()
      .type('7500')

    cy.get('#notes')
      .clear()
      .type('Save for a glorious wall-sized monitor')

    cy.contains('button', 'Save goal').click()

    cy.contains(/Computer Accessories/i)
      .should('be.visible')

    cy.contains('Big Monitor')
      .should('be.visible')

    cy.contains('$7,500.00')
      .should('be.visible')
  })


  // TEST 5: User can edit a saved goal
  it('edits a saved goal', () => {
    cy.get('#goal').select('Emergency Fund')

    cy.get('#name')
      .clear()
      .type('Emergency Savings')

    cy.get('#target')
      .clear()
      .type('5000')

    cy.contains('button', 'Save goal').click()

    cy.contains('Emergency Savings')
      .should('be.visible')

    cy.contains('button', 'Edit').click()

    cy.contains(/Edit Goal/i)
      .should('be.visible')

    cy.get('input')
      .filter(':visible')
      .then(($inputs) => {
        const nameInput = [...$inputs].find(
          (input) => input.value === 'Emergency Savings'
        )

        cy.wrap(nameInput)
          .clear()
          .type('Rainy Day Fund')
      })

    cy.contains('button', 'Save changes').click()

    cy.contains('Rainy Day Fund')
      .should('be.visible')
  })


  // TEST 6: User can delete a saved goal
  it('deletes a saved goal', () => {
    cy.get('#goal').select('Emergency Fund')

    cy.get('#name')
      .clear()
      .type('Emergency Savings')

    cy.get('#target')
      .clear()
      .type('5000')

    cy.contains('button', 'Save goal').click()

    cy.contains('Emergency Savings')
      .should('be.visible')

    cy.contains('button', 'Delete').click()

    cy.contains('Emergency Savings')
      .should('not.exist')

    cy.contains('Your saved goals will appear here.')
      .should('be.visible')
  })


  // TEST 7: Created goal appears on dashboard
  it('shows a created goal on the dashboard', () => {
    cy.get('#goal').select('Emergency Fund')

    cy.get('#name')
      .clear()
      .type('Emergency Savings')

    cy.get('#target')
      .clear()
      .type('5000')

    cy.contains('button', 'Save goal').click()

    cy.contains('a', 'Dashboard').click()

    cy.url().should('include', '/dashboard')

    cy.contains('Emergency Savings')
      .should('be.visible')

    cy.contains('$5,000')
      .should('be.visible')
  })


  // TEST 8: User can add money toward a goal
  it('adds money toward a financial goal', () => {
    cy.get('#goal').select('Emergency Fund')

    cy.get('#name')
      .clear()
      .type('Emergency Savings')

    cy.get('#target')
      .clear()
      .type('5000')

    cy.contains('button', 'Save goal').click()

    cy.contains('a', 'Dashboard').click()

    cy.contains('Emergency Savings')
      .should('be.visible')

    cy.contains('button', /Add Money/i)
      .click()

    cy.get('input[type="number"]')
      .filter(':visible')
      .last()
      .clear()
      .type('500')

    cy.contains('button', 'Add to Savings')
      .should('be.visible')
      .click()

    cy.contains('$500')
      .should('be.visible')
  })


  // TEST 9: User can withdraw money from a goal
  it('withdraws money from a financial goal', () => {
    cy.get('#goal').select('Emergency Fund')

    cy.get('#name')
      .clear()
      .type('Emergency Savings')

    cy.get('#target')
      .clear()
      .type('5000')

    cy.contains('button', 'Save goal').click()

    cy.contains('a', 'Dashboard').click()

    // Add $500 first
    cy.contains('button', /Add Money/i)
      .click()

    cy.get('input[type="number"]')
      .filter(':visible')
      .last()
      .clear()
      .type('500')

    cy.contains('button', 'Add to Savings')
      .should('be.visible')
      .click()

    cy.contains('$500')
      .should('be.visible')

    // Withdraw $100
    cy.contains('button', /Withdraw/i)
      .click()

    cy.get('input[type="number"]')
      .filter(':visible')
      .last()
      .clear()
      .type('100')

    cy.get('button.sl-btn--primary')
      .contains('Withdraw')
      .click()

    // $500 - $100 = $400
    cy.contains('$400')
      .should('be.visible')
  })

})