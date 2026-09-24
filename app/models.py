from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from app.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    title = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=False
    )

    severity = Column(
        String(20),
        nullable=False
    )

    status = Column(
        String(20),
        nullable=False,
        default="open"
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    # Deleting an incident also deletes its analyses and webhook events,
    # so no orphaned rows point at an incident that no longer exists.
    analyses = relationship(
        "IncidentAnalysis",
        cascade="all, delete-orphan"
    )

    webhook_events = relationship(
        "WebhookEvent",
        cascade="all, delete-orphan"
    )


class IncidentAnalysis(Base):
    __tablename__ = "incident_analyses"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    incident_id = Column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    summary = Column(
        Text,
        nullable=False
    )

    likely_root_cause = Column(
        Text,
        nullable=False
    )

    confidence = Column(
        Float,
        nullable=False
    )

    troubleshooting_steps = Column(
        JSON,
        nullable=False
    )

    recommended_action = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    __table_args__ = (
        UniqueConstraint(
            "source",
            "external_id",
            name="uq_webhook_source_external_id"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    incident_id = Column(
        Integer,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    source = Column(
        String(100),
        nullable=False
    )

    external_id = Column(
        String(200),
        nullable=False
    )

    raw_payload = Column(
        JSON,
        nullable=False
    )

    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
