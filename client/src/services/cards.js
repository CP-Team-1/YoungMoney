import api from './api'

function formatRate(rate) {
  const multiplier = Number(rate.rate_multiplier)
  const suffix = rate.rate_type === 'percent_cashback' ? '%' : 'x'
  const target = rate.is_base_rate ? 'everything else' : rate.category.category
  return `${multiplier}${suffix} on ${target}`
}

function buildHighlights(rewardRates) {
  const active = (rewardRates || []).filter((r) => !r.is_rotating)
  const baseRates = active.filter((r) => r.is_base_rate)
  const categoryRates = active.filter((r) => !r.is_base_rate)

  const bestByCategory = new Map()
  for (const rate of categoryRates) {
    const key = rate.category.slug
    const existing = bestByCategory.get(key)
    if (!existing || Number(rate.rate_multiplier) > Number(existing.rate_multiplier)) {
      bestByCategory.set(key, rate)
    }
  }

  const topCategories = [...bestByCategory.values()]
    .sort((a, b) => Number(b.rate_multiplier) - Number(a.rate_multiplier))
    .map(formatRate)

  const base = baseRates[0] ? [formatRate(baseRates[0])] : []

  const highlights = [...topCategories, ...base]
  return highlights.length ? highlights : ['Reward rate details not yet available']
}

function periodSuffix(period) {
  switch (period) {
    case 'annual': return '/yr'
    case 'semi_annual': return '/6mo'
    case 'quarterly': return '/qtr'
    case 'monthly': return '/mo'
    default: return ''
  }
}

function buildPerkHighlights(perks) {
  const list = (perks || []).map((p) => p.name)
  return list.length ? list : ['No perks listed']
}

function buildCreditHighlights(statementCredits) {
  const list = (statementCredits || []).map(
    (c) => `${c.name}: $${Number(c.amount)}${periodSuffix(c.period)}`
  )
  return list.length ? list : ['No statement credits listed']
}

function gcd(a, b) {
  return b === 0 ? a : gcd(b, a % b)
}

function formatTransferRatio(sourceAmount, destinationAmount) {
  const source = Math.round(Number(sourceAmount))
  const destination = Math.round(Number(destinationAmount))
  const divisor = gcd(source, destination) || 1
  return `${source / divisor}:${destination / divisor}`
}

function buildTransferPartnerHighlights(transferPartners) {
  return (transferPartners || []).map(
    (t) => `${formatTransferRatio(t.source_amount, t.destination_amount)} to ${t.destination_program.name}`
  )
}

function mapStatementCredits(statementCredits) {
  return (statementCredits || []).map((c) => ({
    id: c.id,
    name: c.name,
    amount: Number(c.amount),
    period: c.period,
    annualizedAmount: c.annualized_amount === null ? null : Number(c.annualized_amount),
  }))
}

function stripCardSuffix(name) {
  return name.replace(/\s+(credit\s+)?card$/i, '')
}

function stripSubstring(text, needle) {
  if (!text || !needle) return text
  const idx = text.toLowerCase().indexOf(needle.toLowerCase())
  if (idx === -1) return text
  return text.slice(0, idx) + text.slice(idx + needle.length)
}

function cleanupText(text, fallback) {
  const cleaned = text
    .replace(/\s+[®™℠]$/, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
  return cleaned || fallback
}

function stripIssuerFromReward(rewardText, issuerName) {
  return cleanupText(stripSubstring(rewardText, issuerName), rewardText)
}

function stripTrailingWord(text, word) {
  return text.replace(new RegExp(`\\s+${word}$`, 'i'), '')
}

function buildDisplayName(rawName, issuerName) {
  let name = stripCardSuffix(rawName)
  name = stripSubstring(name, 'credit card')
  name = stripSubstring(name, issuerName)
  name = stripSubstring(name, 'Visa')
  name = stripSubstring(name, 'Mastercard')
  name = cleanupText(name, rawName)
  name = stripTrailingWord(name, 'from')
  return cleanupText(name, rawName)
}

function mapCard(item, detail) {
  const issuerName = item.issuer?.name ?? ''
  return {
    id: item.slug,
    name: buildDisplayName(item.name, issuerName),
    issuer: item.issuer?.name ?? 'Unknown',
    network: item.network,
    cardType: item.card_type,
    annualFee: Number(item.annual_fee),
    maxEffectiveAnnualFee: detail.max_effective_annual_fee === null ? null : Number(detail.max_effective_annual_fee),
    statementCredits: mapStatementCredits(detail.statement_credits),
    rewardType: stripIssuerFromReward(item.reward_currency_name || item.reward_currency || '', issuerName),
    rewardHighlights: buildHighlights(detail.reward_rates),
    perkHighlights: buildPerkHighlights(detail.perks),
    creditHighlights: buildCreditHighlights(detail.statement_credits),
    transferPartnerHighlights: buildTransferPartnerHighlights(detail.transfer_partners),
    signupBonus: 'None',
    productUrl: item.product_url,
  }
}

export async function getCards() {
  const { data } = await api.get('/cards/', { params: { page_size: 100 } })
  const details = await Promise.all(
    data.results.map((item) => api.get(`/cards/${item.slug}/`).then((res) => res.data))
  )
  return data.results.map((item, i) => mapCard(item, details[i]))
}
