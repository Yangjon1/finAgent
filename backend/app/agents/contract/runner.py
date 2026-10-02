import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from app.agents.contract.graph import ContractGraph
from app.db import SessionLocal
from app.models.agent import AgentRun
from app.models.contract import Contract

graph = ContractGraph(SessionLocal)


def save_run(run_id: str, state: dict, status: str, human_required: bool = False, error_message: str | None = None):
    db = SessionLocal()
    try:
        run = db.scalar(select(AgentRun).where(AgentRun.id == run_id))
        if run:
            run.status = status
            run.human_required = human_required
            run.state_json = json.dumps(state, ensure_ascii=False, default=str)
            run.output_json = run.state_json
            run.error_message = error_message
            if status in {"SUCCEEDED", "HUMAN_REVIEW", "FAILED"}:
                run.ended_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()


def start_contract_run(contract_id: str, tenant_id: str) -> dict:
    run_id = str(uuid4())
    db = SessionLocal()
    try:
        contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.tenant_id == tenant_id))
        if not contract:
            raise ValueError("合同不存在")
        db.add(AgentRun(id=run_id, tenant_id=tenant_id, business_type="contract", business_id=contract_id, graph_name=graph.name, graph_version=graph.version, status="RUNNING"))
        db.commit()
    finally:
        db.close()
    try:
        state = graph.invoke({"run_id": run_id, "contract_id": contract_id, "tenant_id": tenant_id, "errors": []})
        interrupted = bool(state.get("__interrupt__"))
        save_run(run_id, state, "HUMAN_REVIEW" if interrupted else "SUCCEEDED", interrupted)
        return {"run_id": run_id, "status": "HUMAN_REVIEW" if interrupted else "SUCCEEDED", "state": state}
    except Exception as exc:
        save_run(run_id, {"run_id": run_id, "contract_id": contract_id}, "FAILED", False, str(exc))
        raise


def resume_contract_run(run_id: str, decision: str, tenant_id: str) -> dict:
    db = SessionLocal()
    try:
        run = db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.tenant_id == tenant_id, AgentRun.business_type == "contract"))
        if not run:
            raise ValueError("合同 Agent Run 不存在")
    finally:
        db.close()
    state = graph.resume(run_id, decision)
    save_run(run_id, state, "SUCCEEDED")
    return {"run_id": run_id, "status": "SUCCEEDED", "state": state}
