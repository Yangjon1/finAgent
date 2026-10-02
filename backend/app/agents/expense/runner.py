import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.agents.expense.graph import ExpenseGraph
from app.core.config import get_settings
from app.db import SessionLocal
from app.models.agent import AgentRun
from app.models.expense import ExpenseReport

graph = ExpenseGraph(SessionLocal)


def _save_run(run_id: str, state: dict, status: str, human_required: bool = False, error_message: str | None = None) -> None:
    db = SessionLocal()
    try:
        run = db.scalar(select(AgentRun).where(AgentRun.id == run_id))
        if not run:
            return
        run.status = status
        run.human_required = human_required
        run.state_json = json.dumps(state, ensure_ascii=False, default=str)
        run.output_json = json.dumps(state, ensure_ascii=False, default=str)
        run.error_message = error_message
        if status in {"SUCCEEDED", "HUMAN_REVIEW", "FAILED"}:
            run.ended_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


def start_expense_run(report_id: str, tenant_id: str) -> dict:
    run_id = str(uuid4())
    db = SessionLocal()
    try:
        report = db.scalar(select(ExpenseReport).where(ExpenseReport.id == report_id, ExpenseReport.tenant_id == tenant_id))
        if not report:
            raise ValueError("报销单不存在")
        run = AgentRun(id=run_id, tenant_id=tenant_id, business_type="expense", business_id=report_id, graph_name=graph.name, graph_version=graph.version, status="RUNNING", model_name=None)
        db.add(run)
        db.commit()
    finally:
        db.close()
    try:
        state = graph.invoke({"run_id": run_id, "report_id": report_id, "tenant_id": tenant_id, "errors": []})
        interrupted = bool(state.get("__interrupt__"))
        _save_run(run_id, state, "HUMAN_REVIEW" if interrupted else "SUCCEEDED", interrupted)
        return {"run_id": run_id, "status": "HUMAN_REVIEW" if interrupted else "SUCCEEDED", "state": state}
    except Exception as exc:
        _save_run(run_id, {"run_id": run_id, "report_id": report_id}, "FAILED", False, str(exc))
        raise


def resume_expense_run(run_id: str, decision: str, tenant_id: str) -> dict:
    db = SessionLocal()
    try:
        run = db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.tenant_id == tenant_id))
        if not run:
            raise ValueError("Agent Run 不存在")
    finally:
        db.close()
    state = graph.resume(run_id, decision)
    _save_run(run_id, state, "SUCCEEDED", False)
    return {"run_id": run_id, "status": "SUCCEEDED", "state": state}
