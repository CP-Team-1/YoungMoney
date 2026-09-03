# CardAPI integration

The integration stores CardAPI catalog data in local Django models. Reviewed
official issuer data takes precedence when it is at least as recent as CardAPI's
dated value. An undated API response never silently replaces a reviewed value.
Curated overrides retain their source, review date, and prior value.

## Current status and ownership boundary

The CardAPI catalog, import pipeline, coverage reporting, reward calculations,
goal matching, portfolio analysis, recommendation API, and weekly maintenance
command are implemented. The CardAPI test suite is the authoritative regression
check. User goals, owned cards, spending profiles, and budgets belong to the
accounts domain; this app only accepts that information as transient calculation
input and does not persist it.

Last verified on 2026-09-03: all 86 CardAPI tests passed, Django system checks
passed, the committed snapshot restored successfully into a freshly migrated
test database, and no model migration changes were pending.

The weekly maintenance command exists, but no host or platform scheduler has
been installed. Deployment location and execution time still need to be chosen.
The suggested starting cadence is Sunday at 3:00 a.m. Pacific.

## Cold-start recovery

Docker Compose passes backend environment variables from `server/.env`. Add the
key there, without source-code changes:

```dotenv
CARDAPI_KEY=your-current-key
```

Environment-file changes only reach newly created containers. Recreate the
backend container after changing the key:

```bash
docker compose up -d --force-recreate backend
```

The preferred recovery path does not call CardAPI. From the repository root,
start the database and backend, apply migrations, and restore the committed
catalog snapshot:

```bash
docker compose up -d db backend
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py restore_cardapi_snapshot \
  cardapi/data/catalog_snapshot_2026-09-02.json --confirm-replace
docker compose exec backend python manage.py check
docker compose exec backend python manage.py test cardapi
```

The restore command replaces only the CardAPI catalog tables and requires the
explicit `--confirm-replace` safeguard. Use it for cold-start recovery, not as a
routine synchronization command. The transaction rolls back if fixture loading
fails.

The snapshot contains catalog data only—no users, saved goals, or API keys. It
restores stable local and external identities, active and inactive history,
reward rates, signup bonuses, credits, perks, reward programs, companion-card
rules, and transfer routes. After restoring it, run weekly maintenance once if
current CardAPI data is desired, then review the coverage output.

If the snapshot is unavailable, rebuild from external and reviewed sources in
this order. Run these commands inside the backend container, or prefix each
with `docker compose exec backend` when running from the repository root:

```bash
python manage.py migrate
python manage.py run_cardapi_maintenance --country US --page-size 100 \
  --max-pages 100 --unavailable perks --unavailable statement_credits
python manage.py import_curated_cards \
  cardapi/data/official_product_pilot_2026-09-02.json
python manage.py import_curated_cards \
  cardapi/data/official_perks_pilot_2026-09-02.json
python manage.py import_curated_cards \
  cardapi/data/official_aeroplan_rates_2026-09-02.json
python manage.py import_reward_programs \
  cardapi/data/official_reward_programs_2026-09-02.json
python manage.py import_transfer_partners \
  cardapi/data/official_transfer_partners_2026-09-02.json
python manage.py cardapi_coverage --country US --format json \
  --unavailable perks --unavailable statement_credits
```

The source-file rebuild requires a working `CARDAPI_KEY` and network access.
Treat the dated official JSON as reviewed source material; do not replace it
with ad hoc SQL. After any reviewed data change, regenerate and commit a new
dated snapshot using the instructions below.

## Configuration

Rotate any API key that has been shared in chat or committed anywhere. For a
non-Docker process, set the replacement only in the process environment:

```bash
export CARDAPI_KEY="your-replacement-key"
```

`CARDAPI_BASE_URL` is optional and defaults to CardAPI's production REST URL.
Never place the API key in Django settings, fixtures, logs, or version control.

## Small CardAPI import

Apply migrations, then import a deliberately small page:

```bash
python manage.py migrate
python manage.py sync_cardapi --limit 20 --offset 0 --country US
```

The command is safe to repeat. It does not mark missing reward rates or signup
bonuses inactive because free-tier responses may be incomplete.

Fetch a reviewed shortlist by its stable CardAPI slugs:

```bash
python manage.py sync_cardapi_cards chase-sapphire-reserve-credit-card \
  capital-one-venture-x
```

