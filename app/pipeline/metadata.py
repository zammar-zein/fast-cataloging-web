from dataclasses import dataclass
import requests 
from ..config import Settings

settings = Settings()

@dataclass 
class BookMetadata:
    title: str 
    description: str | None = None 
    authors: list[str] | None = None 
    language: str | None = None 
    source: str = "" # which service found it

def fetch_google_books(isbn13: str) -> BookMetadata | None:
    params = {"q": f"isbn:{isbn13}"}
    if settings.google_books_api_key:
        params["key"] = settings.google_books_api_key
    response = requests.get(
        'https://www.googleapis.com/books/v1/volumes', 
        params=params,
        timeout=15
        )
    response.raise_for_status()
    data = response.json()

    if data.get("totalItems", 0) == 0:
        return None 
    
    info = data["items"][0]["volumeInfo"]

    title = info.get("title")
    if not title:
        return None 
    
    return BookMetadata(
        title=title,
        description=info.get("description"),
        authors=info.get("authors"),
        language=info.get("language"),
        source="google_books"
    )

def fetch_open_library(isbn13: str) -> BookMetadata | None:
    response = requests.get(
        f'https://openlibrary.org/isbn/{isbn13}.json',
        timeout=15
    )
    if response.status_code == 404:
        return None 
    response.raise_for_status()
    data = response.json()

    title = data.get("title")
    if not title:
        return None
    description = data.get("description")
    if isinstance(description, dict):
        description = description.get("value")

    language = None 
    langs = data.get("languages")
    if langs: 
        language = langs[0]["key"].split("/")[-1]
    
    if description is None:
        works = data.get("works")
        if works:
            work_resp = requests.get(
                f"https://openlibrary.org{works[0]['key']}.json",
                timeout=15,
            )
            if work_resp.ok:
                description = work_resp.json().get("description")
                if isinstance(description, dict):
                    description = description.get("value")
    
    return BookMetadata(
        title=title,
        description=description,
        language=language,
        source="open_library"
    )

# What the web-search distiller must return. `matches` is the wrong-book
# guard: search results for obscure ISBNs are often about a DIFFERENT book,
# and a wrong description silently poisons every heading downstream.
_DISTILL_SCHEMA = {
    "type": "object",
    "properties": {
        "matches": {
            "type": "boolean",
            "description": "true ONLY if the search results clearly and "
                           "unambiguously describe this exact book",
        },
        "title": {"type": ["string", "null"]},
        "description": {
            "type": ["string", "null"],
            "description": "3-5 factual sentences about the book's subject "
                           "matter, written from the search results",
        },
    },
    "required": ["matches"],
}

_DISTILL_PROMPT = """You are helping catalog a book. Below are web search \
results for ISBN {isbn13}{title_hint}.

If — and only if — the results clearly describe this exact book, write a \
factual 3-5 sentence description of its subject matter (no marketing fluff). \
If the results are about a different book, are ambiguous, or say nothing \
substantive about this book's content, report matches=false.

Search results:
{snippets}"""


def fetch_web_search(isbn13: str, known_title: str | None = None) -> BookMetadata | None:
    """Last-resort metadata via web search (Tavily) + model distillation.

    LOWEST-TRUST source: only accepted when the distiller confirms the
    results describe this exact book. Disabled (returns None) when no
    TAVILY_API_KEY is configured.
    """
    if not settings.tavily_api_key:
        return None

    query = f'"{isbn13}" book'
    if known_title:
        query = f'"{known_title}" {isbn13} book'

    response = requests.post(
        "https://api.tavily.com/search",
        json={
            "api_key": settings.tavily_api_key,
            "query": query,
            "max_results": 5,
        },
        timeout=30,
    )
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        return None

    snippets = "\n\n".join(
        f"[{r.get('url', '')}]\n{r.get('title', '')}\n{r.get('content', '')}"
        for r in results
    )
    title_hint = f' (title: "{known_title}")' if known_title else ""

    # local import to avoid a circular dependency at module load
    from .generate import OPUS, call_claude

    verdict = call_claude(
        _DISTILL_PROMPT.format(isbn13=isbn13, title_hint=title_hint,
                               snippets=snippets[:8000]),
        _DISTILL_SCHEMA,
        model=OPUS,
    )
    if not verdict.get("matches") or not verdict.get("description"):
        return None

    title = known_title or verdict.get("title")
    if not title:
        return None
    return BookMetadata(
        title=title,
        description=verdict["description"],
        source="web_search",
    )


def fetch_metadata(isbn13: str) -> BookMetadata | None:
    sources = [fetch_google_books, fetch_open_library]
    title_only: BookMetadata | None = None
    for fetch in sources:
        try:
            record = fetch(isbn13)
        except requests.RequestException:
            continue # Possibly out of API calls

        if record is None: # source doesn't know about this isbn
            continue

        if record.description:
            return record

        if title_only is None:
            title_only = record

    # Last rung: web search — rescue a total miss, or enrich a thin record
    # with a description. Fail-open: any trouble here just means we return
    # whatever the library sources gave us.
    try:
        web = fetch_web_search(
            isbn13,
            known_title=title_only.title if title_only else None,
        )
    except (requests.RequestException, ValueError):
        web = None

    if web is not None:
        if title_only is not None:
            # keep the library record's fields, graft on the web description
            title_only.description = web.description
            title_only.source = f"{title_only.source}+web_search"
            return title_only
        return web

    return title_only