import ArticlePage from '../ArticlePage.jsx'

function TaxesExperiencedPage() {
  return (
    <ArticlePage
      title="Taxes: Plan for Income Beyond a Paycheck"
      topic="Taxes"
      level="Experienced"
      takeaway="Tax planning is an ongoing cash-flow process, not an annual filing-day calculation."
      sources={[
        { label: 'IRS: Estimated taxes', href: 'https://www.irs.gov/businesses/small-businesses-self-employed/estimated-taxes' },
        { label: 'IRS Publication 505', href: 'https://www.irs.gov/publications/p505' },
      ]}
    >
      <p>
        Self-employment, interest, dividends, capital gains, rent, and other income
        may not have enough tax withheld. Because federal tax is pay-as-you-go, some
        taxpayers need estimated payments during the year. Underpayment can
        potentially produce a penalty even when the return is filed on time.
      </p>
      <h2>Project and revisit</h2>
      <p>
        Build a projection using expected income, deductions, credits, withholding,
        and prior-year information. Revisit it when income changes. Current Form
        1040-ES and IRS Publication 505 explain who may need to pay and how to
        calculate payments. Keep tax reserves separate from operating money.
      </p>
      <h2>Take action</h2>
      <p>
        Schedule quarterly projection reviews and reconcile payments with your
        records after each one. Seek qualified help when your situation is complex.
      </p>
    </ArticlePage>
  )
}

export default TaxesExperiencedPage
