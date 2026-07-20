from .db import SessionLocal
from .models import Run, Work
from .pipeline.metadata import fetch_metadata

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
        run.status = "succeeded"
        db.commit()
    except Exception as exc:
        run.status = "failed" 
        run.error = str(exc)
        db.commit()
    finally:
        db.close()