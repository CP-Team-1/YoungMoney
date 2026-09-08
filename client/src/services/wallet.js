import api from './api'

function mapOwnedCard(row) {
  return {
    cardSlug: row.card_slug,
    effectiveAnnualFee: row.effective_annual_fee === null ? null : Number(row.effective_annual_fee),
    usedCreditIds: new Set(row.used_credit_ids),
  }
}

export async function getOwnedCards() {
  const { data } = await api.get('/wallet/cards/')
  return data.map(mapOwnedCard)
}

export async function addOwnedCard(cardSlug) {
  const { data } = await api.post('/wallet/cards/', { card_slug: cardSlug })
  return mapOwnedCard(data)
}

export async function removeOwnedCard(cardSlug) {
  await api.delete(`/wallet/cards/${cardSlug}/`)
}

export async function setCreditUse(cardSlug, statementCreditId, used) {
  if (used) {
    await api.post('/wallet/credit-uses/', { card_slug: cardSlug, statement_credit_id: statementCreditId })
  } else {
    await api.delete(`/wallet/credit-uses/${statementCreditId}/`)
  }
}
