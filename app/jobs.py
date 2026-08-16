from .db import SessionLocal
from .models import Run, Work, Heading
from .pipeline.metadata import fetch_metadata
from .pipeline.generate import generate_candidates
from .pipeline.reconcile import reconcile_label

def process_run(run_id: int) -> None:
    db = SessionLocal()
    try: 
        run = db.get(Run, run_id)
        run.status="running"
        db.commit()

        work = db.get(Work, run.work_id)
        meta = fetch_metadata(work.isbn13)
        if not meta:
            raise ValueError("No metadata found for this ISBN")
        work.title = meta.title
        work.description = meta.description
        work.metadata_source = meta.source
        db.commit()

        candidates = generate_candidates(work.title, work.description)
        for position, cand in enumerate(candidates, start=1):
            match = reconcile_label(cand.label, cand.facet)
            db.add(Heading(
                run_id = run.id,
                proposed_label=cand.label,
                label=match.label if match else None, 
                fast_id = match.fast_id if match else None, 
                facet = match.facet if match else cand.facet, 
                tier = match.tier if match else "no_match",
                source_model = cand.source_model,
                position=position,
            ))

        run.status = "succeeded"
        db.commit()
    except Exception as exc:
        db.rollback()
        run.status = "failed" 
        run.error = str(exc)
        db.commit()
    finally:
        db.close()