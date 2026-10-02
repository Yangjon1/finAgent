import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.api import auth, expenses, files, health, identity, rbac, rules
from app.core.config import get_settings
from app.core.request_id import request_id_middleware
from app.core.errors import validation_exception_handler, unhandled_exception_handler
from app.core.logging import configure_logging, RequestIdFilter

settings = get_settings()
configure_logging()
for handler in logging.getLogger().handlers:
    handler.addFilter(RequestIdFilter())
app = FastAPI(title=settings.app_name, version="0.1.0", docs_url="/docs")
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.middleware("http")(request_id_middleware)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router)
app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(identity.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(rbac.router, prefix=settings.api_prefix)
app.include_router(expenses.router, prefix=settings.api_prefix)
app.include_router(files.router, prefix=settings.api_prefix)
app.include_router(rules.router, prefix=settings.api_prefix)
