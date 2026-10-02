from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.contract.runner import resume_contract_run, start_contract_run
from app.core.response import ok
from app.core.security import CurrentUser, require_permission
from app.db import get_db
from app.models.agent import AgentRun
from app.models.contract import Contract, ContractVersion
from app.schemas.contract import ContractCreate, ContractResumeRequest

router = APIRouter(tags=["contracts"])


@router.get("/contracts")
def list_contracts(request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    items = db.scalars(select(Contract).where(Contract.tenant_id == user.tenant_id).order_by(Contract.created_at.desc())).all()
    return ok([{"id": item.id, "title": item.title, "contract_no": item.contract_no, "status": item.status, "risk_level": item.risk_level, "current_version_id": item.current_version_id} for item in items], request)


@router.post("/contracts", dependencies=[Depends(require_permission("contract:create"))])
def create_contract(payload: ContractCreate, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    contract = Contract(tenant_id=user.tenant_id, owner_id=user.id, title=payload.title, contract_no=payload.contract_no, counterparty_id=payload.counterparty_id)
    db.add(contract)
    db.flush()
    version = ContractVersion(tenant_id=user.tenant_id, contract_id=contract.id, version_no=1, file_id=payload.file_id, raw_text=payload.content, status="CURRENT")
    db.add(version)
    db.flush()
    contract.current_version_id = version.id
    db.commit()
    return ok({"id": contract.id, "version_id": version.id, "status": contract.status}, request)


@router.post("/contracts/{contract_id}/analyze", dependencies=[Depends(require_permission("contract:analyze"))])
def analyze_contract(contract_id: str, request: Request, user: CurrentUser):
    try:
        result = start_contract_run(contract_id, user.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ok({"run_id": result["run_id"], "status": result["status"], "state": result["state"]}, request)


@router.post("/contract-runs/{run_id}/resume", dependencies=[Depends(require_permission("contract:resume"))])
def resume_contract(run_id: str, payload: ContractResumeRequest, request: Request, user: CurrentUser):
    try:
        result = resume_contract_run(run_id, payload.decision, user.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ok({"run_id": result["run_id"], "status": result["status"], "state": result["state"]}, request)


@router.get("/contract-runs/{run_id}", dependencies=[Depends(require_permission("contract:read"))])
def get_contract_run(run_id: str, request: Request, user: CurrentUser, db: Session = Depends(get_db)):
    run = db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.tenant_id == user.tenant_id, AgentRun.business_type == "contract"))
    if not run:
        raise HTTPException(status_code=404, detail="合同 Agent Run 不存在")
    return ok({"id": run.id, "status": run.status, "graph_name": run.graph_name, "graph_version": run.graph_version, "state": run.state_json, "error_message": run.error_message}, request)
