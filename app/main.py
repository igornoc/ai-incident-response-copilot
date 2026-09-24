import logging

from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.database import Base, engine
from app.routers import incidents, webhooks


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="AI Incident Copilot",
    description=(
        "AI-powered incident management, "
        "webhook ingestion, and troubleshooting API"
    ),
    version="0.3.0"
)


app.include_router(
    incidents.router
)

app.include_router(
    webhooks.router
)


@app.get("/")
def root():
    return {
        "message": (
            "AI Incident Copilot API is running"
        ),
        "status": "healthy",
        "version": "0.3.0"
    }


@app.get("/health")
def health_check():
    # Report unhealthy if the database is unreachable, so Docker or a
    # load balancer can detect a broken instance.
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )

    return {
        "status": "ok"
    }
