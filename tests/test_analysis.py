from app.routers import incidents


def fake_analysis(
    incident
):
    return {
        "incident_id": incident.id,
        "summary": (
            "Mock incident analysis."
        ),
        "likely_root_cause": (
            "Mock database hypothesis."
        ),
        "confidence": 0.5,
        "troubleshooting_steps": [
            "Check logs",
            "Check database metrics"
        ],
        "recommended_action": (
            "Collect more evidence."
        )
    }


def test_analyze_incident_without_real_ai(
    client,
    auth_headers,
    monkeypatch
):
    monkeypatch.setattr(
        incidents,
        "analyze_incident",
        fake_analysis
    )

    create_response = client.post(
        "/incidents",
        headers=auth_headers,
        json={
            "title": "Checkout failure",
            "description": (
                "Checkout is returning "
                "HTTP 500 errors."
            ),
            "severity": "critical"
        }
    )

    incident_id = (
        create_response.json()["id"]
    )

    response = client.post(
        f"/incidents/"
        f"{incident_id}/analyze",
        headers=auth_headers
    )

    assert response.status_code == 201

    analysis = response.json()

    assert (
        analysis["incident_id"]
        == incident_id
    )

    assert analysis["confidence"] == 0.5

    assert (
        analysis["likely_root_cause"]
        == "Mock database hypothesis."
    )


def test_analysis_is_saved(
    client,
    auth_headers,
    monkeypatch
):
    monkeypatch.setattr(
        incidents,
        "analyze_incident",
        fake_analysis
    )

    create_response = client.post(
        "/incidents",
        headers=auth_headers,
        json={
            "title": "Database errors",
            "description": (
                "Multiple database-related "
                "errors were observed."
            ),
            "severity": "high"
        }
    )

    incident_id = (
        create_response.json()["id"]
    )

    client.post(
        f"/incidents/"
        f"{incident_id}/analyze",
        headers=auth_headers
    )

    history_response = client.get(
        f"/incidents/"
        f"{incident_id}/analyses",
        headers=auth_headers
    )

    assert (
        history_response.status_code
        == 200
    )

    history = (
        history_response.json()
    )

    assert len(history) == 1

    assert (
        history[0]["summary"]
        == "Mock incident analysis."
    )
