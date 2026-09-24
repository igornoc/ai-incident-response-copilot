import os

import requests
from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")


def _alerts_enabled() -> bool:
    value = os.getenv(
        "SLACK_ALERTS_ENABLED",
        "false"
    )

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on"
    }


def send_incident_alert(
    incident,
    analysis=None
) -> bool:
    if not _alerts_enabled():
        return False

    if incident.severity not in {
        "high",
        "critical"
    }:
        return False

    webhook_url = os.getenv(
        "SLACK_WEBHOOK_URL"
    )

    if not webhook_url:
        return False

    dashboard_url = os.getenv(
        "DASHBOARD_URL",
        "http://localhost:8501"
    )

    emoji = (
        "🚨"
        if incident.severity == "critical"
        else "⚠️"
    )

    confidence = "N/A"
    hypothesis = "AI analysis unavailable."
    action = "Review the incident."

    if analysis is not None:
        confidence = (
            f"{round(analysis.confidence * 100)}%"
        )

        hypothesis = (
            analysis.likely_root_cause
        )

        action = (
            analysis.recommended_action
        )

    payload = {
        "text": (
            f"{emoji} "
            f"{incident.severity.upper()} "
            f"incident: {incident.title}"
        ),
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": (
                        f"{emoji} "
                        f"{incident.severity.upper()} "
                        f"Incident #{incident.id}"
                    ),
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*{incident.title}*\n"
                        f"{incident.description}"
                    )
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            "*Severity*\n"
                            f"{incident.severity.upper()}"
                        )
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            "*Status*\n"
                            f"{incident.status.upper()}"
                        )
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            "*AI Confidence*\n"
                            f"{confidence}"
                        )
                    },
                    {
                        "type": "mrkdwn",
                        "text": (
                            "*Incident ID*\n"
                            f"#{incident.id}"
                        )
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Root Cause Hypothesis*\n"
                        f"{hypothesis}"
                    )
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*Recommended Action*\n"
                        f"{action}"
                    )
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"<{dashboard_url}|"
                        "Open AI Incident Response Copilot>"
                    )
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            "AI Incident Response Copilot "
                            "• Evidence-grounded analysis"
                        )
                    }
                ]
            }
        ]
    }

    response = requests.post(
        webhook_url,
        json=payload,
        timeout=15
    )

    response.raise_for_status()

    return True
