"""
MedRoute AI backend entrypoint.
"""
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import (
    admin_mrs,
    ai_recommendations,
    analytics,
    audit_logs,
    auth,
    dashboard,
    doctors,
    health,
    medical_shops,
    notifications,
    specializations,
    stockists,
    territories,
    visits,
)
from app.api.v1.auth import limiter
from app.core.config import get_settings
from app.core.logging import configure_logging, logger

settings = get_settings()
configure_logging(settings.APP_ENV)

app = FastAPI(
    title=settings.APP_NAME,
    description="Field intelligence platform for Medical Representatives — Phase 1 API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.is_production:
    # In production, restrict to known hosts (configure via env/infra as needed).
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


# ---------- Global exception handling (never leak stack traces) ----------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "data": None, "errors": [str(exc.detail)]},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in exc.errors()]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"success": False, "message": "Validation failed.", "data": None, "errors": errors},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "message": "Something went wrong.", "data": None, "errors": []},
    )


@app.on_event("startup")
async def on_startup():
    logger.info("MedRoute AI API starting up in '%s' environment.", settings.APP_ENV)


# ---------- Routers ----------
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_mrs.router, prefix=settings.API_V1_PREFIX)
app.include_router(doctors.router, prefix=settings.API_V1_PREFIX)
app.include_router(specializations.router, prefix=settings.API_V1_PREFIX)
app.include_router(medical_shops.router, prefix=settings.API_V1_PREFIX)
app.include_router(stockists.router, prefix=settings.API_V1_PREFIX)
app.include_router(territories.router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_logs.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_recommendations.router, prefix=settings.API_V1_PREFIX)
app.include_router(visits.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)
