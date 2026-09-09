describe(
  'YoungMoney Financial Goals',
  () => {
    beforeEach(() => {
      cy.loginAsTestUser(
        '/goals',
        {
          goals: [],
        }
      )

      cy.contains(
        'h1',
        'Financial goals'
      ).should('be.visible')
    })

    // TEST 1
    it(
      'loads the financial goals page',
      () => {
        cy.contains(
          'h1',
          'Financial goals'
        ).should('be.visible')

        cy.contains(
          'Add a goal'
        ).should('be.visible')

        cy.contains(
          'Your goals'
        ).should('be.visible')
      }
    )

    // TEST 2
    it(
      'shows an empty state when there are no saved goals',
      () => {
        cy.contains(
          'Your saved goals will appear here.'
        ).should('be.visible')
      }
    )

    // TEST 3
    it(
      'creates a predefined financial goal',
      () => {
        cy.get('#goal')
          .should('be.enabled')
          .select(
            'Emergency Fund'
          )

        cy.get('#name')
          .clear()
          .type(
            'Emergency Savings'
          )

        cy.get('#target')
          .clear()
          .type('5000')

        cy.get('#notes')
          .clear()
          .type(
            'Six months of expenses'
          )

        cy.contains(
          'button',
          'Save goal'
        ).click()

        cy.wait('@createGoal')

        cy.contains(
          'Emergency Savings'
        ).should('be.visible')

        cy.contains(
          '$5,000.00'
        ).should('be.visible')

        cy.contains(
          'Six months of expenses'
        ).should('be.visible')
      }
    )

    // TEST 4
    it(
      'creates a custom financial goal',
      () => {
        cy.get('#goal')
          .should('be.enabled')
          .select(
            'Other / Custom'
          )

        cy.get(
          '#customGoalType'
        )
          .should('be.visible')
          .clear()
          .type(
            'Computer Accessories'
          )

        cy.get('#name')
          .clear()
          .type(
            'Big Monitor'
          )

        cy.get('#target')
          .clear()
          .type('7500')

        cy.get('#notes')
          .clear()
          .type(
            'Save for a glorious wall-sized monitor'
          )

        cy.contains(
          'button',
          'Save goal'
        ).click()

        cy.wait('@createGoal')

        cy.contains(
          'Computer Accessories'
        ).should('be.visible')

        cy.contains(
          'Big Monitor'
        ).should('be.visible')

        cy.contains(
          '$7,500.00'
        ).should('be.visible')
      }
    )

    // TEST 5
    it(
      'edits a saved goal',
      () => {
        cy.get('#goal')
          .should('be.enabled')
          .select(
            'Emergency Fund'
          )

        cy.get('#name')
          .type(
            'Emergency Savings'
          )

        cy.get('#target')
          .type('5000')

        cy.contains(
          'button',
          'Save goal'
        ).click()

        cy.wait('@createGoal')

        cy.contains(
          'Emergency Savings'
        ).should('be.visible')

        cy.contains(
          'button',
          'Edit'
        ).click()

        cy.contains(
          'h2',
          'Edit Goal'
        ).should('be.visible')

        cy.get('#edit-name')
          .clear()
          .type(
            'Rainy Day Fund'
          )

        cy.contains(
          'button',
          'Save changes'
        ).click()

        cy.wait('@updateGoal')

        cy.contains(
          'Rainy Day Fund'
        ).should('be.visible')

        cy.contains(
          'Emergency Savings'
        ).should('not.exist')
      }
    )

    // TEST 6
    it(
      'deletes a saved goal',
      () => {
        cy.get('#goal')
          .should('be.enabled')
          .select(
            'Emergency Fund'
          )

        cy.get('#name')
          .type(
            'Emergency Savings'
          )

        cy.get('#target')
          .type('5000')

        cy.contains(
          'button',
          'Save goal'
        ).click()

        cy.wait('@createGoal')

        cy.contains(
          'Emergency Savings'
        ).should('be.visible')

        cy.contains(
          'button',
          'Delete'
        ).click()

        cy.wait('@deleteGoal')

        cy.contains(
          'Emergency Savings'
        ).should('not.exist')

        cy.contains(
          'Your saved goals will appear here.'
        ).should('be.visible')
      }
    )

    // TEST 7
    it(
      'shows a created goal on the dashboard',
      () => {
        cy.get('#goal')
          .should('be.enabled')
          .select(
            'Emergency Fund'
          )

        cy.get('#name')
          .type(
            'Emergency Savings'
          )

        cy.get('#target')
          .type('5000')

        cy.contains(
          'button',
          'Save goal'
        ).click()

        cy.wait('@createGoal')

        cy.contains(
          'a',
          'Dashboard'
        ).click()

        cy.url()
          .should(
            'include',
            '/dashboard'
          )

        cy.contains(
          'Emergency Savings'
        ).should('be.visible')

        cy.contains(
          '$5,000'
        ).should('be.visible')
      }
    )

    // TEST 8
    it(
      'adds money toward a financial goal',
      () => {
        cy.get('#goal')
          .should('be.enabled')
          .select(
            'Emergency Fund'
          )

        cy.get('#name')
          .type(
            'Emergency Savings'
          )

        cy.get('#target')
          .type('5000')

        cy.contains(
          'button',
          'Save goal'
        ).click()

        cy.wait('@createGoal')

        cy.contains(
          'a',
          'Dashboard'
        ).click()

        cy.contains(
          'Emergency Savings'
        ).should('be.visible')

        cy.contains(
          'button',
          /Add Money/i
        ).click()

        cy.get(
          '#savings-amount'
        )
          .should('be.visible')
          .clear()
          .type('500')

        cy.contains(
          'button',
          'Add to Savings'
        ).click()

        cy.wait('@updateGoal')

        cy.contains(
          '$500'
        ).should('be.visible')
      }
    )

    // TEST 9
    it(
      'withdraws money from a financial goal',
      () => {
        cy.get('#goal')
          .should('be.enabled')
          .select(
            'Emergency Fund'
          )

        cy.get('#name')
          .type(
            'Emergency Savings'
          )

        cy.get('#target')
          .type('5000')

        cy.contains(
          'button',
          'Save goal'
        ).click()

        cy.wait('@createGoal')

        cy.contains(
          'a',
          'Dashboard'
        ).click()

        // Add $500 first
        cy.contains(
          'button',
          /Add Money/i
        ).click()

        cy.get(
          '#savings-amount'
        )
          .clear()
          .type('500')

        cy.contains(
          'button',
          'Add to Savings'
        ).click()

        cy.wait('@updateGoal')

        cy.contains(
          '$500'
        ).should('be.visible')

        // Withdraw $100
        cy.contains(
          'button',
          /Withdraw/i
        )
          .filter(':enabled')
          .first()
          .click()

        cy.get(
          '#savings-amount'
        )
          .clear()
          .type('100')

        cy.get(
          'button.sl-btn--primary'
        )
          .contains(
            'Withdraw'
          )
          .click()

        cy.wait('@updateGoal')

        // $500 - $100 = $400
        cy.contains(
          '$400'
        ).should('be.visible')
      }
    )
  }
)