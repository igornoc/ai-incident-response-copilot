from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.ai_service import analyze_incident
from app.services.webhook_service import verify_webhook_secret


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)


@router.post(
    "/incidents",
    response_model=schemas.WebhookIngestResponse,
    status_code=status.HTTP_201_CREATED
)
def receive_incident_webhook(
    payload: schemas.WebhookIncidentCreate,
    x_webhook_secret: str | None = Header(
        default=None,
        alias="X-Webhook-Secret"
    ),
    db: Session = Depends(get_db)
):
    if not verify_webhook_secret(
        x_webhook_secret
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook secret"
        )

    existing_event = (
        db.query(models.WebhookEvent)
        .filter(
            models.WebhookEvent.source
            == payload.source,
            models.WebhookEvent.external_id
            == payload.external_id
        )
        .first()
    )

    if existing_event:
        incident = (
            db.query(models.Incident)
            .filter(
                models.Incident.id
                == existing_event.incident_id
            )
            .first()
        )

        latest_analysis = (
            db.query(models.IncidentAnalysis)
            .filter(
                models.IncidentAnalysis.incident_id
                == incident.id
            )
            .order_by(
                models.IncidentAnalysis.created_at.desc()
            )
            .first()
        )

        return schemas.WebhookIngestResponse(
            duplicate=True,
            event_id=existing_event.id,
            source=existing_event.source,
            external_id=existing_event.external_id,
            incident=(
                schemas.IncidentResponse.model_validate(
                    incident
                )
            ),
            analysis=(
                schemas.AIAnalysisResponse.model_validate(
                    latest_analysis
                )
                if latest_analysis
                else None
            )
        )

    incident = models.Incident(
        title=payload.title,
        description=payload.description,
        severity=payload.severity
    )

    db.add(incident)
    db.flush()

    webhook_event = models.WebhookEvent(
        incident_id=incident.id,
        source=payload.source,
        external_id=payload.external_id,
        raw_payload=payload.model_dump()
    )

    db.add(webhook_event)
    db.commit()

    db.refresh(incident)
    db.refresh(webhook_event)

    saved_analysis = None

    if payload.auto_analyze:
        analysis_data = analyze_incident(
            incident
        )

        saved_analysis = models.IncidentAnalysis(
            **analysis_data
        )

        db.add(saved_analysis)
        db.commit()
        db.refresh(saved_analysis)

    return schemas.WebhookIngestResponse(
        duplicate=False,
        event_id=webhook_event.id,
        source=webhook_event.source,
        external_id=webhook_event.external_id,
        incident=(
            schemas.IncidentResponse.model_validate(
                incident
            )
        ),
        analysis=(
            schemas.AIAnalysisResponse.model_validate(
                saved_analysis
            )
            if saved_analysis
            else None
        )
    )
