from typing import Any

from fastapi import Request


def ok(data: Any, request: Request, message: str = "OK") -> dict[str, Any]:
    return {"code": 0, "message": message, "data": data, "request_id": request.state.request_id}
