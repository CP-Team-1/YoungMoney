import ArticlePage from '../ArticlePage.jsx'

function CreditExperiencedPage() {
  return (
    <ArticlePage
      title="Credit: Read the Whole Profile, Not One Score"
      topic="Credit"
      level="Experienced"
      takeaway="Manage accurate report data and healthy borrowing habits; treat the score as an outcome, not the goal."
      sources={[
        { label: 'CFPB: Understand your credit score', href: 'https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/understand-your-credit-score/' },
        { label: 'AnnualCreditReport.com', href: 'https://www.annualcreditreport.com/' },
      ]}
    >
      <p>
        A credit score is a snapshot, not a complete measure of financial health.
        Lenders may use different score versions, reporting bureaus, and approval
        rules. Focus on the report data you can influence instead of chasing one
        number.
      </p>
      <h2>Manage the underlying profile</h2>
      <p>
        Payment history and revolving utilization—the share of available card credit
        reported as used—can matter. Closing a card may reduce available credit and
        raise that percentage, so weigh fees and fraud concerns against the effect on
        your profile. Several applications in a short period can also signal risk.
      </p>
      <h2>Take action</h2>
      <p>
        Review all three reports. List each account's limit and reported balance, and
        correct errors before applying for important credit. Never take on unnecessary
        debt merely to optimize a score.
      </p>
    </ArticlePage>
  )
}

export default CreditExperiencedPage