CardAPI currently returns `403` for the per-card perks and statement-credit
endpoints on the free plan. Their tables can be populated through the curated
import format below; the service also supports the documented API payloads if
the subscription is upgraded later.

`--authoritative-child-data` enables deactivation and must only be used when the
response is known to contain the complete child collections for every returned
card.

## Curated fallback import

Curated records are loaded from reviewed, version-controlled JSON instead of
raw SQL. A file uses this shape:

```json
{
  "data": [
    {
      "cardapi_slug": "american-express-gold-card",
      "source_url": "https://www.americanexpress.com/example",
      "verified_at": "2026-09-02",
      "source_updated_at": "2026-04-30",
      "fields": {
        "foreign_transaction_fee": 0
      },
      "reward_rates": [
        {
          "source_key": "issuer-dining-rate-2026",
          "category_slug": "dining",
          "rate_multiplier": 4,
          "rate_type": "points_per_dollar"
        }
      ],
      "signup_bonuses": [
        {
          "source_key": "issuer-public-offer-2026-09",
          "offer_text": "Earn 60,000 points after meeting the spend requirement",
          "bonus_amount": 60000,
          "bonus_unit": "points",
          "minimum_spend": 6000,
          "minimum_spend_months": 6
        }
      ],
      "statement_credits": [
        {
          "source_key": "issuer-dining-credit-2026",
          "name": "Dining Credit",
          "amount": 120,
          "period": "annual",
          "eligible_merchants": "Selected dining partners",
          "enrollment_required": false
        }
      ],
      "perks": [
        {
          "source_key": "issuer-lounge-access-2026",
          "perk_type": "lounge",
          "name": "Lounge Access",
          "value": null,
          "period": "annual",
          "partner": "Example lounge network"
        }
      ]
    }
  ]
}
```

`source_updated_at` is optional and must only be supplied when the issuer
publishes an update date. The import records `source_url` as the card's canonical
product URL and `verified_at` as YoungMoney's last official-page review date.

Child records inherit the card entry's `source_url` and `verified_at`, or may
override them. Import the file with:

```bash
python manage.py import_curated_cards path/to/reviewed_cards.json
```

Reviewed card fields may correct conflicting CardAPI values. CardAPI can replace
a reviewed field only when its payload includes an `updated_at` later than the
official-page verification date; doing so removes that field's curated marker.

APR is intentionally not modeled or curated because it is applicant-specific.
Signup bonuses use the offer displayed on the canonical public product page at
review time; channel-specific and targeted offers are not combined with it.

## Coverage report

Generate a read-only report after an import:

```bash
python manage.py cardapi_coverage \
  --country US \
  --unavailable perks \
  --unavailable statement_credits
```

Use `--format json` for machine-readable output, `--slug` to select particular
cards, and `--stale-after-days` to change the default 90-day freshness window.
The unavailable flags identify fields blocked by the current CardAPI plan; they
do not mark database records or change future imports.

The initial recommendation-readiness check requires an issuer, card type,
annual fee, at least one active reward rate, an active base reward rate, and a
reward-program mapping whenever the card earns points or miles. Active point or
mile signup bonuses without a program link are reported as incomplete. Other
missing fields remain visible without automatically disqualifying a card.

## Weekly CardAPI maintenance

The scheduler should invoke one command. It fetches every CardAPI page for the
selected country, performs non-authoritative upserts, and emits one JSON result
containing aggregate synchronization counts plus the complete coverage report:

```bash
python manage.py run_cardapi_maintenance \
  --country US \
  --page-size 100 \
  --max-pages 100 \
  --stale-after-days 90 \
  --unavailable perks \
  --unavailable statement_credits
```

Non-authoritative imports are deliberate because free-tier responses may omit
child data; an omitted reward rate or signup bonus must not be deactivated. The
command stops on an invalid or repeated page and fails if `--max-pages` is
reached before pagination ends. A nonzero exit status allows the scheduler to
report a failure, while successful JSON output can be retained as the weekly
audit log.

For the current Docker Compose development setup, one host cron entry could run
the command every Sunday at 3:00 a.m. in the host's configured timezone:

```cron
0 3 * * 0 cd /path/to/YoungMoney && docker compose exec -T backend python manage.py run_cardapi_maintenance --country US --page-size 100 --max-pages 100 --unavailable perks --unavailable statement_credits
```

Curated card imports, reward-program imports, transfer-partner imports, and
catalog fixture generation remain manual reviewed operations.

## Portfolio value service

