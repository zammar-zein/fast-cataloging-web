from dataclasses import dataclass

import requests 

from ..config import Settings 

settings = Settings() 

HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
OPUS = "us.anthropic.claude-opus-4-5-20251101-v1:0"

@dataclass
class CandidateHeading:
    label: str
    facet: str
    source_model: str

PROMPT = """You are a subject-cataloging assistant. Given a book's metadata, \
propose FAST (Faceted Application of Subject Terminology) subject headings \
describing what the book is about.

Rules:
- topical: subjects the book is about. geographic: places it substantively \
covers, as their own headings (never folded into a topical heading). \
form_genre: what the book IS (e.g. "Textbooks", "Dictionaries"), only when \
evident.
- Prefer established FAST wording. FAST headings are single-concept: never \
build compound "Topic--Place--Form" strings.
- At most {max_headings} headings, ordered from most to least central.
- If the metadata is too thin to judge, return fewer headings rather than \
guessing.
- Use "personal" for people, including fictitious characters; "corporate" \
for organizations.
- Never append form subdivisions such as "--Fiction" to a heading; \
express form only as its own form_genre heading.

Book metadata:
  Title: {title}
  Description: {description}"""

HEADINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "headings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "The FAST subject heading text.",
                    },
                    "facet": {
                        "type": "string",
                        "enum": ["topical", "geographic", "form_genre", "personal", "corporate", "event", "chronological"],
                    },
                },
                "required": ["label", "facet"]
            },
        },
    },
    "required": ["headings"],
}

def generate_candidates(title: str, description: str | None,
                        max_headings: int = 10,
                        model: str = HAIKU) -> list[CandidateHeading]:
    prompt = PROMPT.format(
        max_headings=max_headings,
        title=title,
        description=description or "(none available)",
    )
    result = call_claude(prompt, HEADINGS_SCHEMA, model)
    return [
        CandidateHeading(label=h["label"], facet=h["facet"], source_model=model)
        for h in result.get("headings", [])
    ]

def call_claude(prompt: str, schema: dict, model: str = HAIKU) -> dict:
    response = requests.post(
        f"{settings.huit_api_base_url}/model/{model}/invoke",
        headers={"api-key": settings.huit_api_key},
        json={
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}],
            "tools": [{
                "name": "record_result",
                "description": "Record the resut in the required structure.",
                "input_schema": schema,
            }],
            "tool_choice": {"type": "tool", "name": "record_result"}
        },
        timeout=120,
    )
    response.raise_for_status()
    for block in response.json()["content"]:
        if block["type"] == "tool_use":
            return block["input"]
    raise ValueError("no structured block in model response")