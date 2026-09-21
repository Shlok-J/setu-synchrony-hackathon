"""
Turns model output into a plain-English explanation.

Calls an LLM if an API key is configured (GEMINI_API_KEY -- standing in
for "AWS Bedrock or equivalent" per the problem statement's own wording),
and falls back to a deterministic template if not, so the demo never
breaks because of a missing or rate-limited API key.

Guardrail: the prompt may ONLY rephrase the factors it's given. It is
explicitly told not to introduce new claims or reference demographic
categories -- none are passed to it in the first place.
"""

import os

_SYSTEM_PROMPT = (
    "You explain credit risk scores to loan applicants in one short, plain "
    "English sentence. You may ONLY reference the factors provided to you. "
    "Never introduce information not given. Never reference gender, region, "
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
            # Latency levers for a hosted API call: cap output length (we
            # only need one sentence), and disable extended "thinking" --
            # pure overhead for a task this simple.
            config=types.GenerateContentConfig(
                max_output_tokens=80,
                temperature=0.3,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return response.text.strip()
    except Exception:
        return _template_explanation(top_factors, method)
