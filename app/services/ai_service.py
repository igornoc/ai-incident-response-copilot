import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from app.models import Incident
from app.services.rag_service import retrieve_incident_evidence


load_dotenv(dotenv_path=".env")


SYSTEM_INSTRUCTIONS = """
You are an incident-response copilot for software,
API, cloud infrastructure, and SaaS incidents.

You may receive internal troubleshooting documentation.

Rules:

1. Use only the supplied incident information and retrieved evidence.
2. Treat runbooks as troubleshooting guidance, not proof.
3. Never claim a root cause is confirmed without direct evidence.
4. Do not invent logs, metrics, traces, deployments, dependencies,
   infrastructure, or events.
5. Clearly distinguish known facts from hypotheses.
6. Prefer evidence gathering and reversible actions first.
7. Give troubleshooting steps in a useful investigation order.
8. Confidence must be between 0 and 1.
9. Keep confidence conservative when direct telemetry is missing.
10. Mention relevant runbook filenames when useful.
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


def format_evidence(
    evidence: list[dict]
) -> str:
    if not evidence:
        return (
            "No relevant internal evidence "
            "was retrieved."
        )

    sections = []

    for number, item in enumerate(
        evidence,
        start=1
    ):
        sections.append(
            f"""
EVIDENCE {number}

Source:
{item["source"]}

Section:
{item["section"]}

Retrieval relevance:
{item["score"]}

Content:
{item["content"]}
"""
        )

    return "\n".join(sections)


def analyze_incident(
    incident: Incident
) -> dict:
    client = get_openai_client()

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-5.6-luna"
    )

    evidence = retrieve_incident_evidence(
        incident,
        top_k=3
    )

    evidence_text = format_evidence(
        evidence
    )

    prompt = f"""
INCIDENT

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


RETRIEVED INTERNAL EVIDENCE

{evidence_text}


TASK

Analyze the incident using the incident information
and the retrieved documentation.

The documentation describes possible failure modes
and investigation procedures.

It does NOT prove that those failure modes are
actually occurring in this incident.

Return:

1. A concise incident summary.
2. The most plausible root-cause hypothesis.
3. A confidence value between 0 and 1.
4. Ordered troubleshooting steps.
5. The safest recommended next action.

Reference useful runbook filenames when appropriate.
"""

    response = client.responses.create(
        model=model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=prompt,
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
            analysis[
                "troubleshooting_steps"
            ]
        ),
        "recommended_action": (
            analysis[
                "recommended_action"
            ]
        )
    }