`cardapi.services.portfolio` compares a current card portfolio with adding each
candidate card. It accepts annual spending buckets, uses the reward matcher and
the selected points valuation strategy, assigns each bucket to its highest-value
card, and subtracts annual fees.

Statement credits are conservative opt-ins: callers pass a `StatementCreditUse`
with a utilization value from `0` to `1`. Monthly, quarterly, and semiannual
amounts are annualized. Unselected credits, signup bonuses, and perks are not
silently treated as cash. The result reports perks as unvalued and keeps signup
bonuses outside recurring annual value.

Signup bonuses store a normalized `bonus_amount` and `bonus_unit`; point and mile
offers may also link directly to their `RewardProgram`. Candidate analysis always
keeps recurring value separate from first-year value. A caller may pass a
`SignupBonusUse` with confirmed or explicitly assumed eligibility and confirmation
that the minimum spend is achievable. Without those inputs, the service reports
the offer's potential estimated value but does not include it in the first-year
total. Point and mile bonuses use the same cash, portal, transfer, or custom
cents-per-point strategy as purchase rewards.

Use `evaluate_portfolio` for one portfolio and `analyze_candidate_cards` to
compare the baseline with adding each candidate individually. If a reward value,
annual fee, or spending bucket cannot be evaluated, the result explains the gap
and does not report a falsely precise net value.

Signup bonus amounts are stored in their native unit (`cash`, `points`, or
`miles`) and may be linked to a `RewardProgram`. The candidate analysis reports
their potential estimated value separately. It includes that value in
`incremental_first_year_value` only when the offer is active, its amount and
minimum-spend terms are known, and a `SignupBonusUse` says the user is eligible
(or explicitly assumes eligibility) and can meet the spend requirement.
`incremental_recurring_value` never includes a signup bonus.

Reward programs are classified as issuer rewards, airline loyalty, hotel
loyalty, or cash back. This prevents direct currencies such as Aeroplan points
or AAdvantage miles from being mistaken for transferable issuer currencies.

## Transfer partners and reward goals

Reviewed transfer catalogs are imported separately from CardAPI:

```bash
python manage.py import_transfer_partners \
  cardapi/data/official_transfer_partners_2026-09-02.json
```

The import is idempotent and authoritative for every source program included in
the file. Omitted routes for those programs are marked inactive rather than
deleted. Each route retains its source, review date, ratio, minimum/increment,
effective dates, and optional card/account-opening cohort conditions. Use
`--non-authoritative` for a deliberately partial file.

`cardapi.services.goals.match_reward_goals` accepts one or more `RewardGoal`
objects. Each goal may contain multiple acceptable destination programs. It
reports direct earning, ordinary transfers, and portfolio-unlocked transfers
without treating transfer ratios as cash values. If a ratio depends on when a
card account was opened, the result requests that date rather than guessing.

`analyze_candidate_cards` accepts the same goals through `reward_goals`. Its
result keeps recurring-dollar rank, first-year rank, and goal-fit rank separate.
This prevents a subjective goal priority from being silently added to a dollar
estimate.

The reviewed catalog currently covers public partner lists for Chase Ultimate
Rewards, American Express Membership Rewards, Capital One Miles, and Citi
ThankYou Points. Wells Fargo's public terms confirm Points Transfer and a 1:1
default but its public non-authenticated page does not enumerate the current
partners; coverage therefore reports that catalog as missing instead of loading
an unverifiable list.

Reviewed one-card reward corrections may live in a focused curated file, such
as `data/official_aeroplan_rates_2026-09-02.json`. Reward-rate lists are
authoritative for that card, so the file must contain the complete reviewed
rate set rather than only the corrected row.

## Database-independent catalog backup

The reviewed JSON files remain the editable source of truth for official data.
In addition, `data/catalog_snapshot_2026-09-02.json` is a Django fixture of the
entire `cardapi` app catalog, including the CardAPI rows that were initially
fetched, stable external IDs, inactive history, reward programs, memberships,
and transfer routes. It contains no API key or user data.

After creating an empty database, rebuild the catalog without making external
requests:

```bash
python manage.py migrate
python manage.py restore_cardapi_snapshot \
  cardapi/data/catalog_snapshot_2026-09-02.json --confirm-replace
```

Refresh the snapshot after reviewed catalog changes:

```bash
python manage.py dumpdata cardapi --indent 2 \
  --output cardapi/data/catalog_snapshot_YYYY-MM-DD.json
```

