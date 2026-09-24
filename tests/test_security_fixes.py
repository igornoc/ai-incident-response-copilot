from app import models
from app.routers import incidents, webhooks
from app.schemas import MAX_DESCRIPTION_LENGTH
from app.services.slack_service import slack_escape

from tests.conftest import TestingSessionLocal


def webhook_payload(**overrides):
    payload = {
        "source": "monitoring-test",
        "external_id": "alert-001",
        "title": "Checkout error spike",
        "description": "HTTP 500 rate increased to 12 percent.",
        "severity": "low",
        "auto_analyze": False,
    }
    payload.update(overrides)
    return payload


def fake_analysis(incident):
    return {
        "incident_id": incident.id,
        "summary": "Mock summary.",
        "likely_root_cause": "Mock hypothesis.",
        "confidence": 0.4,
        "troubleshooting_steps": ["Check logs"],
        "recommended_action": "Collect more evidence.",
    }


def failing_analysis(incident):
    raise RuntimeError("provider exploded: secret-ish detail")


def count(model):
    db = TestingSessionLocal()
    try:
        return db.query(model).count()
    finally:
        db.close()


# --- Delete / retry bugs ---------------------------------------------------

def test_delete_removes_analyses_and_webhook_events(
    client, auth_headers, webhook_headers, monkeypatch
):
    monkeypatch.setattr(webhooks, "analyze_incident", fake_analysis)

    response = client.post(
        "/webhooks/incidents",
        json=webhook_payload(auto_analyze=True),
        headers=webhook_headers,
    )
    incident_id = response.json()["incident"]["id"]

    assert count(models.IncidentAnalysis) == 1
    assert count(models.WebhookEvent) == 1

    delete = client.delete(
        f"/incidents/{incident_id}", headers=auth_headers
    )

    assert delete.status_code == 204
    assert count(models.IncidentAnalysis) == 0
    assert count(models.WebhookEvent) == 0


def test_webhook_retry_after_delete_creates_new_incident(
    client, auth_headers, webhook_headers
):
    first = client.post(
        "/webhooks/incidents",
        json=webhook_payload(),
        headers=webhook_headers,
    )
    client.delete(
        f"/incidents/{first.json()['incident']['id']}",
        headers=auth_headers,
    )

    retry = client.post(
        "/webhooks/incidents",
        json=webhook_payload(),
        headers=webhook_headers,
    )

    assert retry.status_code == 201
    assert retry.json()["duplicate"] is False


def test_orphaned_webhook_event_does_not_crash(
    client, webhook_headers
):
    # Simulates a database written by the old code, where deleting an
    # incident left its webhook event behind.
    db = TestingSessionLocal()
    db.add(
        models.WebhookEvent(
            incident_id=999,
            source="monitoring-test",
            external_id="alert-001",
            raw_payload={},
        )
    )
    db.commit()
    db.close()

    response = client.post(
        "/webhooks/incidents",
        json=webhook_payload(),
        headers=webhook_headers,
    )

    assert response.status_code == 201
    assert response.json()["duplicate"] is False


def test_concurrent_duplicate_returns_existing_incident(
    client, webhook_headers, monkeypatch
):
    first = client.post(
        "/webhooks/incidents",
        json=webhook_payload(),
        headers=webhook_headers,
    )

    # Make the pre-check miss the existing event once, as happens when two
    # identical alerts are processed at the same moment. The unique
    # constraint then fires on commit.
    real_find = webhooks.find_existing_event
    calls = {"n": 0}

    def racy_find(db, source, external_id):
        calls["n"] += 1
        if calls["n"] == 1:
            return None
        return real_find(db, source, external_id)

    monkeypatch.setattr(webhooks, "find_existing_event", racy_find)

    second = client.post(
        "/webhooks/incidents",
        json=webhook_payload(),
        headers=webhook_headers,
    )

    assert second.status_code == 201
    assert second.json()["duplicate"] is True
    assert (
        second.json()["incident"]["id"]
        == first.json()["incident"]["id"]
    )
    assert count(models.Incident) == 1


# --- AI failure handling ---------------------------------------------------

def test_webhook_survives_ai_failure(
    client, webhook_headers, monkeypatch
):
    monkeypatch.setattr(webhooks, "analyze_incident", failing_analysis)

    response = client.post(
        "/webhooks/incidents",
        json=webhook_payload(auto_analyze=True),
        headers=webhook_headers,
    )

    body = response.json()

    assert response.status_code == 201
    assert body["analysis"] is None
    assert "Retry" in body["analysis_error"]
    assert "secret-ish" not in body["analysis_error"]
    assert count(models.Incident) == 1


def test_analyze_endpoint_returns_502_on_ai_failure(
    client, auth_headers, monkeypatch
):
    monkeypatch.setattr(incidents, "analyze_incident", failing_analysis)

    created = client.post(
        "/incidents",
        headers=auth_headers,
        json={
            "title": "Checkout error spike",
            "description": "HTTP 500 rate increased.",
            "severity": "high",
        },
    )

    response = client.post(
        f"/incidents/{created.json()['id']}/analyze",
        headers=auth_headers,
    )

    assert response.status_code == 502
    assert "secret-ish" not in response.text


# --- Input size limits -----------------------------------------------------

def test_oversized_webhook_description_is_rejected(
    client, webhook_headers
):
    response = client.post(
        "/webhooks/incidents",
        json=webhook_payload(
            description="A" * (MAX_DESCRIPTION_LENGTH + 1)
        ),
        headers=webhook_headers,
    )

    assert response.status_code == 422
    assert count(models.Incident) == 0


def test_oversized_incident_description_is_rejected(
    client, auth_headers
):
    response = client.post(
        "/incidents",
        headers=auth_headers,
        json={
            "title": "Checkout error spike",
            "description": "A" * (MAX_DESCRIPTION_LENGTH + 1),
            "severity": "low",
        },
    )

    assert response.status_code == 422


# --- Slack output ----------------------------------------------------------

def test_slack_escape_neutralises_links_and_mentions():
    escaped = slack_escape(
        "<!channel> <https://evil.example|Open runbook> a&b"
    )

    assert "<" not in escaped
    assert ">" not in escaped
    assert "&amp;" in escaped


def test_slack_escape_respects_length_limit():
    escaped = slack_escape("<" * 10_000, limit=100)

    assert len(escaped) <= 100
    # No half-written escape sequence before the ellipsis.
    assert escaped.endswith(";…")
