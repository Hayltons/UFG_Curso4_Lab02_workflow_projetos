from contextlib import asynccontextmanager
from datetime import UTC, datetime
from collections.abc import AsyncIterator

from fastapi import FastAPI
from pydantic import BaseModel

from app.api.project_routes import router as project_router
from app.database import Base, engine
from app.models import project as _project_models  # Register ORM tables before create_all.


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Monitoramento de Projetos em Workflow", lifespan=lifespan)
app.include_router(project_router)


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.now(UTC),
    )
