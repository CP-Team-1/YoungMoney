import ArticlePage from '../ArticlePage.jsx'

function InvestingExperiencedPage() {
  return (
    <ArticlePage
      title="Investing: Allocation, Costs, and Rebalancing"
      topic="Investing"
      level="Experienced"
      takeaway="Align risk with the goal, diversify deliberately, minimize unnecessary costs, and rebalance consistently."
      sources={[
        { label: 'Investor.gov: Asset allocation and rebalancing', href: 'https://www.investor.gov/additional-resources/general-resources/publications-research/info-sheets/beginners-guide-asset' },
      ]}
    >
      <p>
        Asset allocation divides a portfolio among categories such as stocks, bonds,
        and cash equivalents. The mix should reflect the goal, time horizon, financial
        situation, and ability to tolerate loss. Diversification should occur both
        between asset categories and within them.
      </p>
      <h2>Restore the intended risk</h2>
      <p>
        Market movement causes allocations to drift. Rebalancing restores the target
        by selling overweight assets, buying underweight assets, or directing new
        contributions toward underweight categories. Use a consistent review rule
        instead of reacting to headlines, and consider costs and tax consequences.
      </p>
      <h2>Take action</h2>
      <p>
        Record your target allocation, acceptable drift, review schedule, and
        rebalancing method in a short written policy.
      </p>
    </ArticlePage>
  )
}

export default InvestingExperiencedPage
