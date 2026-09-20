"""
Turns model output into a plain-English explanation.

Calls an LLM if an API key is configured (ANTHROPIC_API_KEY -- standing in
for "AWS Bedrock or equivalent" per the problem statement's own wording,
and Bedrock can itself serve Claude models), and falls back to a
deterministic template if not, so the demo never breaks because of a
missing or rate-limited API key.

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
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return _template_explanation(top_factors, method)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        factors_text = "; ".join(
            f"{f['feature']} ({f['direction']}, magnitude {f['magnitude']})"
            for f in top_factors
        ) or "insufficient individual history yet"

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            system=_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"Scoring method: {method}. Contributing factors: {factors_text}. "
                    "Write one sentence explaining this score to the applicant."
                ),
            }],
        )
        return response.content[0].text.strip()
    except Exception:
        return _template_explanation(top_factors, method)
