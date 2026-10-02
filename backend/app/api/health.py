from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.response import ok
from app.core.config import get_settings
from app.services.readiness import check_dependencies

router = APIRouter(tags=["system"])


@router.get("/health")
def health(request: Request):
    return ok({"status": "ok", "service": "backend"}, request)


@router.get("/ready")
def ready(request: Request):
    dependencies = check_dependencies(get_settings())
    is_ready = all(status == "ok" for status in dependencies.values())
    payload = {"status": "ready" if is_ready else "degraded", "dependencies": dependencies}
    if not is_ready:
        return JSONResponse(status_code=503, content={"code": "NOT_READY", "message": "基础设施未全部就绪", "data": payload, "request_id": request.state.request_id})
    return ok(payload, request)
