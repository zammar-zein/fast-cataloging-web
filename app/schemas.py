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