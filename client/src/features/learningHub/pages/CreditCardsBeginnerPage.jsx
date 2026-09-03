import ArticlePage from '../ArticlePage.jsx'

function CreditCardsBeginnerPage() {
  return (
    <ArticlePage
      title="Credit Cards: Make Rewards Secondary"
      topic="Credit Cards and Rewards"
      level="Beginner"
      takeaway="First avoid interest and fees; rewards come second."
      sources={[
        { label: 'CFPB: Credit-card grace periods', href: 'https://www.consumerfinance.gov/ask-cfpb/what-is-a-grace-period-for-a-credit-card-en-47/' },
      ]}
    >
      <p>
        A credit card is borrowed money, not additional income. Each billing cycle
        produces a statement with a balance, minimum payment, and due date. Paying
        only the minimum keeps the account current but usually stretches repayment
        and adds interest.
      </p>
      <h2>Understand the grace period</h2>
      <p>
        If your card offers a purchase grace period and you are not carrying a
        balance, paying the statement balance in full by the due date can prevent
        interest on new purchases. Other transactions may not qualify. Rewards are
        easily outweighed by interest, late fees, or an annual fee.
      </p>
      <h2>Take action</h2>
      <p>
        Find your card's purchase APR, annual fee, grace-period terms, statement
        balance, and due date. Review every statement for errors.
      </p>
    </ArticlePage>
  )
}

export default CreditCardsBeginnerPage
