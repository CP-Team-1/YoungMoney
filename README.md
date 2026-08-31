# YoungMoney 💰

## Overview

**YoungMoney** is a financial literacy tool and educational library designed primarily for younger adults who want to build a stronger understanding of personal finance. The platform combines educational content, interactive quizzes, financial tools, and credit-card reward optimization into one application.

YoungMoney allows users to enter their active credit cards, typical monthly spending, and preferred reward strategy. The application uses this information alongside credit-card data from CardAPI to determine an optimized credit-card setup. Gemini then analyzes the available information and explains the recommended strategy, including potential cards the user does not currently own.

YoungMoney is designed to help users not only make better financial decisions, but also understand *why* those decisions may be beneficial.

---

## Core Features

### Financial Education
An educational library covering fundamental personal finance topics:

- Credit
- Budgeting
- Investing
- Debt
- Taxes
- Credit cards and rewards

Users can complete lessons and quizzes to test their understanding and track their learning progress.

### Credit Card Optimizer
Users can:

- Add their active credit cards
- Enter typical monthly spending
- Select an optimization goal
- Compare potential reward strategies
- Receive an optimized credit-card setup
- Discover cards they may not currently own

Optimization goals may include:

- Travel rewards
- Cashback
- Points
- Other user-defined preferences

### Personalized Financial Tools

The platform provides tools and recommendations based on a user's financial goals, preferences, spending habits, and credit-card setup.

### AI Financial Assistant

Gemini is used to analyze optimization results and provide understandable explanations and recommendations. The application's financial calculations and reward data are used as the foundation for AI recommendations.

YoungMoney is intended as an educational and decision-support tool, not a substitute for professional financial advice.

---

## Technology Stack

### Frontend
- React
- Vite
- React Router DOM
- Axios
- Cypress

### Backend
- Python
- Django
- Django REST Framework
- JWT Authentication
- Django TestCase

### Database
- PostgreSQL
- Psycopg3

### APIs
- **CardAPI** — Credit-card information
- **Gemini API** — AI-powered analysis, explanations, and recommendations

### Infrastructure
- Docker
- Docker Compose
- GitHub Actions
- AWS EC2 (t3.micro)
- Git / GitHub

---

## Application Architecture

```text
                 ┌──────────────────┐
                 │   React / Vite   │
                 │    Frontend      │
                 └────────┬─────────┘
                          │
                       Axios
                          │
                 ┌────────▼─────────┐
                 │ Django REST API  │
                 │     Backend      │
                 └────┬────────┬────┘
                      │        │
             ┌────────▼───┐ ┌──▼─────────┐
             │ PostgreSQL │ │   Gemini   │
             │  Database  │ │     AI     │
             └────────────┘ └────────────┘
                      │
                 ┌────▼─────┐
                 │ CardAPI  │
                 │ Card Data│
                 └──────────┘
