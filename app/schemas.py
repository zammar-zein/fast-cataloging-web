from datetime import datetime

from pydantic import BaseModel, ConfigDict

class HeadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proposed_label: str
    label: str | None
    fast_id: str | None
    facet: str
    tier: str 
    source_model: str 
    position: int

class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    error: str | None 
    created_at: datetime 
    headings: list[HeadingOut]

class WorkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn13: str
    title: str | None
    description: str | None
    runs: list[RunOut]

class WorkCreated(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    work_id: int
    run_id: int
    status: str

class RunListItem(BaseModel):
    """One row of the chronological runs table (history view)."""
    id: int
    status: str
    created_at: datetime
    work_id: int
    isbn13: str
    title: str | None

class RunPage(BaseModel):
    """One page of the runs table plus what the pager needs."""
    items: list[RunListItem]
    total: int
    page: int
    page_size: int

class DecisionCreate(BaseModel):
    fast_id: str

class DecisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int 
    fast_id: str 
    decision: str 
    created_at: datetime

class FinalEntry(BaseModel):
    fast_id: str
    label: str | None
    facet: str
    source_models: list[str]      # who voted for it 
    rejected: bool                # UI renders strikethrough + undo button

class ReviewScreen(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    isbn13: str
    title: str | None
    description: str | None
    metadata_source: str | None
    run_id: int
    status: str
    proposals: dict[str, list[HeadingOut]]   # per model, tiers visible
    final: list[FinalEntry]

class HeadingCreate(BaseModel):
    label: str 
    facet: str = ""