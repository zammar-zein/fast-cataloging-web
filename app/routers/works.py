from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..jobs import process_run
from ..models import Run, Work
from ..schemas import WorkCreated
from ..pipeline.isbn import normalize

router = APIRouter(prefix="/works", tags=["works"])


class WorkCreate(BaseModel):
    isbn13: str


@router.post("", response_model=WorkCreated)
def create_work(
    payload: WorkCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        isbn13 = normalize(payload.isbn13)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    work = db.scalar(select(Work).where(Work.isbn13 == isbn13))
    if work is None:
        work = Work(isbn13=isbn13)
        db.add(work)
        db.commit()
    
    run = Run(work_id=work.id)
    db.add(run)
    db.commit()
    db.refresh(run)

    background_tasks.add_task(process_run, run.id)

    return {"work_id": work.id, "run_id": run.id, "status": run.status}