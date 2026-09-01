import ArticlePage from '../ArticlePage.jsx'

function CreditBeginnerPage() {
  return (
    <ArticlePage
      title="Credit: Your Borrowing Report Card"
      topic="Credit"
      level="Beginner"
      takeaway="Build credit by borrowing carefully, paying on time, and checking the information used to evaluate you."
      sources={[
        { label: 'CFPB: Understand your credit score', href: 'https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/understand-your-credit-score/' },
        { label: 'CFPB: Get and keep a good credit score', href: 'https://www.consumerfinance.gov/ask-cfpb/how-do-i-get-and-keep-a-good-credit-score-en-318/' },
      ]}
    >
      <p>
        Credit is your ability to borrow money and repay it later. A credit report
        records information such as your accounts, balances, and payment history. A
        credit score uses report information to estimate how likely you are to repay
        borrowed money. You can have several scores because lenders use different
        formulas and reporting sources.
      </p>
      <h2>Build healthy habits</h2>
      <p>
        Pay every bill on time. Automatic payments or reminders can help. Avoid
        getting close to your credit limits, and remember that you do not need to
        carry a balance or pay interest to build a strong score.
      </p>
      <h2>Take action</h2>
      <p>
        Review your credit reports for unfamiliar accounts and incorrect late
        payments. Set every credit account to send a due-date alert. If you use
        autopay, keep enough money in the linked account.
      </p>
    </ArticlePage>
  )
}

export default CreditBeginnerPage
