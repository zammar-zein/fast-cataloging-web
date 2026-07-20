from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Run, Work
from ..schemas import WorkCreated

router = APIRouter(prefix="/works", tags=["works"])


class WorkCreate(BaseModel):
    isbn13: str


@router.post("", response_model=WorkCreated)
def create_work(payload: WorkCreate, db: Session = Depends(get_db)):
    work = db.scalar(select(Work).where(Work.isbn13 == payload.isbn13))
    if work is None:
        work = Work(isbn13=payload.isbn13)
        db.add(work)
        db.commit()
    
    run = Run(work_id=work.id)
    db.add(run)
    db.commit()
    db.refresh(run)

    return {"work_id": work.id, "run_id": run.id, "status": run.status}