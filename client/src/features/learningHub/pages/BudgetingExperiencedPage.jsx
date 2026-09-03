import ArticlePage from '../ArticlePage.jsx'

function BudgetingExperiencedPage() {
  return (
    <ArticlePage
      title="Budgeting: Build a Resilient Cash-Flow System"
      topic="Budgeting"
      level="Experienced"
      takeaway="Coordinate cash timing, reserves, and priorities so one unusual month does not break the plan."
      sources={[
        { label: 'CFPB: Build an emergency fund', href: 'https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/' },
      ]}
    >
      <p>
        Once basic tracking works, shift from recording the past to managing timing
        and uncertainty. Create a cash-flow calendar showing paydays, due dates,
        transfers, and irregular expenses. This reveals weeks when the monthly total
        looks affordable but the checking balance may run short.
      </p>
      <h2>Separate known costs from emergencies</h2>
      <p>
        Use sinking funds for predictable nonmonthly costs. Keep emergency savings
        for genuinely unplanned shocks, decide what qualifies in advance, and make a
        plan to replenish the fund after using it. With variable income, build the
        core plan around a conservative baseline.
      </p>
      <h2>Take action</h2>
      <p>
        Run a monthly review: reconcile accounts, refill sinking funds, check upcoming
        expenses, and automate one improvement.
      </p>
    </ArticlePage>
  )
}

export default BudgetingExperiencedPage
