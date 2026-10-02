import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def error_response(request: Request, code: str, message: str, status_code: int, data=None):
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": data,
            "request_id": request.state.request_id,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(request, "VALIDATION_ERROR", "请求参数校验失败", 422, exc.errors())


async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled request exception", extra={"request_id": request.state.request_id})
    return error_response(request, "INTERNAL_ERROR", "服务内部错误", 500)
