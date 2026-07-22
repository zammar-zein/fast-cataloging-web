from dataclasses import dataclass

import requests 

ASSIGN_FAST_URL = "https://fast.oclc.org/searchfast/fastsuggest"

@dataclass
class ReconcileHeading:
    fast_id: str
    label: str
    facet: str 
    tier: str 


TAG_TO_FACET = {
    "100": "personal",
    "110": "corporate",
    "111": "event",
    "130": "title",
    "147": "event",
    "148": "chronological",
    "150": "topical",
    "151": "geographic",
    "155": "form_genre",
}

def _clean_id(value) -> str | None:
    if isinstance(value, list):
        value = value[0] if value else None 
    if value is None: 
        return None 
    digits = str(value).removeprefix("fst").lstrip("0")
    return digits or None 

def best_match(label: str) -> ReconcileHeading | None:
    docs = suggest(label)
    if not docs:
        return None # unsearchable label 

    def build(doc: dict, tier: str) -> ReconcileHeading | None:
        fast_id = _clean_id(doc.get("idroot"))
        if fast_id is None: 
            return None 
        return ReconcileHeading(
            fast_id=fast_id,
            label=doc.get("auth", ""),
            facet=TAG_TO_FACET.get(str(doc.get("tag")), "other"),
            tier=tier
        )
    
    # an exact authorized form match beats the API's own ranking
    for doc in docs:
        if doc.get("auth", "").strip().lower() == label.strip().lower():
            return build(doc, "exact")
    
    first = docs[0]
    tier = "variant" if first.get("type") == "alt" else "fuzzy"
    return build(first, tier)


def suggest(label: str, rows: int = 20) -> list[dict]:
    response = requests.get(
        ASSIGN_FAST_URL,
        params={
            "query": label,
            "queryIndex": "suggestall",
            "queryReturn": "suggestall,idroot,auth,tag,type",
            "suggest": "autoSubject",
            "rows": rows,
        },
        timeout=20
    )
    response.raise_for_status()
    return response.json().get("response", {}).get("docs", [])

def reconcile_label(label: str) -> ReconcileHeading | None: 
    match = best_match(label)
    if match is not None: 
        return match 
    
    while "--" in label: 
        label = label.rsplit("--", 1)[0]
        match = best_match(label) 
        if match is not None: 
            match.tier = "truncated"
            return match
    
    return None 