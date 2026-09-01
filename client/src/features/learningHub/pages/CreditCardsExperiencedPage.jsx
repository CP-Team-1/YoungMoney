import ArticlePage from '../ArticlePage.jsx'

function CreditCardsExperiencedPage() {
  return (
    <ArticlePage
      title="Rewards: Calculate Net Value, Not Points"
      topic="Credit Cards and Rewards"
      level="Experienced"
      takeaway="The best rewards setup matches existing spending and produces positive value after every cost."
      sources={[
        { label: 'CFPB: Changes to credit-card terms', href: 'https://www.consumerfinance.gov/ask-cfpb/can-my-credit-card-company-change-the-terms-of-my-account-en-70/' },
        { label: 'CFPB: Credit-card grace periods', href: 'https://www.consumerfinance.gov/ask-cfpb/what-is-a-grace-period-for-a-credit-card-en-47/' },
      ]}
    >
      <p>
        Optimize rewards using net value. Estimate the value of rewards you will
        actually redeem, then subtract annual fees, transaction fees, interest, and
        extra spending encouraged by the program. An advertised rate may apply only
        to certain categories or be limited by a cap.
      </p>
      <h2>Value benefits realistically</h2>
      <p>
        For travel rewards, include taxes, surcharges, restrictions, expiration
        policies, and flexibility. Credits or lounge access count only when they
        replace spending you would have made. Never carry interest-bearing debt or
        manufacture purchases to earn a welcome offer. Benefits can also change.
      </p>
      <h2>Take action</h2>
      <p>
        For each card, calculate annual rewards from normal spending plus benefits
        used, minus all fees and interest. Reevaluate before renewal.
      </p>
    </ArticlePage>
  )
}

export default CreditCardsExperiencedPage
