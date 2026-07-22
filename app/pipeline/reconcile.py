from dataclasses import dataclass

import requests 
import time


ASSIGN_FAST_URL = "https://fast.oclc.org/searchfast/fastsuggest"

@dataclass
class ReconcileHeading:
    fast_id: str
    label: str
    facet: str 
    tier: str 

FACET_INDEX = {
    "personal": "suggest00",
    "corporate": "suggest10",
    "event": "suggest11",
    "title": "suggest30",
    "chronological": "suggest48",
    "topical": "suggest50",
    "geographic": "suggest51",
    "form_genre": "suggest55",
}

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

def best_match(label: str, facet: str = "") -> ReconcileHeading | None:
    docs = suggest(label, facet)
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


def suggest(label: str, facet: str = "", rows: int = 20, attempts: int = 3) -> list[dict]:
    index = FACET_INDEX.get(facet, "suggestall")
    params={
        "query": label,
        "queryIndex": index,
        "queryReturn": f"{index},idroot,auth,tag,type",
        "suggest": "autoSubject",
        "rows": rows,
    }
    for attempt in range(1, attempts + 1): 
        time.sleep(0.3)
        try:
            response = requests.get(ASSIGN_FAST_URL, params=params, timeout=20)
            response.raise_for_status()
            return response.json().get("response", {}).get("docs", [])
        except (requests.RequestException, ValueError):
            if attempt < attempts:
                time.sleep(1.5 * attempt)
    return []

def reconcile_label(label: str, facet: str = "") -> ReconcileHeading | None: 
    original = label 

    match = best_match(label, facet)
    if match is not None: 
        return match 

    if " (" in label:
        match = best_match(label.split(" (")[0], facet)
        if match is not None:
            if match.label.strip().lower() == label.strip().lower():
                match.tier = "exact"
            return match 
    
    while "--" in label: 
        label = label.rsplit("--", 1)[0]
        match = best_match(label, facet) 
        if match is not None: 
            match.tier = "truncated"
            return match

    if "--" not in original and " (" not in original:
        match = best_match(original) 
        if match is not None:
            match.tier = "fuzzy"
            return match 

    return None 