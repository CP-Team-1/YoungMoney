import ArticlePage from '../ArticlePage.jsx'

function TaxesBeginnerPage() {
  return (
    <ArticlePage
      title="Taxes: Understand Your Paycheck and Return"
      topic="Taxes"
      level="Beginner"
      takeaway="Understand what is withheld, keep reliable records, and use current official guidance when filing."
      sources={[
        { label: 'IRS: Tax withholding', href: 'https://www.irs.gov/individuals/employees/tax-withholding' },
        { label: 'IRS: Individual tax filing', href: 'https://www.irs.gov/individual-tax-filing' },
      ]}
    >
      <p>
        Federal income tax generally operates on a pay-as-you-go basis. Employees
        usually have tax withheld from each paycheck based partly on Form W-4. A tax
        return compares what you paid with what you owe. A refund generally means you
        paid more during the year than the final calculation required.
      </p>
      <h2>Keep your information current</h2>
      <p>
        Save income documents and records that may support credits or deductions. Use
        current IRS instructions because rules and deadlines can change. Review
        withholding after events such as a new job, second job, marriage, divorce, or
        new nonwage income.
      </p>
      <h2>Take action</h2>
      <p>
        Compare gross pay, taxes withheld, other deductions, and net pay on your
        latest pay stub. Use the IRS estimator if you need to review withholding.
      </p>
    </ArticlePage>
  )
}

export default TaxesBeginnerPage
