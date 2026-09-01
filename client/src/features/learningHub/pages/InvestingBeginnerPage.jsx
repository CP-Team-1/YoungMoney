import ArticlePage from '../ArticlePage.jsx'

function InvestingBeginnerPage() {
  return (
    <ArticlePage
      title="Investing: Start With Goals, Time, and Risk"
      topic="Investing"
      level="Beginner"
      takeaway="Choose an approach suited to your goal, diversify, contribute consistently, and remember that every investment carries risk."
      sources={[
        { label: 'Investor.gov: Saving and investing for students', href: 'https://www.investor.gov/sites/investorgov/files/2023-09/Pub%20075%20-%20Saving%20and%20Investing%20for%20Students%20-%20R1_0.pdf' },
        { label: 'Investor.gov: Dollar-cost averaging', href: 'https://www.investor.gov/introduction-investing/investing-basics/glossary/dollar-cost-averaging' },
      ]}
    >
      <p>
        Saving prioritizes stability and access to cash. Investing accepts possible
        loss in pursuit of longer-term growth. First identify your goal and when you
        will need the money. Money needed soon generally should not depend on a
        volatile investment recovering in time.
      </p>
      <h2>Use time and diversification</h2>
      <p>
        Compound growth allows returns to generate additional returns. Investing
        equal amounts regularly builds consistency, although it cannot prevent loss.
        Diversification spreads money across investments so one company or category
        has less power over the result. Fees matter because they reduce what you keep.
      </p>
      <h2>Take action</h2>
      <p>
        Write down one goal, its target date, and how much loss you could tolerate
        without abandoning the plan.
      </p>
    </ArticlePage>
  )
}

export default InvestingBeginnerPage