Do not use this fixture as the hand-edited research format. Make reviewed
changes in the smaller provenance-bearing JSON files, import them, run the
coverage report and tests, and then regenerate the fixture as the reproducible
database checkpoint.

## Read-only card catalog API

The catalog is publicly readable; catalog writes remain limited to the reviewed
imports and synchronization commands.

```text
GET /api/cards/
GET /api/cards/{local_slug}/
POST /api/cards/compare/
POST /api/portfolio/evaluate/
POST /api/portfolio/analyze-candidates/
POST /api/portfolio/recommend/
POST /api/reward-goals/match/
GET /api/issuers/
GET /api/reward-categories/
GET /api/reward-programs/
```

The list response is paginated with 20 cards by default. `page_size` may request
up to 100. Supported list filters are `search`, `issuer`, `card_type`,
`max_annual_fee`, `reward_category`, and `include_discontinued`. Discontinued
cards are excluded by default but remain retrievable directly by slug so an
existing cardholder can still see a legacy product.

List rows contain compact card and issuer summaries. The detail response adds
active reward rates, reward-program capabilities, signup bonuses, statement
credits, perks, and currently effective transfer routes. Internal database IDs,
CardAPI IDs, source keys, synchronization timestamps, and internal provenance
objects are not exposed.

The issuer endpoint is an unpaginated list of active issuers that have at least
one non-discontinued card. Each row includes `active_card_count`. The reward
category endpoint is an unpaginated tree of active, user-facing categories;
root categories contain their active user-facing `children`. Internal CardAPI
aliases are intentionally excluded from this frontend-facing taxonomy.

The reward-program endpoint is an unpaginated, public reference list of active
issuer, airline, hotel, and cash-back programs. Each row contains the stable
`code` accepted by calculation endpoints, along with its display name, reward
unit, and program type. Use the optional `program_type` query parameter to
filter by `issuer`, `airline`, `hotel`, or `cash`. This endpoint exposes valid
goal inputs but does not create or store user goals.

The comparison endpoint requires JWT authentication. It evaluates one purchase
against 2 to 20 cards and returns ranked results only where a defensible dollar
value can be calculated. Example request:

```json
{
  "card_slugs": ["american-express-gold-card", "capital-one-venture-x"],
  "owned_card_slugs": [],
  "category_slug": "dining",
  "amount": "100.00",
  "valuation_strategy": "cash",
  "category_spend_to_date": "0.00"
}
```

Supported valuation strategies are `cash`, `travel_portal`, `transfer`, and
`user`. Transfer and user valuation may provide `custom_cpp`, keyed by reward
program code. Optional purchase context includes `purchase_date`,
`booking_channel`, `booking_portal`, `geographic_scope`, `transaction_method`,
`merchant_eligible`, `enrolled`, and `category_spend_to_date`. If a material
input is missing, that card returns `needs_information` and lists the missing
fields instead of estimating a value. `owned_card_slugs` allows the comparison
service to apply verified companion-card reward unlocks.

The authenticated portfolio endpoint evaluates recurring annual value across
one or more cards and spending buckets. It does not persist the submitted
portfolio. Example request:

```json
{
  "card_slugs": ["american-express-gold-card", "capital-one-venture-x"],
  "spending": [
    {"category_slug": "dining", "annual_amount": "6000.00"},
    {"category_slug": "flights", "annual_amount": "3000.00"}
  ],
  "valuation_strategy": "cash",
  "statement_credit_uses": [
    {
      "card_slug": "american-express-gold-card",
      "credit_name": "Dining Credit",
      "utilization": "0.7500"
    }
  ]
}
```

Each spending bucket may supply the same merchant and booking qualifiers used
by card comparison. Statement credits are included only when explicitly listed,
and `utilization` must be between zero and one. The response assigns each bucket
to its highest-valued card and reports annual spend, reward value, selected
credit value, recurring fees, first-year fees, recurring net value, unresolved
spending, unvalued perk count, and warnings. Signup bonuses are deliberately
excluded because an existing-card portfolio is a recurring-value calculation;
they belong to candidate-card analysis.

The authenticated candidate-analysis endpoint compares a baseline portfolio
with adding each candidate individually. Current portfolios may be empty, and
discontinued cards may be evaluated as cards already owned; discontinued cards
cannot be candidates. Example request:

