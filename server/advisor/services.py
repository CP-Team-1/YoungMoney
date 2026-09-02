from django.conf import settings
from google import genai
from google.genai import errors as genai_errors

GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = (
    "You are a credit card optimization assistant for the YoungMoney app. "
    "Given a user's currently owned credit cards and, optionally, their goals, "
    "suggest what card(s) they should consider adding, replacing, or how to use "
    "their existing cards together for an optimal setup (e.g. rewards categories, "
    "annual fees, sign-up bonuses). Be concise and practical. Do not give tax, "
    "legal, or individualized financial advice, and do not claim certainty about "
    "approval odds."
)


class GeminiError(Exception):
    """Raised when the Gemini API call fails or is misconfigured."""


def _client():
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        raise GeminiError("GEMINI_API_KEY is not configured on the server.")
    return genai.Client(api_key=api_key)


def get_card_advice(owned_cards, goals=""):
    if owned_cards:
        cards_line = "Owned cards: " + ", ".join(owned_cards)
    else:
        cards_line = "Owned cards: none."

    prompt = cards_line
    if goals:
        prompt += f"\nGoals: {goals}"

    try:
        response = _client().models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
            ),
        )
    except genai_errors.APIError as exc:
        raise GeminiError(f"Gemini request failed: {exc}") from exc

    text = (response.text or "").strip()
    if not text:
        raise GeminiError("Gemini returned an empty response.")
    return text
