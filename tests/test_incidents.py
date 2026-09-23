def test_health_endpoint(client):
    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "ok"
    }


def test_incidents_require_api_key(
    client
):
    response = client.get(
        "/incidents"
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Missing API key"
    }


def test_wrong_api_key_is_rejected(
    client
):
    response = client.get(
        "/incidents",
        headers={
            "X-API-Key": "wrong-key"
        }
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid API key"
    }


def test_create_incident(
    client,
    auth_headers
):
    response = client.post(
        "/incidents",
        headers=auth_headers,
        json={
            "title": "Payment API failing",
            "description": (
                "Checkout requests return "
                "HTTP 500 errors."
            ),
            "severity": "high"
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1

    assert (
        data["title"]
        == "Payment API failing"
    )

    assert data["severity"] == "high"

    assert data["status"] == "open"

    assert "created_at" in data


def test_get_incident(
    client,
    auth_headers
):
    create_response = client.post(
        "/incidents",
        headers=auth_headers,
        json={
            "title": "API timeout",
            "description": (
                "API requests are timing out."
            ),
            "severity": "medium"
        }
    )

    incident_id = (
        create_response.json()["id"]
    )

    response = client.get(
        f"/incidents/{incident_id}",
        headers=auth_headers
    )

    assert response.status_code == 200

    assert (
        response.json()["title"]
        == "API timeout"
    )


def test_get_missing_incident_returns_404(
    client,
    auth_headers
):
    response = client.get(
        "/incidents/999",
        headers=auth_headers
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Incident not found"
    }


def test_update_incident_status(
    client,
    auth_headers
):
    create_response = client.post(
        "/incidents",
        headers=auth_headers,
        json={
            "title": "Login service issue",
            "description": (
                "Users cannot log in."
            ),
            "severity": "high"
        }
    )

    incident_id = (
        create_response.json()["id"]
    )

    response = client.patch(
        f"/incidents/{incident_id}",
        headers=auth_headers,
        json={
            "status": "investigating"
        }
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "investigating"
    )


def test_delete_incident(
    client,
    auth_headers
):
    create_response = client.post(
        "/incidents",
        headers=auth_headers,
        json={
            "title": "Temporary incident",
            "description": (
                "Temporary test incident."
            ),
            "severity": "low"
        }
    )

    incident_id = (
        create_response.json()["id"]
    )

    delete_response = client.delete(
        f"/incidents/{incident_id}",
        headers=auth_headers
    )

    assert (
        delete_response.status_code
        == 204
    )

    get_response = client.get(
        f"/incidents/{incident_id}",
        headers=auth_headers
    )

    assert get_response.status_code == 404
