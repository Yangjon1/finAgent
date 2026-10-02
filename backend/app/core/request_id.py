from uuid import uuid4
import logging

from fastapi import Request


async def request_id_middleware(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-ID", str(uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    logging.getLogger("finagent.request").info(
        "%s %s -> %s", request.method, request.url.path, response.status_code, extra={"request_id": request.state.request_id}
    )
    return response
