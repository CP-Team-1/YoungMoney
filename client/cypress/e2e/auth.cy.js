describe('YoungMoney Authentication', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
  })

  // TEST 1: Login page loads
  it('loads the login page', () => {
    cy.visit('http://localhost:5173/login')

    cy.contains('Welcome back').should('be.visible')
    cy.get('#email').should('be.visible')
    cy.get('#password').should('be.visible')
    cy.contains('button', 'Sign in').should('be.visible')
  })

  // TEST 2: Login page links to registration
  it('navigates from login to registration', () => {
    cy.visit('http://localhost:5173/login')

    cy.contains('Create one').click()

    cy.url().should('include', '/register')
    cy.contains('Create your account').should('be.visible')
  })

  // TEST 3: Invalid login shows an error
  it('shows an error for an invalid login', () => {
    cy.intercept('POST', '/api/auth/login/', {
      statusCode: 401,
      body: {
        detail: 'Invalid credentials',
      },
    }).as('badLogin')

    cy.visit('http://localhost:5173/login')

    cy.get('#email').type('wrong@example.com')
    cy.get('#password').type('wrongpassword')
    cy.contains('button', 'Sign in').click()

    cy.wait('@badLogin')

    cy.contains('Incorrect email or password. Please try again.')
      .should('be.visible')
  })

  // TEST 4: Successful login sends the user to the dashboard
  it('logs in successfully and navigates to the dashboard', () => {
    cy.intercept('POST', '/api/auth/login/', {
      statusCode: 200,
      body: {
        access: 'fake-access-token',
        refresh: 'fake-refresh-token',
      },
    }).as('login')

    cy.intercept('GET', '/api/auth/me/', {
      statusCode: 200,
      body: {
        id: 1,
        email: 'test@youngmoney.com',
        first_name: 'Patty',
        last_name: 'Tester',
      },
    }).as('getMe')

    cy.visit('http://localhost:5173/login')

    cy.get('#email').type('test@youngmoney.com')
    cy.get('#password').type('password123')
    cy.contains('button', 'Sign in').click()

    cy.wait('@login')
    cy.wait('@getMe')

    cy.url().should('include', '/dashboard')
    cy.contains('Hey, Patty').should('be.visible')
  })

  // TEST 5: Registration page loads
  it('loads the registration page', () => {
    cy.visit('http://localhost:5173/register')

    cy.contains('Create your account').should('be.visible')
    cy.get('#first_name').should('be.visible')
    cy.get('#last_name').should('be.visible')
    cy.get('#email').should('be.visible')
    cy.get('#password').should('be.visible')
  })

  // TEST 6: Registration rejects a short password
  it('shows an error when the password is too short', () => {
    cy.visit('http://localhost:5173/register')

    cy.get('#first_name').type('Patty')
    cy.get('#email').type('patty@example.com')
    cy.get('#password').type('short')

    cy.contains('button', 'Create account').click()

    cy.contains('Password must be at least 8 characters.')
      .should('be.visible')
  })

  // TEST 7: Successful registration starts onboarding
  it('registers successfully and navigates to onboarding', () => {
    cy.intercept('POST', '/api/auth/register/', {
      statusCode: 201,
      body: {},
    }).as('register')

    cy.intercept('POST', '/api/auth/login/', {
      statusCode: 200,
      body: {
        access: 'fake-access-token',
        refresh: 'fake-refresh-token',
      },
    }).as('login')

    cy.intercept('GET', '/api/auth/me/', {
      statusCode: 200,
      body: {
        id: 1,
        email: 'patty@example.com',
        first_name: 'Patty',
        last_name: 'Tester',
      },
    }).as('getMe')

    cy.visit('http://localhost:5173/register')

    cy.get('#first_name').type('Patty')
    cy.get('#last_name').type('Tester')
    cy.get('#email').type('patty@example.com')
    cy.get('#password').type('password123')

    cy.contains('button', 'Create account').click()

    cy.wait('@register')
    cy.wait('@login')
    cy.wait('@getMe')

    cy.url().should('include', '/dashboard')
    cy.contains('Hey, Patty').should('be.visible')
  })
})