from fastapi import APIRouter, HTTPException

from agent_api.database import open_session
from agent_api.models import Run
from agent_api.schemas import RunOut

router = APIRouter()

reviewable_statuses = ["needs_review", "error", "approval_failed"]


@router.post("/runs/{run_id}/dismiss", response_model=RunOut)
def dismiss_run(run_id: int):
    with open_session() as database_session:
        run = database_session.get(Run, run_id)

        if run is None:
            raise HTTPException(status_code=404, detail="Run not found.")

        if run.status not in reviewable_statuses:
            raise HTTPException(
                status_code=409,
                detail="Only runs that need review can be dismissed.",
            )

        run.status = "dismissed"
        database_session.commit()
        database_session.refresh(run)
        return RunOut.model_validate(run)