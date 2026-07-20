from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..jobs import process_run
from ..models import Run, Work
from ..schemas import WorkCreated, WorkOut
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

@router.get("/{id}", response_model=WorkOut)
def get_work(id: int, db: Session = Depends(get_db)):
    work = db.get(Work, id)
    if work is None:
        raise HTTPException(status_code=404, detail=f'Work with id {id} not found')
    return work

@router.get("", response_model=list[WorkOut])
def get_works(db: Session = Depends(get_db)):
    works = db.scalars(
        select(Work)
        .options(selectinload(Work.runs))
        .order_by(Work.id.desc())
        .limit(10)
    ).all()
    return works 