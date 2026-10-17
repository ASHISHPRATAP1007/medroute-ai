"""
MedRoute AI backend entrypoint.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
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
    doctor_discovery,
    doctors,
    health,
    medical_shops,
    notifications,
    search,
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


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("MedRoute AI API starting up in '%s' environment.", settings.APP_ENV)
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    description="Field intelligence platform for Medical Representatives.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class CatchUnhandledErrors:
    """
    Turns unexpected exceptions into the standard JSON 500 *inside* the CORS
    middleware. Starlette's own `Exception` handler runs outside CORS, so its
    500s had no Access-Control-Allow-Origin header and browsers showed a
    misleading "blocked by CORS policy" error instead.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        started = False

        async def tracking_send(message):
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
            await send(message)

        try:
            await self.app(scope, receive, tracking_send)
        except Exception:
            logger.exception("Unhandled exception on %s %s", scope.get("method"), scope.get("path"))
            if started:
                raise
            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"success": False, "message": "Something went wrong.", "data": None, "errors": []},
            )
            await response(scope, receive, send)


# Added before CORS so CORS wraps it (the last-added middleware is outermost).
app.add_middleware(CatchUnhandledErrors)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# ---------- Routers ----------
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_mrs.router, prefix=settings.API_V1_PREFIX)
# Discovery is registered before the doctors router so its literal
# /doctors/discovery/* paths are never shadowed by /doctors/{doctor_id}.
app.include_router(doctor_discovery.router, prefix=settings.API_V1_PREFIX)
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
app.include_router(search.router, prefix=settings.API_V1_PREFIX)
