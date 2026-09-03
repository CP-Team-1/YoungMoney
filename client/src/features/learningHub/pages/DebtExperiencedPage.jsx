import ArticlePage from '../ArticlePage.jsx'

function DebtExperiencedPage() {
  return (
    <ArticlePage
      title="Debt: Compare the Real Cost of Repayment Options"
      topic="Debt"
      level="Experienced"
      takeaway="Optimize for total cost and resilience—not merely the smallest advertised payment."
      sources={[
        { label: 'CFPB: How to reduce your debt', href: 'https://www.consumerfinance.gov/archive/blog/how-reduce-your-debt/' },
        { label: 'CFPB: Build an emergency fund', href: 'https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/' },
      ]}
    >
      <p>
        An interest rate does not tell the whole story. Evaluate debt using annual
        percentage rate, fees, variable-rate terms, remaining payoff time, and any
        relevant tax treatment. Test how an extra payment changes total interest and
        the payoff date.
      </p>
      <h2>Look beyond the monthly payment</h2>
      <p>
        Refinancing or consolidation can simplify payments or lower a rate, but a
        smaller payment may extend repayment and increase total cost. Introductory
        rates can expire, transfers may charge fees, and secured debt can put
        collateral at risk. Maintain a cash buffer so an emergency does not recreate
        high-cost debt.
      </p>
      <h2>Take action</h2>
      <p>
        Compare each proposal using total dollars paid, payoff date, fees, rate-change
        risk, and required monthly payment.
      </p>
    </ArticlePage>
  )
}

export default DebtExperiencedPage
