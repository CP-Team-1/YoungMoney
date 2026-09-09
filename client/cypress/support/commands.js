// FinancialProvider (client/src/context/FinancialContext.jsx) wraps the whole
// app and fetches income/budget-categories/spend-log on every page mount, so
// every authenticated page needs these mocked or a real 401 trips the axios
// interceptor's refresh-then-redirect-to-login logic.
//
// LearningContext fetches article-reads on mount.
// Today page fetches daily-tasks on mount.
// GoalsContext fetches goal types and saved goals on mount.
//
// All endpoints used by authenticated Cypress pages are intercepted here so
// tests do not accidentally hit the real backend.
//
// opts overrides (all optional):
//   income        – body for GET /api/wallet/income/          (default $3800)
//   categories    – body for GET /api/wallet/budget-categories/
//   tasks         – body for GET /api/wallet/daily-tasks/     (default 3 tasks)
//   articleReads  – body for GET /api/wallet/article-reads/   (default [])
//   streak        – body value for daily-task streak           (default 0)
//   goals         – initial saved goals                        (default [])
//   goalTypes     – available predefined goal types

Cypress.Commands.add(
  'loginAsTestUser',
  (path = '/dashboard', opts = {}) => {
    cy.intercept('GET', '/api/auth/me/', {
      statusCode: 200,
      body: {
        id: 1,
        email: 'test@youngmoney.com',
        first_name: 'Patty',
        last_name: 'Tester',
      },
    }).as('getMe')

    const income =
      Object.prototype.hasOwnProperty.call(
        opts,
        'income'
      )
        ? opts.income
        : {
            amount: '3800.00',
          }

    const categories =
      Object.prototype.hasOwnProperty.call(
        opts,
        'categories'
      )
        ? opts.categories
        : [
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
          ]

    const tasks =
      Object.prototype.hasOwnProperty.call(
        opts,
        'tasks'
      )
        ? opts.tasks
        : [
            {
              id: 1,
              title: 'Review your budget',
              completed: false,
              order: 0,
            },
            {
              id: 2,
              title: "Log today's spending",
              completed: false,
              order: 1,
            },
            {
              id: 3,
              title: 'Complete a lesson',
              completed: false,
              order: 2,
            },
          ]

    const articleReads =
      Object.prototype.hasOwnProperty.call(
        opts,
        'articleReads'
      )
        ? opts.articleReads
        : []

    const streak =
      Object.prototype.hasOwnProperty.call(
        opts,
        'streak'
      )
        ? opts.streak
        : 0

    const goalTypes =
      Object.prototype.hasOwnProperty.call(
        opts,
        'goalTypes'
      )
        ? opts.goalTypes
        : [
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
          ]

    let goalStore =
      Object.prototype.hasOwnProperty.call(
        opts,
        'goals'
      )
        ? structuredClone(opts.goals)
        : []

    let nextGoalId = 100

    function findGoalType(id) {
      return goalTypes.find(
        (type) =>
          Number(type.id) === Number(id)
      )
    }

    function buildGoalResponse(body, existing = {}) {
      const isCustom =
        body.goal === null ||
        body.goal === 'custom' ||
        (
          body.goal === undefined &&
          existing.goal === null
        )

      const goalId = isCustom
        ? null
        : body.goal !== undefined
          ? Number(body.goal)
          : existing.goal

      const customGoalType =
        body.custom_goal_type !== undefined
          ? body.custom_goal_type
          : existing.custom_goal_type ?? ''

      const predefinedType =
        goalId !== null
          ? findGoalType(goalId)
          : null

      return {
        ...existing,
        id:
          existing.id ??
          String(nextGoalId++),

        goal: goalId,

        goal_name: isCustom
          ? customGoalType
          : predefinedType?.goal ??
            existing.goal_name ??
            '',

        custom_goal_type:
          isCustom
            ? customGoalType
            : '',

        name:
          body.name !== undefined
            ? body.name
            : existing.name,

        target:
          body.target !== undefined
            ? String(
                Number(body.target).toFixed(2)
              )
            : existing.target,

        current:
          body.current !== undefined
            ? String(
                Number(body.current).toFixed(2)
              )
            : existing.current ??
              '0.00',

        notes:
          body.notes !== undefined
            ? body.notes
            : existing.notes ?? '',
      }
    }

    // ---------------------------------------------------------
    // Financial data
    // ---------------------------------------------------------

    cy.intercept(
      'GET',
      '/api/wallet/income/',
      income
    ).as('getIncome')

    cy.intercept(
      'GET',
      '/api/wallet/budget-categories/',
      categories
    ).as('getBudgetCategories')

    cy.intercept(
      'GET',
      '/api/wallet/spend-log/',
      []
    ).as('getSpendLog')

    // ---------------------------------------------------------
    // Today / daily tasks
    // ---------------------------------------------------------

    cy.intercept(
      {
        method: 'GET',
        pathname:
          '/api/wallet/daily-tasks/',
      },
      tasks
    ).as('getDailyTasks')

    cy.intercept(
      'GET',
      '/api/wallet/daily-tasks/streak/',
      {
        streak,
      }
    ).as('getStreak')

    cy.intercept(
      'POST',
      '/api/wallet/daily-tasks/',
      {
        statusCode: 201,
        body: {
          id: 99,
          title: 'New task',
          completed: false,
          order: 3,
        },
      }
    ).as('createDailyTask')

    cy.intercept(
      'DELETE',
      '/api/wallet/daily-tasks/**',
      {
        statusCode: 204,
      }
    ).as('deleteDailyTask')

    cy.intercept(
      'POST',
      '/api/wallet/daily-tasks/*/complete/',
      {
        statusCode: 204,
      }
    ).as('completeTask')

    cy.intercept(
      'DELETE',
      '/api/wallet/daily-tasks/*/complete/',
      {
        statusCode: 204,
      }
    ).as('uncompleteTask')

    // ---------------------------------------------------------
    // Learning / article reads
    // ---------------------------------------------------------

    cy.intercept(
      'GET',
      '/api/wallet/article-reads/',
      articleReads
    ).as('getArticleReads')

    cy.intercept(
      'POST',
      '/api/wallet/article-reads/',
      {
        statusCode: 204,
      }
    ).as('postArticleRead')

    cy.intercept(
      'DELETE',
      '/api/wallet/article-reads/',
      {
        statusCode: 204,
      }
    ).as('deleteArticleRead')

    // ---------------------------------------------------------
    // Goals
    // ---------------------------------------------------------

    cy.intercept(
      'GET',
      '/api/goals/types/',
      {
        statusCode: 200,
        body: goalTypes,
      }
    ).as('getGoalTypes')

    cy.intercept(
      'GET',
      '/api/goals/',
      (req) => {
        req.reply({
          statusCode: 200,
          body: goalStore,
        })
      }
    ).as('getGoals')

    cy.intercept(
      'POST',
      '/api/goals/',
      (req) => {
        const created =
          buildGoalResponse(
            req.body
          )

        goalStore = [
          ...goalStore,
          created,
        ]

        req.reply({
          statusCode: 201,
          body: created,
        })
      }
    ).as('createGoal')

    cy.intercept(
      'PATCH',
      /\/api\/goals\/[^/]+\/$/,
      (req) => {
        const id =
          req.url
            .split('/api/goals/')[1]
            .split('/')[0]

        const existing =
          goalStore.find(
            (goal) =>
              String(goal.id) ===
              String(id)
          )

        if (!existing) {
          req.reply({
            statusCode: 404,
            body: {
              detail:
                'Goal not found.',
            },
          })

          return
        }

        const updated =
          buildGoalResponse(
            req.body,
            existing
          )

        goalStore =
          goalStore.map(
            (goal) =>
              String(goal.id) ===
              String(id)
                ? updated
                : goal
          )

        req.reply({
          statusCode: 200,
          body: updated,
        })
      }
    ).as('updateGoal')

    cy.intercept(
      'DELETE',
      /\/api\/goals\/[^/]+\/$/,
      (req) => {
        const id =
          req.url
            .split('/api/goals/')[1]
            .split('/')[0]

        goalStore =
          goalStore.filter(
            (goal) =>
              String(goal.id) !==
              String(id)
          )

        req.reply({
          statusCode: 204,
        })
      }
    ).as('deleteGoal')

    // ---------------------------------------------------------
    // Visit authenticated page
    // ---------------------------------------------------------

    cy.visit(
      `http://localhost:5173${path}`,
      {
        onBeforeLoad(win) {
          win.localStorage.setItem(
            'access_token',
            'fake-access-token'
          )

          win.localStorage.setItem(
            'refresh_token',
            'fake-refresh-token'
          )
        },
      }
    )

    cy.wait('@getMe')

    // FinancialProvider and GoalsProvider now load asynchronously.
    // Wait for their GETs so Cypress does not click elements while React
    // is still re-rendering the authenticated page.
    cy.wait('@getIncome')
    cy.wait('@getBudgetCategories')
    cy.wait('@getSpendLog')
    cy.wait('@getGoalTypes')
    cy.wait('@getGoals')
  }
)