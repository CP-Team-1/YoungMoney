describe('YoungMoney Financial Goals', () => {
  beforeEach(() => {
    cy.intercept('GET', '/api/goals/types/', {
      statusCode: 200,
      body: [
        {
          id: 1,
          goal: 'Emergency Fund',
        },
        {
          id: 2,
          goal: 'Travel',
        },
      ],
    }).as('goalTypes')
  })

  // TEST 1: Goals page loads saved goals
  it('loads existing financial goals', () => {
    cy.intercept('GET', '/api/goals/', {
      statusCode: 200,
      body: [
        {
          id: 1,
          goal: 1,
          goal_name: 'Emergency Fund',
          name: 'Emergency Savings',
          target: '5000.00',
          notes: 'Six months of expenses',
        },
      ],
    }).as('getGoals')

    cy.loginAsTestUser('/goals')

    cy.wait('@goalTypes')
    cy.wait('@getGoals')

    cy.contains('h1', 'Financial goals').should('be.visible')
    cy.contains('Add a goal').should('be.visible')
    cy.contains('Emergency Savings').should('be.visible')
    cy.contains('$5,000.00').should('be.visible')
  })

  // TEST 2: Empty goals state loads
  it('shows an empty state when there are no saved goals', () => {
    cy.intercept('GET', '/api/goals/', {
      statusCode: 200,
      body: [],
    }).as('getGoals')

    cy.loginAsTestUser('/goals')

    cy.wait('@goalTypes')
    cy.wait('@getGoals')

    cy.contains('Your saved goals will appear here.')
      .should('be.visible')
  })

  // TEST 3: User can create a new goal
  it('creates a financial goal', () => {
    cy.intercept('GET', '/api/goals/', {
      statusCode: 200,
      body: [],
    }).as('getGoals')

    cy.intercept('POST', '/api/goals/', {
      statusCode: 201,
      body: {
        id: 2,
        goal: 1,
        goal_name: 'Emergency Fund',
        name: 'Car Fund',
        target: '2500.00',
        notes: 'Save for a reliable car',
      },
    }).as('createGoal')

    cy.loginAsTestUser('/goals')

    cy.wait('@goalTypes')
    cy.wait('@getGoals')

    cy.get('#goal').select('Emergency Fund')
    cy.get('#name').type('Car Fund')
    cy.get('#target').type('2500')
    cy.get('#notes').type('Save for a reliable car')

    cy.contains('button', 'Save goal').click()

    cy.wait('@createGoal')

    cy.contains('Car Fund').should('be.visible')
    cy.contains('$2,500.00').should('be.visible')
    cy.contains('Save for a reliable car').should('be.visible')
  })

  // TEST 4: User can delete a goal
  it('deletes a saved goal', () => {
    cy.intercept('GET', '/api/goals/', {
      statusCode: 200,
      body: [
        {
          id: 1,
          goal: 1,
          goal_name: 'Emergency Fund',
          name: 'Emergency Savings',
          target: '5000.00',
          notes: '',
        },
      ],
    }).as('getGoals')

    cy.intercept('DELETE', '/api/goals/1/', {
      statusCode: 204,
      body: '',
    }).as('deleteGoal')

    cy.loginAsTestUser('/goals')

    cy.wait('@goalTypes')
    cy.wait('@getGoals')

    cy.get('[aria-label="Delete Emergency Savings"]').click()

    cy.wait('@deleteGoal')

    cy.contains('Emergency Savings').should('not.exist')
    cy.contains('Your saved goals will appear here.')
      .should('be.visible')
  })

  // TEST 5: Goals API failure displays an error
  it('shows an error when goals cannot load', () => {
    cy.intercept('GET', '/api/goals/', {
      statusCode: 500,
      body: {},
    }).as('getGoals')

    cy.loginAsTestUser('/goals')

    cy.wait('@goalTypes')
    cy.wait('@getGoals')

    cy.contains('Could not load your goals. Please try again.')
      .should('be.visible')
  })
})