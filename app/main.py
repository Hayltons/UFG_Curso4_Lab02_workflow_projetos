from datetime import UTC, datetime

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


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
