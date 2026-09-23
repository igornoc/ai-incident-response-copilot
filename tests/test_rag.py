def create_payment_incident(
    client,
    auth_headers
):
    response = client.post(
        "/incidents",
        headers=auth_headers,
        json={
            "title": (
                "Production checkout "
                "error spike"
            ),
            "description": (
                "Checkout HTTP 500 error "
                "rate increased to 12 percent."
            ),
            "severity": "critical"
        }
    )

    return response.json()["id"]


def test_evidence_retrieval(
    client,
    auth_headers
):
    incident_id = (
        create_payment_incident(
            client,
            auth_headers
        )
    )

    response = client.get(
        f"/incidents/"
        f"{incident_id}/evidence",
        headers=auth_headers
    )

    assert response.status_code == 200

    evidence = response.json()

    assert len(evidence) > 0

    sources = [
        item["source"]
        for item in evidence
    ]

    assert (
        "runbooks/payment-api.md"
        in sources
    )


def test_evidence_has_required_fields(
    client,
    auth_headers
):
    incident_id = (
        create_payment_incident(
            client,
            auth_headers
        )
    )

    response = client.get(
        f"/incidents/"
        f"{incident_id}/evidence",
        headers=auth_headers
    )

    first_item = response.json()[0]

    assert "source" in first_item
    assert "section" in first_item
    assert "score" in first_item
    assert "content" in first_item

    assert first_item["score"] > 0
