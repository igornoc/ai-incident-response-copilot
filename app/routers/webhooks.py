import logging

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    status,
)

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.ai_service import analyze_incident
from app.services.webhook_service import verify_webhook_secret
from app.services.slack_service import send_incident_alert


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"]
)


def find_existing_event(
    db: Session,
    source: str,
    external_id: str
):
    return (
        db.query(models.WebhookEvent)
        .filter(
            models.WebhookEvent.source
            == source,
            models.WebhookEvent.external_id
            == external_id
        )
        .first()
    )


def duplicate_response(
    db: Session,
    existing_event: models.WebhookEvent
) -> schemas.WebhookIngestResponse:
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

    existing_event = find_existing_event(
        db,
        payload.source,
        payload.external_id
    )

    if existing_event:
        incident_exists = (
            db.query(models.Incident.id)
            .filter(
                models.Incident.id
                == existing_event.incident_id
            )
            .first()
        )

        if incident_exists:
            return duplicate_response(
                db,
                existing_event
            )

        # Orphaned event (its incident was deleted before cascading
        # deletes existed). Drop it so the alert is treated as new
        # instead of crashing.
        db.delete(existing_event)
        db.flush()

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

    try:
        db.commit()
    except IntegrityError:
        # Two identical alerts arrived at the same time and the other
        # request committed first. Return its incident as a duplicate.
        db.rollback()

        existing_event = find_existing_event(
            db,
            payload.source,
            payload.external_id
        )

        if existing_event is None:
            raise

        return duplicate_response(
            db,
            existing_event
        )

    db.refresh(incident)
    db.refresh(webhook_event)

    saved_analysis = None
    analysis_error = None

    if payload.auto_analyze:
        try:
            analysis_data = analyze_incident(
                incident
            )
        except Exception:
            # The incident is already stored; a failed AI call should not
            # turn the whole webhook into a 500 (the sender would retry and
            # get a "duplicate" with no analysis ever produced).
            logger.exception(
                "AI analysis failed for incident %s",
                incident.id
            )

            analysis_error = (
                "AI analysis failed. Retry with "
                f"POST /incidents/{incident.id}/analyze."
            )
        else:
            saved_analysis = models.IncidentAnalysis(
                **analysis_data
            )

            db.add(saved_analysis)
            db.commit()
            db.refresh(saved_analysis)

        try:
            send_incident_alert(
                incident,
                saved_analysis
            )
        except Exception:
            logger.exception(
                "Slack notification failed for incident %s",
                incident.id
            )

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
        ),
        analysis_error=analysis_error
    )
