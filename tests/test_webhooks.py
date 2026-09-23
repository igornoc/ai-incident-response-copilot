def webhook_payload(
    external_id="alert-test-001"
):
    return {
        "source": "pytest-monitor",
        "external_id": external_id,
        "title": (
            "Production checkout alert"
        ),
        "description": (
            "Checkout HTTP 500 rate "
            "increased significantly."
        ),
        "severity": "critical",
        "auto_analyze": False
    }


def test_webhook_rejects_bad_secret(
    client
):
    response = client.post(
        "/webhooks/incidents",
        headers={
            "X-Webhook-Secret":
                "wrong-secret"
        },
        json=webhook_payload()
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Invalid webhook secret"
    }


def test_webhook_creates_incident(
    client,
    webhook_headers
):
    response = client.post(
        "/webhooks/incidents",
        headers=webhook_headers,
        json=webhook_payload()
    )

    assert response.status_code == 201

    data = response.json()

    assert data["duplicate"] is False

    assert (
        data["source"]
        == "pytest-monitor"
    )

    assert (
        data["external_id"]
        == "alert-test-001"
    )

    assert data["analysis"] is None


def test_duplicate_webhook_is_idempotent(
    client,
    webhook_headers
):
    payload = webhook_payload(
        "duplicate-test-001"
    )

    first = client.post(
        "/webhooks/incidents",
        headers=webhook_headers,
        json=payload
    )

    second = client.post(
        "/webhooks/incidents",
        headers=webhook_headers,
        json=payload
    )

    assert first.status_code == 201
    assert second.status_code == 201

    first_data = first.json()
    second_data = second.json()

    assert (
        first_data["duplicate"]
        is False
    )

    assert (
        second_data["duplicate"]
        is True
    )

    assert (
        first_data["incident"]["id"]
        == second_data["incident"]["id"]
    )

    assert (
        first_data["event_id"]
        == second_data["event_id"]
    )
