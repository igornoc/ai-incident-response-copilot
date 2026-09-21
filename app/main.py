from fastapi import FastAPI

from app.database import Base, engine
from app.routers import incidents, webhooks


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
    return {
        "status": "ok"
    }
