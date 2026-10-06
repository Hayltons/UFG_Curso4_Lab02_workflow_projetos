from contextlib import asynccontextmanager
from datetime import UTC, datetime
from collections.abc import AsyncIterator

from fastapi import FastAPI
from pydantic import BaseModel

from app.api.project_routes import router as project_router
from app.database import engine, initialize_database
from app.models import project as _project_models  # Register ORM tables before schema inspection.


# Rev1 version approved for announcement after functional validation.
APP_VERSION = "0.2.0"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    initialize_database(engine)
    yield


app = FastAPI(
    title="Monitoramento de Projetos em Workflow",
    version=APP_VERSION,
    lifespan=lifespan,
)
app.include_router(project_router)


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=APP_VERSION,
        timestamp=datetime.now(UTC),
    )
