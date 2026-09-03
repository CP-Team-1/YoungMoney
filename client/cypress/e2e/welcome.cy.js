describe('YoungMoney Welcome Page', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5173/')
  })

  // TEST 1: Welcome page loads
  it('loads the YoungMoney welcome page', () => {
    cy.contains('YoungMoney').should('be.visible')
    cy.contains("Get started — it's free").should('be.visible')
    cy.contains('Sign in').should('be.visible')
  })

  // TEST 2: Get Started navigates to registration
  it('takes the user to registration when Get Started is clicked', () => {
    cy.contains("Get started — it's free").click()

    cy.url().should('include', '/register')
  })

  // TEST 3: Sign In navigates to login
  it('takes the user to login when Sign in is clicked', () => {
    cy.contains('Sign in').click()

    cy.url().should('include', '/login')
  })
})
