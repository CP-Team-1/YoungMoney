# YOUNGMONEY_PLAN

Place materials used in the final app in this file

## Learning Hub

The Financial Education Library will contain 12 dedicated article pages. Each of the six topics will have one beginner article and one experienced article. Every article will be no more than 500 words.

### Planned Article Pages

| Topic | Beginner page | Experienced page |
| --- | --- | --- |
| Credit | Credit: Your Borrowing Report Card | Credit: Read the Whole Profile, Not One Score |
| Budgeting | Budgeting: Give Every Dollar a Job | Budgeting: Build a Resilient Cash-Flow System |
| Investing | Investing: Start With Goals, Time, and Risk | Investing: Allocation, Costs, and Rebalancing |
| Debt | Debt: Make a Repayment Map | Debt: Compare the Real Cost of Repayment Options |
| Taxes | Taxes: Understand Your Paycheck and Return | Taxes: Plan for Income Beyond a Paycheck |
| Credit cards and rewards | Credit Cards: Make Rewards Secondary | Rewards: Calculate Net Value, Not Points |

### Page Requirements

- Each article has its own page and stable URL.
- Each page identifies its topic and experience level.
- Each article contains a short introduction, core concepts, a practical action, a key takeaway, and authoritative sources.
- The Learning Hub index links to all 12 pages and supports filtering by topic and experience level.
- Article pages include a clear path back to the Learning Hub.
- Content is educational and does not present individualized financial, investment, tax, or legal advice.

### Frontend Ownership Boundary

Learning Hub implementation will stay inside `client/src/features/learningHub/`. It will expose the page components and route metadata through a single entry point. Shared application routing, navigation, `App.jsx`, and global styles will not be changed without coordination with the frontend owner.

## Database Schema
