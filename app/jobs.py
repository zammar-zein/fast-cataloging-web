from .db import SessionLocal
from .models import Run 

def process_run(run_id: int) -> None:
    db = SessionLocal()
    try: 
        run = db.get(Run, run_id)
        run.status="running"
        db.commit()
        # some stuff
        run.status = "succeeded"
        db.commit()
    except Exception as exc:
        run.status = "failed" 
        run.error = str(exc)
        db.commit()
    finally:
        db.close()