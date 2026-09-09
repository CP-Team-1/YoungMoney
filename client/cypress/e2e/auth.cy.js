describe('YoungMoney Authentication', () => {
  beforeEach(() => {
    cy.clearLocalStorage()
  })

  function mockAuthenticatedAppData() {
    cy.intercept(
      'GET',
      '/api/wallet/income/',
      {
        statusCode: 200,
        body: {
          amount: '3800.00',
        },
      }
    ).as('getIncome')

    cy.intercept(
      'GET',
      '/api/wallet/budget-categories/',
      {
        statusCode: 200,
        body: [
          {
            id: 'housing',
            key: 'housing',
            label: 'Housing',
            allocated: '1200.00',
            color: '#e8834a',
          },
          {
            id: 'food',
            key: 'food',
            label: 'Food',
            allocated: '500.00',
            color: '#7fa882',
          },
        ],
      }
    ).as('getBudgetCategories')

    cy.intercept(
      'GET',
      '/api/wallet/spend-log/',
      {
        statusCode: 200,
        body: [],
      }
    ).as('getSpendLog')

    cy.intercept(
      'GET',
      '/api/goals/types/',
      {
        statusCode: 200,
        body: [
          {
            id: 1,
            goal: 'Emergency Fund',
          },
          {
            id: 2,
            goal: 'Savings',
          },
          {
            id: 3,
            goal: 'First Home',
          },
          {
            id: 4,
            goal: 'New Car',
          },
          {
            id: 5,
            goal: 'Vacation',
          },
          {
            id: 6,
            goal: 'Debt Payoff',
          },
          {
            id: 7,
            goal: 'Investment',
          },
          {
            id: 8,
            goal: 'Education',
          },
        ],
      }
    ).as('getGoalTypes')

    cy.intercept(
      'GET',
      '/api/goals/',
      {
        statusCode: 200,
        body: [],
      }
    ).as('getGoals')

    cy.intercept(
      'GET',
      '/api/wallet/article-reads/',
      {
        statusCode: 200,
        body: [],
      }
    ).as('getArticleReads')
  }

  function waitForAuthenticatedAppData() {
    cy.wait('@getIncome')
    cy.wait('@getBudgetCategories')
    cy.wait('@getSpendLog')
    cy.wait('@getGoalTypes')
    cy.wait('@getGoals')
    cy.wait('@getArticleReads')
  }

  // TEST 1: Login page loads
  it('loads the login page', () => {
    cy.visit(
      'http://localhost:5173/login'
    )

    cy.contains(
      'Welcome back'
    ).should('be.visible')

    cy.get('#email')
      .should('be.visible')

    cy.get('#password')
      .should('be.visible')

    cy.contains(
      'button',
      'Sign in'
    ).should('be.visible')
  })

  // TEST 2: Login page links to registration
  it(
    'navigates from login to registration',
    () => {
      cy.visit(
        'http://localhost:5173/login'
      )

      cy.contains(
        'Create one'
      ).click()

      cy.url()
        .should(
          'include',
          '/register'
        )

      cy.contains(
        'Create your account'
      ).should('be.visible')
    }
  )

  // TEST 3: Invalid login shows an error
  it(
    'shows an error for an invalid login',
    () => {
      cy.intercept(
        'POST',
        '/api/auth/login/',
        {
          statusCode: 401,
          body: {
            detail:
              'Invalid credentials',
          },
        }
      ).as('badLogin')

      cy.visit(
        'http://localhost:5173/login'
      )

      cy.get('#email')
        .type(
          'wrong@example.com'
        )

      cy.get('#password')
        .type(
          'wrongpassword'
        )

      cy.contains(
        'button',
        'Sign in'
      ).click()

      cy.wait('@badLogin')

      cy.contains(
        'Incorrect email or password. Please try again.'
      ).should('be.visible')
    }
  )

  // TEST 4: Successful login sends the user to the dashboard
  it(
    'logs in successfully and navigates to the dashboard',
    () => {
      mockAuthenticatedAppData()

      cy.intercept(
        'POST',
        '/api/auth/login/',
        {
          statusCode: 200,
          body: {
            access:
              'fake-access-token',
            refresh:
              'fake-refresh-token',
          },
        }
      ).as('login')

      cy.intercept(
        'GET',
        '/api/auth/me/',
        {
          statusCode: 200,
          body: {
            id: 1,
            email:
              'test@youngmoney.com',
            first_name:
              'Patty',
            last_name:
              'Tester',
          },
        }
      ).as('getMe')

      cy.visit(
        'http://localhost:5173/login'
      )

      cy.get('#email')
        .type(
          'test@youngmoney.com'
        )

      cy.get('#password')
        .type(
          'password123'
        )

      cy.contains(
        'button',
        'Sign in'
      ).click()

      cy.wait('@login')
      cy.wait('@getMe')

      waitForAuthenticatedAppData()

      cy.url()
        .should(
          'include',
          '/dashboard'
        )

      cy.contains(
        'Hey, Patty'
      ).should('be.visible')
    }
  )

  // TEST 5: Registration page loads
  it(
    'loads the registration page',
    () => {
      cy.visit(
        'http://localhost:5173/register'
      )

      cy.contains(
        'Create your account'
      ).should('be.visible')

      cy.get('#first_name')
        .should('be.visible')

      cy.get('#last_name')
        .should('be.visible')

      cy.get('#email')
        .should('be.visible')

      cy.get('#password')
        .should('be.visible')
    }
  )

  // TEST 6: Registration rejects a short password
  it(
    'shows an error when the password is too short',
    () => {
      cy.visit(
        'http://localhost:5173/register'
      )

      cy.get('#first_name')
        .type('Patty')

      cy.get('#email')
        .type(
          'patty@example.com'
        )

      cy.get('#password')
        .type('short')

      cy.contains(
        'button',
        'Create account'
      ).click()

      cy.contains(
        'Password must be at least 8 characters.'
      ).should('be.visible')
    }
  )

  // TEST 7: Successful registration signs in and reaches dashboard
  it(
    'registers successfully and navigates to the dashboard',
    () => {
      mockAuthenticatedAppData()

      cy.intercept(
        'POST',
        '/api/auth/register/',
        {
          statusCode: 201,
          body: {},
        }
      ).as('register')

      cy.intercept(
        'POST',
        '/api/auth/login/',
        {
          statusCode: 200,
          body: {
            access:
              'fake-access-token',
            refresh:
              'fake-refresh-token',
          },
        }
      ).as('login')

      cy.intercept(
        'GET',
        '/api/auth/me/',
        {
          statusCode: 200,
          body: {
            id: 1,
            email:
              'patty@example.com',
            first_name:
              'Patty',
            last_name:
              'Tester',
          },
        }
      ).as('getMe')

      cy.visit(
        'http://localhost:5173/register'
      )

      cy.get('#first_name')
        .type('Patty')

      cy.get('#last_name')
        .type('Tester')

      cy.get('#email')
        .type(
          'patty@example.com'
        )

      cy.get('#password')
        .type(
          'password123'
        )

      cy.contains(
        'button',
        'Create account'
      ).click()

      cy.wait('@register')
      cy.wait('@login')
      cy.wait('@getMe')

      waitForAuthenticatedAppData()

      cy.url()
        .should(
          'include',
          '/dashboard'
        )

      cy.contains(
        'Hey, Patty'
      ).should('be.visible')
    }
  )
})