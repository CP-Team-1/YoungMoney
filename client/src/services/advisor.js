import api from './api'

// POST /api/advisor/suggest/
// body:     { owned_cards: string[], goals?: string }
// response: { suggestion: string }
export async function getCardAdvice({ ownedCards, goals = '' }) {
  const { data } = await api.post('/advisor/suggest/', {
    owned_cards: ownedCards,
    goals,
  })
  return data.suggestion
}