```json
{
  "current_card_slugs": ["chase-freedom-unlimited-credit-card"],
  "candidate_card_slugs": [
    "chase-sapphire-preferred-credit-card",
    "capital-one-venture-x"
  ],
  "spending": [
    {"category_slug": "dining", "annual_amount": "6000.00"},
    {"category_slug": "travel", "annual_amount": "4000.00"}
  ],
  "valuation_strategy": "cash",
  "statement_credit_uses": [],
  "signup_bonus_uses": [
    {
      "card_slug": "chase-sapphire-preferred-credit-card",
      "eligibility": "eligible",
      "can_meet_minimum_spend": true
    }
  ]
}
```

The response includes the baseline evaluation and one portfolio evaluation per
candidate, incremental recurring value, potential signup-bonus value, included
signup-bonus value, first-year net value, and separate recurring and first-year
ranks. An offer is included in first-year value only when the request explicitly
marks eligibility as `eligible` or `assumed`, confirms the minimum spend can be
met, and the catalog contains complete active offer terms. Without those inputs,
potential value may be shown but is not added to the result.

The authenticated reward-goal endpoint ranks cards by their verified access to
one or more explicitly selected loyalty programs. It distinguishes direct
earning, direct transfer access, and transfer access unlocked by another owned
card. Example request:

```json
{
  "card_slugs": [
    "american-express-gold-card",
    "chase-freedom-unlimited-credit-card"
  ],
  "owned_card_slugs": ["chase-sapphire-preferred-credit-card"],
  "goals": [
    {
      "label": "Air Canada redemption",
      "program_codes": ["aeroplan"],
      "priority": "2.0000"
    }
  ],
  "account_opened_dates": {
    "chase-sapphire-preferred-credit-card": "2024-08-15"
  },
  "as_of": "2026-09-03"
}
```

`card_slugs` are the cards being ranked. `owned_card_slugs` provide portfolio
context for companion-card unlocks but are not added to the card ranking.
Priorities must be positive and determine the `covered_priority` ranking score;
they are relative weights, not cash valuations. If a transfer ratio depends on
when an account was opened and the date is absent, the result is
`needs_information` and identifies the required
`account_opened_dates.{card_slug}` input. The response also includes a portfolio
summary of covered and unresolved goals. Unknown cards and inactive or unknown
program codes are rejected rather than silently ignored.

The authenticated recommendation endpoint automatically considers active cards
as individual additions and one-for-one replacements. It is stateless: saved
goals, owned-card selections, budgets, and spending remain the responsibility
of the calling application. Example request:

```json
{
  "current_card_slugs": ["chase-freedom-unlimited-credit-card"],
  "spending": [
    {"category_slug": "dining", "annual_amount": "6000.00"},
    {"category_slug": "travel", "annual_amount": "4000.00"}
  ],
  "goals": [
    {
      "label": "Air Canada redemption",
      "program_codes": ["aeroplan"],
      "priority": "2.0000"
    }
  ],
  "annual_fee_budget": "695.00",
  "recommendation_priority": "ongoing_value",
  "valuation_strategy": "cash",
  "credit_profile": "good",
  "country": "US",
  "allowed_card_types": ["personal"],
  "issuer_slugs": [],
  "excluded_card_slugs": [],
  "statement_credit_uses": [],
  "signup_bonus_uses": [],
  "result_limit": 10
}
```

`annual_fee_budget` applies to the total recurring fees of the resulting setup,
not merely the candidate card. `recommendation_priority` may be
`ongoing_value`, `first_year_value`, or `goals`; goal-priority requests require
at least one goal. The default candidate pool contains U.S. personal cards,
excludes discontinued products and cards already owned, and may be narrowed by
credit profile, country, card type, or explicit exclusions. Unknown recommended
credit profiles remain eligible and are disclosed rather than treated as
confirmed approval.
To prevent unexpectedly expensive requests as the catalog grows, one request
may evaluate at most 500 addition/replacement actions. `issuer_slugs` can narrow
the candidate pool to active issuers in the selected country.

The response contains the current baseline, the leading feasible actions,
category allocations, goal coverage, recurring and first-year changes, signup
bonus treatment, screening counts, and an explanation for each action. It
returns `keep_current_setup` when no action improves the selected priority and
`insufficient_data` when the selected result cannot be calculated safely. If
the current setup is already over budget, the best feasible replacement may be
recommended even when it reduces reward value; `no_feasible_recommendation`
means the current setup is over budget and no evaluated action satisfies it.
