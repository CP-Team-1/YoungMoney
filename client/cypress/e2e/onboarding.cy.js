describe('YoungMoney Onboarding', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
  })

  // TEST 1: Goal selection page loads
  it('loads the financial goal choices', () => {
    cy.visit('http://localhost:5173/onboarding/goals')

    cy.contains('Step 1 of 2').should('be.visible')
    cy.contains("What's your main goal?").should('be.visible')

    cy.contains('Travel Rewards').should('be.visible')
    cy.contains('Cash Back').should('be.visible')
    cy.contains('Points Strategy').should('be.visible')
    cy.contains('Build Credit').should('be.visible')
  })

  // TEST 2: Continue is disabled until a goal is selected
  it('disables Continue until the user selects a goal', () => {
    cy.visit('http://localhost:5173/onboarding/goals')

    cy.contains('button', 'Continue').should('be.disabled')

    cy.contains('button', 'Travel Rewards').click()

    cy.contains('button', 'Continue').should('not.be.disabled')
  })

  // TEST 3: Selected goal is saved and moves to income setup
  it('saves the selected goal and moves to step two', () => {
    cy.visit('http://localhost:5173/onboarding/goals')

    cy.contains('button', 'Travel Rewards').click()
    cy.contains('button', 'Continue').click()

    cy.url().should('include', '/onboarding/income')

    cy.window().then((win) => {
      expect(win.localStorage.getItem('ym_goal')).to.equal('travel')
    })
  })

  // TEST 4: Income setup saves the entered financial information
  it('saves income information and moves to the dashboard', () => {
    cy.loginAsTestUser('/onboarding/income')

    cy.get('#income').type('4000')
    cy.get('#rent').type('1200')
    cy.get('#food').type('500')
    cy.get('#transport').type('200')

    cy.contains('button', 'Go to my dashboard').click()

    cy.url().should('include', '/dashboard')

    cy.window().then((win) => {
      const saved = JSON.parse(win.localStorage.getItem('ym_income'))

      expect(saved).to.deep.equal({
        income: '4000',
        rent: '1200',
        food: '500',
        transport: '200',
      })
    })
  })
})