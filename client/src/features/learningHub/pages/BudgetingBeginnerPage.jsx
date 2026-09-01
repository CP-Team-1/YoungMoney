import ArticlePage from '../ArticlePage.jsx'

function BudgetingBeginnerPage() {
  return (
    <ArticlePage
      title="Budgeting: Give Every Dollar a Job"
      topic="Budgeting"
      level="Beginner"
      takeaway="A useful budget is realistic, includes future expenses, and changes when your life changes."
      sources={[
        { label: 'CFPB: Build an emergency fund', href: 'https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/' },
      ]}
    >
      <p>
        A budget is a plan for how money will come in, go out, and support your goals.
        Start with monthly take-home income, then list essential bills, flexible
        spending, debt payments, and savings. Use recent statements so the plan
        reflects reality rather than guesses.
      </p>
      <h2>Plan beyond this month</h2>
      <p>
        Divide expected annual or irregular costs—such as registration fees, gifts,
        or school supplies—into monthly amounts and save for them in advance. Include
        a small buffer because no month goes exactly as planned.
      </p>
      <h2>Take action</h2>
      <p>
        On your next payday, plan three numbers before spending: bills due before the
        next check, everyday spending, and savings. Compare the result with reality
        and adjust next month.
      </p>
    </ArticlePage>
  )
}

export default BudgetingBeginnerPage
