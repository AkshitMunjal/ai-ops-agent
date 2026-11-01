from fastapi import APIRouter, HTTPException, Response
from langgraph.types import Command
from sqlalchemy import select

from agent.checkpointer import open_checkpointer
from agent.graph import build_graph
from agent_api.database import open_session
from agent_api.models import Run
from agent_api.schemas import Decision, NewRun, RunDetail, RunOut

router = APIRouter()

graph = build_graph(open_checkpointer())


def thread_config(run_id):
    return {"configurable": {"thread_id": f"run-{run_id}"}}


def find_run_by_message_id(database_session, message_id):
    statement = select(Run).where(Run.message_id == message_id)
    found_runs = database_session.scalars(statement)
    return found_runs.first()


@router.post("/runs", response_model=RunOut, status_code=201)
def start_run(new_run: NewRun, response: Response):
    with open_session() as database_session:
        if new_run.message_id is not None:
            existing_run = find_run_by_message_id(database_session, new_run.message_id)

            if existing_run is not None:
                response.status_code = 200
                return RunOut.model_validate(existing_run)

        run = Run(email_text=new_run.email_text, message_id=new_run.message_id)
        database_session.add(run)
        database_session.commit()
        database_session.refresh(run)

        try:
            result = graph.invoke(
                {"email_text": run.email_text},
                thread_config(run.id),
            )
        except Exception as error:
            run.status = "error"
            run.problems = str(error)
        else:
            if "__interrupt__" in result:
                run.status = "waiting_for_approval"
                run.draft_order_id = result["draft_order"]["id"]
            else:
                run.status = result["status"]
                run.problems = "; ".join(result.get("problems", []))

        database_session.commit()
        database_session.refresh(run)
        return RunOut.model_validate(run)


@router.get("/runs", response_model=list[RunOut])
def list_runs(status: str | None = None):
    statement = select(Run).order_by(Run.id.desc())
    if status is not None:
        statement = statement.where(Run.status == status)

    with open_session() as database_session:
        found_runs = database_session.scalars(statement)
        runs = found_runs.all()
        return [RunOut.model_validate(run) for run in runs]


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: int):
    with open_session() as database_session:
        run = database_session.get(Run, run_id)

        if run is None:
            raise HTTPException(status_code=404, detail="Run not found.")

        run_detail = RunDetail.model_validate(run)

    saved_state = graph.get_state(thread_config(run_id))
    run_detail.understood = saved_state.values.get("matched_order")
    return run_detail


@router.post("/runs/{run_id}/decision", response_model=RunOut)
def decide_run(run_id: int, decision: Decision):
    with open_session() as database_session:
        run = database_session.get(Run, run_id)

        if run is None:
            raise HTTPException(status_code=404, detail="Run not found.")

        if run.status != "waiting_for_approval":
            raise HTTPException(
                status_code=409,
                detail="This run is not waiting for approval.",
            )

        try:
            result = graph.invoke(
                Command(resume=decision.decision),
                thread_config(run.id),
            )
        except Exception as error:
            run.status = "error"
            run.problems = str(error)
        else:
            run.status = result["status"]
            run.problems = "; ".join(result.get("problems", []))

        database_session.commit()
        database_session.refresh(run)
        return RunOut.model_validate(run)