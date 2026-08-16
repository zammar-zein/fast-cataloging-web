from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.pipeline.reconcile import reconcile_label

from ..db import get_db
from ..models import Run, Heading, ReviewDecision
from ..schemas import (
    RunOut,
    RunPage,
    DecisionCreate,
    DecisionOut,
    ReviewScreen,
    HeadingCreate,
)

router = APIRouter(prefix="/runs", tags=["runs"])

@router.get("", response_model=RunPage)
def get_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """One page of the chronological runs table, newest first."""
    total = db.scalar(select(func.count()).select_from(Run)) or 0
    runs = db.scalars(
        select(Run)
        .options(selectinload(Run.work))
        .order_by(Run.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [
            {
                "id": r.id,
                "status": r.status,
                "created_at": r.created_at,
                "work_id": r.work_id,
                "isbn13": r.work.isbn13,
                "title": r.work.title,
            }
            for r in runs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }

@router.get("/{run_id}", response_model=RunOut)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail='run not found')
    return run

@router.get("/{run_id}/review", response_model=ReviewScreen)
def get_review_screen(run_id: int, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail='run not found')
    work = run.work

    proposals: dict[str, list] = {}
    for h in run.headings: 
        proposals.setdefault(h.source_model, []).append(h)
    
    rejected_ids = {d.fast_id for d in run.decisions}
    final: dict[str, dict] = {}
    for h in run.headings:
        if h.fast_id is None:
            continue 
        entry = final.setdefault(h.fast_id, {
            "fast_id": h.fast_id,
            "label": h.label, 
            "facet": h.facet,
            "source_models": [],
            "rejected": h.fast_id in rejected_ids,
        })    
        if h.source_model not in entry["source_models"]:
            entry["source_models"].append(h.source_model)
    
    return {
        "isbn13": work.isbn13,
        "title": work.title,
        "description": work.description,
        "metadata_source": work.metadata_source,
        "run_id": run.id,
        "status": run.status,
        "proposals": proposals,
        "final": list(final.values()),
    }

@router.post("/{run_id}/decisions", response_model=DecisionOut)
def create_decision(
    run_id: int,
    payload: DecisionCreate,
    db: Session = Depends(get_db)    
):
    fast_id = payload.fast_id 
    heading = db.scalar(
        select(Heading).where(
            Heading.run_id == run_id, 
            Heading.fast_id == fast_id)
    )
    if heading is None:
        raise HTTPException(status_code=404, detail='Heading not found')
    decision = db.scalar(
        select(ReviewDecision).where(
            ReviewDecision.run_id == run_id,
            ReviewDecision.fast_id == fast_id 
        )
    )
    if decision is not None:
        return decision
    decision = ReviewDecision(
        run_id = run_id,
        fast_id = fast_id, 
        decision = "rejected"
    )
    db.add(decision)
    db.commit()
    db.refresh(decision)
    return decision

@router.delete("/{run_id}/decisions/{fast_id}")
def delete_decision(run_id: int, fast_id: str, db: Session = Depends(get_db)):
    decision = db.scalar(
        select(ReviewDecision).where(
            ReviewDecision.run_id == run_id,
            ReviewDecision.fast_id == fast_id 
        )
    )
    if decision is None:
        raise HTTPException(status_code=404, detail='Decision not found')
    db.delete(decision)
    db.commit()
    return {"undone": True}

@router.post("/{run_id}/headings")
def create_heading(run_id: int, payload: HeadingCreate, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if run is None: 
        raise HTTPException(status_code=404, detail='run not found')
    
    match = reconcile_label(payload.label, payload.facet)
    if match is None:
        raise HTTPException(
            status_code=422,
            detail=f"couldn't authorize {payload.label!r} against FAST — try different wording",
        )
    existing = db.scalar(select(Heading).where(
        Heading.run_id == run_id, Heading.fast_id == match.fast_id))
    if existing is not None:
        raise HTTPException(status_code=409, detail="already in the list")

    rejection = db.scalar(select(ReviewDecision).where(
        ReviewDecision.run_id == run_id,
        ReviewDecision.fast_id == match.fast_id))
    if rejection is not None:
        db.delete(rejection)
    
    heading = Heading(
        run_id=run_id,
        proposed_label=payload.label,
        label=match.label,
        fast_id=match.fast_id,
        facet=match.facet,
        tier=match.tier,
        source_model="cataloger",
        position=len(run.headings) + 1,
    )
    db.add(heading)
    db.commit()
    db.refresh(heading)
    return heading