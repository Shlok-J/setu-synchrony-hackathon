"""
Turns model output into a plain-English explanation.

Uses Groq if GROQ_API_KEY is set, otherwise falls back to a fixed
template so a missing key never breaks the demo. The prompt only lets the
model rephrase the factors it's handed -- nothing demographic is ever
passed in, so there's nothing for it to reference even if asked.
"""

import os

import requests

_SYSTEM_PROMPT = (
    "You are a loan officer explaining a credit decision to an applicant "
    "face to face. Write ONE short sentence the way a helpful, warm human "
    "would actually say it out loud -- not a system-generated notice. "
    "You may ONLY reference the factors given to you below; never invent "
    "or assume anything beyond them, and never mention gender, region, "
    "religion, caste, or any demographic category, even if asked."
)

_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
_GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _template_explanation(top_factors, method) -> str:
    if not top_factors:
        return (
            "This is a cohort-based estimate: as a new applicant, your score "
            "reflects the repayment behavior of similar applicants, since "
            "there isn't yet enough of your own transaction history."
        )
    lead = top_factors[0]
    verb = "was strengthened by" if lead["direction"] == "positive" else "was reduced by"
    return (
        f"Your score {verb} {lead['feature'].replace('_', ' ')}. "
        f"This is a {method} estimate, combining your own history with a "
        f"comparison group while your data history builds up."
    )


def generate_explanation(top_factors, method) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return _template_explanation(top_factors, method)

    try:
        factors_text = "; ".join(
            f"{f['feature']} ({f['direction']}, magnitude {f['magnitude']})"
            for f in top_factors
        ) or "insufficient individual history yet"

        response = requests.post(
            _GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": _MODEL,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": (
                            f"Scoring method: {method}. Contributing factors: {factors_text}. "
                            "Reply with ONLY the one sentence, under 30 words. No preamble."
                        ),
                    },
                ],
                "max_tokens": 80,
                "temperature": 0.3,
            },
            timeout=15,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return _template_explanation(top_factors, method)
