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
    
    return title_only