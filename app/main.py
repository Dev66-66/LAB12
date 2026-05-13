from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import create_async_engine

from app.api.v1 import auth, kitchen, menu, orders, staff, tables
from app.core.config import settings
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create all database tables on startup."""
    engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Restaurant management REST API: tables, menu, orders, and staff.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_V1_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=_V1_PREFIX)
app.include_router(tables.router, prefix=_V1_PREFIX)
app.include_router(menu.router, prefix=_V1_PREFIX)
app.include_router(orders.router, prefix=_V1_PREFIX)
app.include_router(kitchen.router, prefix=_V1_PREFIX)
app.include_router(staff.router, prefix=_V1_PREFIX)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Return a readable 422 response for request validation failures."""
    errors = [
        {"field": " → ".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation error", "errors": errors},
    )


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    """Return service health status."""
    return {"status": "ok", "version": settings.APP_VERSION}
