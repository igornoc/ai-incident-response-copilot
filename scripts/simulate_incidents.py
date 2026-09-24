from datetime import datetime, timezone
import os
import time

import requests
from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")

API_URL = "http://localhost:8000"

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")

if not WEBHOOK_SECRET:
    raise RuntimeError(
        "WEBHOOK_SECRET is missing from .env"
    )


RUN_ID = datetime.now(
    timezone.utc
).strftime("%Y%m%d%H%M%S")


INCIDENTS = [
    {
        "source": "datadog-simulator",
        "external_id": f"payment-{RUN_ID}",
        "title": "Production checkout HTTP 500 spike",
        "description": (
            "Checkout HTTP 500 error rate increased from "
            "0.4 percent to 14.8 percent during the last "
            "seven minutes. The issue affects payment "
            "submission requests across multiple customers."
        ),
        "severity": "critical",
        "auto_analyze": True,
    },
    {
        "source": "auth-monitor-simulator",
        "external_id": f"auth-{RUN_ID}",
        "title": "Authentication latency and login failures",
        "description": (
            "Login p95 latency increased from 420 ms to "
            "4.6 seconds. HTTP 401 responses also increased "
            "during the same ten-minute period. No identity "
            "provider outage has been confirmed."
        ),
        "severity": "high",
        "auto_analyze": True,
    },
    {
        "source": "apm-simulator",
        "external_id": f"latency-{RUN_ID}",
        "title": "Orders API severe latency degradation",
        "description": (
            "Orders API p95 latency increased from 650 ms "
            "to 5.2 seconds while request volume remained "
            "near its normal baseline. Error rate increased "
            "slightly to 3 percent."
        ),
        "severity": "high",
        "auto_analyze": True,
    },
    {
        "source": "deployment-monitor-simulator",
        "external_id": f"deploy-{RUN_ID}",
        "title": "Checkout failures after application deployment",
        "description": (
            "HTTP 500 errors began approximately six minutes "
            "after checkout-service version 2.8.1 was deployed. "
            "The error rate increased from below 1 percent "
            "to 9 percent. No rollback has been performed."
        ),
        "severity": "critical",
        "auto_analyze": True,
    },
    {
        "source": "operations-simulator",
        "external_id": f"inventory-{RUN_ID}",
        "title": "Intermittent inventory synchronization failures",
        "description": (
            "Several inventory synchronization jobs failed "
            "intermittently during the last twenty minutes. "
            "No application logs, infrastructure metrics, "
            "or dependency telemetry are currently available."
        ),
        "severity": "medium",
        "auto_analyze": True,
    },
]


headers = {
    "X-Webhook-Secret": WEBHOOK_SECRET
}


print()
print("AI Incident Copilot Simulation")
print("=" * 50)


for number, incident in enumerate(
    INCIDENTS,
    start=1
):
    print()
    print(
        f"[{number}/{len(INCIDENTS)}] "
        f"{incident['title']}"
    )

    response = requests.post(
        f"{API_URL}/webhooks/incidents",
        headers=headers,
        json=incident,
        timeout=180,
    )

    print(
        "HTTP status:",
        response.status_code
    )

    response.raise_for_status()

    result = response.json()

    created_incident = result["incident"]
    analysis = result.get("analysis")

    print(
        "Incident ID:",
        created_incident["id"]
    )

    print(
        "Severity:",
        created_incident["severity"]
    )

    if analysis:
        print(
            "AI confidence:",
            f"{analysis['confidence']:.0%}"
        )

        print(
            "Root cause:",
            analysis["likely_root_cause"]
        )

    time.sleep(1)


print()
print("=" * 50)
print("Simulation completed successfully.")
