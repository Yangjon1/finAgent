import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.expense.runner import resume_expense_run, start_expense_run
from app.core.response import ok
from app.core.security import CurrentUser, require_permission
from app.db import get_db
from app.models.agent import AgentRun
from app.schemas.agent import ExpenseAgentResumeRequest, ExpenseAgentStartRequest

router = APIRouter(prefix="/agent-runs", tags=["agent-runs"])


@router.post("/expenses", dependencies=[Depends(require_permission("agent:expense:run"))])
def start_expense_agent(payload: ExpenseAgentStartRequest, request: Request, user: CurrentUser):
    try:
        result = start_expense_run(payload.report_id, user.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ok({"run_id": result["run_id"], "status": result["status"], "state": result["state"]}, request)


@router.post("/{run_id}/resume", dependencies=[Depends(require_permission("agent:expense:resume"))])
def resume_agent(run_id: str, payload: ExpenseAgentResumeRequest, request: Request, user: CurrentUser):
    try:
        result = resume_expense_run(run_id, payload.decision, user.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ok({"run_id": result["run_id"], "status": result["status"], "state": result["state"]}, request)


@router.get("/{run_id}", dependencies=[Depends(require_permission("agent:expense:read"))])
def get_agent_run(run_id: str, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    run = db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.tenant_id == user.tenant_id))
    if not run:
        raise HTTPException(status_code=404, detail="Agent Run 不存在")
    return ok({"id": run.id, "business_type": run.business_type, "business_id": run.business_id, "graph_name": run.graph_name, "graph_version": run.graph_version, "status": run.status, "human_required": run.human_required, "state": json.loads(run.state_json) if run.state_json else None, "error_message": run.error_message}, request)
