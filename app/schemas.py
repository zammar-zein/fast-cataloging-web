from datetime import datetime

from pydantic import BaseModel, ConfigDict

class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    error: str | None 
    created_at: datetime 

class WorkCreated(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    work_id: int
    run_id: int
    status: str