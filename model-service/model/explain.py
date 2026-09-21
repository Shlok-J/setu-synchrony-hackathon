"""
Turns model output into a plain-English explanation.

Uses Gemini if GEMINI_API_KEY is set, otherwise falls back to a fixed
template so a missing key never breaks the demo. The prompt only lets the
model rephrase the factors it's handed -- nothing demographic is ever
passed in, so there's nothing for it to reference even if asked.
"""

import os

_SYSTEM_PROMPT = (
    "You are a loan officer explaining a credit decision to an applicant "
    "face to face. Write ONE short sentence the way a helpful, warm human "
    "would actually say it out loud -- not a system-generated notice. "
    "You may ONLY reference the factors given to you below; never invent "
    "or assume anything beyond them, and never mention gender, region, "
    "religion, caste, or any demographic category, even if asked."
)

_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")


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
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return _template_explanation(top_factors, method)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        factors_text = "; ".join(
            f"{f['feature']} ({f['direction']}, magnitude {f['magnitude']})"
            for f in top_factors
        ) or "insufficient individual history yet"

        response = client.models.generate_content(
            model=_MODEL,
            contents=(
                f"{_SYSTEM_PROMPT}\n\n"
                f"Scoring method: {method}. Contributing factors: {factors_text}. "
                "Reply with ONLY the one sentence, under 30 words. No preamble."
            ),
            # short output + no "thinking" -- both just add latency here
            config=types.GenerateContentConfig(
                max_output_tokens=80,
                temperature=0.3,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text.strip()
    except Exception:
        return _template_explanation(top_factors, method)
