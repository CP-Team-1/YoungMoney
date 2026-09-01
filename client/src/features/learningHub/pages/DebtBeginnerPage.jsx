import ArticlePage from '../ArticlePage.jsx'

function DebtBeginnerPage() {
  return (
    <ArticlePage
      title="Debt: Make a Repayment Map"
      topic="Debt"
      level="Beginner"
      takeaway="Know what you owe, protect every minimum payment, and direct extra money through one consistent strategy."
      sources={[
        { label: 'CFPB: How to reduce your debt', href: 'https://www.consumerfinance.gov/archive/blog/how-reduce-your-debt/' },
        { label: 'CFPB: When you cannot pay a card bill', href: 'https://www.consumerfinance.gov/ask-cfpb/what-should-i-do-if-i-cant-pay-my-credit-card-bills-en-1697/' },
      ]}
    >
      <p>
        Debt lets you use money now and repay it over time, usually with interest and
        possible fees. List every balance, interest rate, minimum payment, and due
        date. Keep making at least the minimum on every account while choosing where
        extra money will go.
      </p>
      <h2>Choose a payoff method</h2>
      <p>
        The avalanche method targets the highest interest rate first and generally
        reduces interest cost. The snowball targets the smallest balance first,
        creating quicker visible wins. The best method is one you can sustain. If you
        cannot pay, contact the lender promptly to ask about available options.
      </p>
      <h2>Take action</h2>
      <p>
        Create your debt list, choose one target account, and schedule a small extra
        payment after each payday.
      </p>
    </ArticlePage>
  )
}

export default DebtBeginnerPage
