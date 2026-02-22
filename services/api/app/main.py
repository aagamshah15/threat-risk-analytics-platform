from __future__ import annotations

from typing import Any, Generator

from fastapi import Depends, FastAPI, Query
from fastapi.responses import JSONResponse

from .config import APP_NAME, APP_VERSION
from .db import get_conn
from .repository import AnalyticsRepository

app = FastAPI(title=APP_NAME, version=APP_VERSION)


def get_repository() -> Generator[AnalyticsRepository, None, None]:
    with get_conn() as conn:
        yield AnalyticsRepository(conn)


@app.get("/health")
def health(repo: AnalyticsRepository = Depends(get_repository)) -> dict[str, Any]:
    db = repo.health()
    return {"status": "ok" if db["db_ok"] else "degraded", **db}


@app.get("/v1/pipeline/summary")
def pipeline_summary(repo: AnalyticsRepository = Depends(get_repository)) -> dict[str, Any]:
    return repo.pipeline_summary()


@app.get("/v1/trends/threat-events")
def threat_event_trends(
    days: int = Query(default=14, ge=1, le=90),
    repo: AnalyticsRepository = Depends(get_repository),
) -> dict[str, Any]:
    return {"days": days, "series": repo.threat_event_trends(days=days)}


@app.get("/v1/risk/kev-summary")
def kev_risk_summary(repo: AnalyticsRepository = Depends(get_repository)) -> dict[str, Any]:
    return repo.kev_risk_summary()


@app.get("/v1/trends/stream-lag")
def stream_lag_trends(
    hours: int = Query(default=24, ge=1, le=168),
    repo: AnalyticsRepository = Depends(get_repository),
) -> dict[str, Any]:
    return {"hours": hours, "series": repo.stream_lag_trends(hours=hours)}


@app.get("/v1/threat/top-hosts")
def top_hosts(
    days: int = Query(default=7, ge=1, le=30),
    limit: int = Query(default=10, ge=1, le=100),
    repo: AnalyticsRepository = Depends(get_repository),
) -> dict[str, Any]:
    return {"days": days, "limit": limit, "rows": repo.top_malicious_hosts(days=days, limit=limit)}


@app.exception_handler(Exception)
async def unhandled_error_handler(_request, exc: Exception):
    # Avoid leaking internals in HTTP responses.
    _ = exc
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
