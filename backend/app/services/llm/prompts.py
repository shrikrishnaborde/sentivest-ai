"""Prompt templates for the report-generation LLM call.

The system prompt is deliberately strict about grounding: the model is
told to synthesize *only* from the supplied context and to flag when
evidence is thin, so the platform never presents unsupported opinion as
fact.
"""

SYSTEM_PROMPT = """\
You are a financial market analyst assistant for SentiVest AI. You write \
concise, evidence-grounded sentiment reports about publicly traded stocks.

Rules:
- Base every claim ONLY on the numbered source excerpts provided. Never use \
outside knowledge about the company, and never speculate beyond the evidence.
- Cite sources inline using their number, e.g. "[2]", next to each claim.
- If the provided sources are thin, contradictory, or insufficient to answer \
confidently, say so explicitly rather than guessing.
- Be neutral and analytical in tone — this is investor research, not advice. \
Never tell the user to buy, sell, or hold.
- Keep the summary tight: 3-6 sentences.
"""

USER_PROMPT_TEMPLATE = """\
Stock: {company_name} ({ticker})
Question: {query}

Source excerpts (numbered, most relevant first):
{context_block}

Respond ONLY with a JSON object matching this schema:
{{
  "summary": "3-6 sentence evidence-grounded narrative answering the question, with inline [n] citations",
  "positive_drivers": ["short phrase", ...],
  "negative_drivers": ["short phrase", ...],
  "key_themes": ["short phrase", ...]
}}
"""


def build_context_block(chunks: list[str]) -> str:
    return "\n\n".join(f"[{i + 1}] {chunk}" for i, chunk in enumerate(chunks))


def build_user_prompt(company_name: str, ticker: str, query: str, context_chunks: list[str]) -> str:
    return USER_PROMPT_TEMPLATE.format(
        company_name=company_name,
        ticker=ticker,
        query=query,
        context_block=build_context_block(context_chunks),
    )
