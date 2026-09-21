import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.models import Incident


load_dotenv(dotenv_path=".env")


SYSTEM_INSTRUCTIONS = """
You are an incident-response copilot for software, APIs,
cloud infrastructure, and SaaS systems.

Analyze incidents conservatively.

Rules:

1. Use only the incident information provided.
2. Do not invent logs, metrics, deployments, dependencies,
   infrastructure, or events.
3. Treat root causes as hypotheses unless the evidence confirms them.
4. Give practical troubleshooting steps in a useful order.
5. Prefer evidence gathering and reversible actions first.
6. Avoid destructive actions unless clearly justified.
7. Confidence must be between 0 and 1.
8. Lower confidence when evidence is limited.
"""


ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string"
        },
        "likely_root_cause": {
            "type": "string"
        },
        "confidence": {
            "type": "number"
        },
        "troubleshooting_steps": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "recommended_action": {
            "type": "string"
        }
    },
    "required": [
        "summary",
        "likely_root_cause",
        "confidence",
        "troubleshooting_steps",
        "recommended_action"
    ],
    "additionalProperties": False
}


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured."
        )

    return OpenAI(
        api_key=api_key
    )


def analyze_incident(
    incident: Incident
) -> dict:

    client = get_openai_client()

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-5.6-luna"
    )

    incident_context = f"""
Analyze this software incident.

Incident ID:
{incident.id}

Title:
{incident.title}

Description:
{incident.description}

Severity:
{incident.severity}

Status:
{incident.status}

Tasks:

1. Summarize the incident.
2. Identify the most plausible root-cause hypothesis.
3. Give a confidence value between 0 and 1.
4. Provide ordered troubleshooting steps.
5. Recommend the safest next action.

Do not invent evidence that was not provided.
"""

    response = client.responses.create(
        model=model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=incident_context,
        text={
            "format": {
                "type": "json_schema",
                "name": "incident_analysis",
                "schema": ANALYSIS_SCHEMA,
                "strict": True
            }
        }
    )

    if not response.output_text:
        raise RuntimeError(
            "The model returned an empty response."
        )

    analysis = json.loads(
        response.output_text
    )

    confidence = float(
        analysis["confidence"]
    )

    confidence = max(
        0.0,
        min(1.0, confidence)
    )

    return {
        "incident_id": incident.id,
        "summary": analysis["summary"],
        "likely_root_cause": (
            analysis["likely_root_cause"]
        ),
        "confidence": confidence,
        "troubleshooting_steps": (
            analysis["troubleshooting_steps"]
        ),
        "recommended_action": (
            analysis["recommended_action"]
        )
    }
