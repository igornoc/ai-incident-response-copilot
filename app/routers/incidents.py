from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.ai_service import analyze_incident


router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"]
)


@router.post(
    "",
    response_model=schemas.IncidentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_incident(
    incident: schemas.IncidentCreate,
    db: Session = Depends(get_db)
):
    db_incident = models.Incident(
        **incident.model_dump()
    )

    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)

    return db_incident


@router.get(
    "",
    response_model=list[schemas.IncidentResponse]
)
def get_incidents(
    db: Session = Depends(get_db)
):
    incidents = (
        db.query(models.Incident)
        .order_by(models.Incident.created_at.desc())
        .all()
    )

    return incidents


@router.get(
    "/{incident_id}",
    response_model=schemas.IncidentResponse
)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    incident = (
        db.query(models.Incident)
        .filter(
            models.Incident.id == incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    return incident


@router.patch(
    "/{incident_id}",
    response_model=schemas.IncidentResponse
)
def update_incident(
    incident_id: int,
    incident_update: schemas.IncidentUpdate,
    db: Session = Depends(get_db)
):
    incident = (
        db.query(models.Incident)
        .filter(
            models.Incident.id == incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    update_data = incident_update.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            incident,
            field,
            value
        )

    db.commit()
    db.refresh(incident)

    return incident


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db)
):
    incident = (
        db.query(models.Incident)
        .filter(
            models.Incident.id == incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    db.delete(incident)
    db.commit()

    return None


@router.post(
    "/{incident_id}/analyze",
    response_model=schemas.AIAnalysisResponse,
    status_code=status.HTTP_201_CREATED
)
def analyze_incident_endpoint(
    incident_id: int,
    db: Session = Depends(get_db)
):
    incident = (
        db.query(models.Incident)
        .filter(
            models.Incident.id == incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    analysis_data = analyze_incident(
        incident
    )

    db_analysis = models.IncidentAnalysis(
        **analysis_data
    )

    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)

    return db_analysis


@router.get(
    "/{incident_id}/analyses",
    response_model=list[schemas.AIAnalysisResponse]
)
def get_incident_analyses(
    incident_id: int,
    db: Session = Depends(get_db)
):
    incident = (
        db.query(models.Incident)
        .filter(
            models.Incident.id == incident_id
        )
        .first()
    )

    if incident is None:
        raise HTTPException(
            status_code=404,
            detail="Incident not found"
        )

    analyses = (
        db.query(models.IncidentAnalysis)
        .filter(
            models.IncidentAnalysis.incident_id
            == incident_id
        )
        .order_by(
            models.IncidentAnalysis.created_at.desc()
        )
        .all()
    )

    return analyses
