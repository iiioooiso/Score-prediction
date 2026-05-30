from typing import Optional


def build_prompt(conversation: str, facet_name: str, description: str) -> str:
    """Construct a concise, strict instruction prompt that asks for JSON-only output."""
    conversation = (conversation or "").strip()
    facet_name = (facet_name or "").strip()
    description = (description or "").strip()

    prompt = (
        "You are an evaluator. Given a conversation, a facet name, and a facet description, "
        "output ONLY a single JSON object with EXACTLY these fields:\n"
        "- score: integer 1-5 (1=Strong evidence against, 2=Weak evidence against, "
        "3=Insufficient evidence / Unknown, 4=Weak evidence for, 5=Strong evidence for)\n"
        "- confidence: float between 0.0 and 1.0 indicating confidence in the score\n"
        "- reason: a concise one-sentence justification citing evidence from the conversation.\n\n"
        "Conversation:\n" + conversation + "\n\n"
        "Facet:\n" + facet_name + "\n\n"
        "Description:\n" + description + "\n\n"
        "Return only valid JSON (no markdown, no surrounding text)."
    )
    return prompt


def build_batch_prompt(conversation: str, facets: list) -> str:
    """Build a prompt that asks the model to score multiple facets in a single JSON array.

    `facets` is a list of dicts each with keys: facet_id, facet_name, description
    """
    conversation = (conversation or "").strip()
    lines = ["You are an evaluator. Given a conversation and multiple facets, output ONLY a JSON array of objects."]
    lines.append("Each object must contain exactly these fields: facet_id (int), score (int 1-5), confidence (float 0.0-1.0), reason (short string), evidence (array of short supporting snippets).")
    lines.append("Do NOT include any surrounding text or markdown. Use double quotes for JSON.")
    lines.append("")
    lines.append("Conversation:")
    lines.append(conversation)
    lines.append("")
    lines.append("Facets:")
    for f in facets:
        fid = f.get("facet_id")
        name = f.get("facet_name", "")
        desc = f.get("description", "")
        lines.append(f"- facet_id: {fid}\n  name: {name}\n  description: {desc}")
    lines.append("")
    lines.append("Example output:\n[\n  {\n    \"facet_id\": 12,\n    \"score\": 3,\n    \"confidence\": 0.72,\n    \"reason\": \"Insufficient evidence in the conversation.\",\n    \"evidence\": []\n  },\n  {\n    \"facet_id\": 24,\n    \"score\": 5,\n    \"confidence\": 0.92,\n    \"reason\": \"Clear first-person statement indicating this trait.\",\n    \"evidence\": [\"I feel exhausted\", \"I can't enjoy things\"]\n  }\n]")
    lines.append("")
    lines.append("Return only the JSON array.")
    return "\n".join(lines)
