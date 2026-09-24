import os

import requests
from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")


# Slack rejects section text longer than 3000 characters. The title and
# description share one section, so together they stay below that.
SLACK_TEXT_LIMIT = 2700
SLACK_TITLE_LIMIT = 250


def slack_escape(value, limit: int = SLACK_TEXT_LIMIT) -> str:
    """Make untrusted text safe for Slack mrkdwn and short enough to send.

    Incident text comes from webhooks and LLM output. Without escaping,
    text like "<https://evil.example|Open runbook>" renders as a disguised
    link, and "<!channel>" pings everyone in the channel.
    """
    text = (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    if len(text) <= limit:
        return text

    text = text[: limit - 1]

    # Don't leave half of an escape sequence such as "&am" at the end.
    last_amp = text.rfind("&")
    if last_amp != -1 and ";" not in text[last_amp:]:
        text = text[:last_amp]

    return text + "…"


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

        hypothesis = slack_escape(
            analysis.likely_root_cause
        )

        action = slack_escape(
            analysis.recommended_action
        )

    title = slack_escape(
        incident.title,
        limit=SLACK_TITLE_LIMIT
    )
    description = slack_escape(incident.description)

    payload = {
        "text": (
            f"{emoji} "
            f"{incident.severity.upper()} "
            f"incident: {title}"
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
                        f"*{title}*\n"
                        f"{description}"
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
