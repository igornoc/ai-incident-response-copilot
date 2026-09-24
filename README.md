# 🚨 AI Incident Response Copilot

**Evidence-grounded incident triage, diagnosis, and response orchestration.**

AI Incident Response Copilot is a full-stack incident-management prototype that combines **FastAPI, OpenAI, Retrieval-Augmented Generation (RAG), webhooks, Slack alerts, Streamlit, automated tests, and Docker**.

The system can ingest operational alerts, retrieve relevant internal runbooks, generate evidence-grounded AI troubleshooting guidance, track incidents through their lifecycle, prevent duplicate webhook events, and notify engineers through Slack.

The project explores how generative AI can support incident-response workflows while remaining conservative about uncertainty and avoiding unsupported root-cause claims.

---

## Overview

```text
Monitoring / APM Alert
        │
        ▼
Webhook Ingestion
        │
        ▼
Authentication + Deduplication
        │
        ▼
Incident Creation
        │
        ▼
RAG Evidence Retrieval
        │
        ▼
OpenAI Structured Analysis
        │
        ├──────────────► SQLite Analysis History
        │
        ├──────────────► Streamlit Dashboard
        │
        └──────────────► Slack Alert
```

---

## Key Features

### Incident Management

- Create, retrieve, update, and delete incidents
- Severity levels:
  - Low
  - Medium
  - High
  - Critical
- Status lifecycle:
  - Open
  - Investigating
  - Resolved
- Persistent storage using SQLAlchemy and SQLite
- Analysis history for every incident

### AI-Assisted Investigation

The system uses the OpenAI Responses API to produce structured incident analysis.

Each analysis contains:

- incident summary
- root-cause hypothesis
- confidence score
- ordered troubleshooting steps
- recommended next action

The model is instructed to distinguish known evidence from hypotheses and avoid inventing telemetry that was not supplied.

---

## Retrieval-Augmented Generation

Before an AI analysis is generated, the system searches internal troubleshooting documentation for relevant evidence.

Current example runbooks include:

```text
docs/runbooks/
├── payment-api.md
├── authentication.md
└── service-latency.md
```

The retrieval pipeline uses TF-IDF and cosine similarity to identify the most relevant document sections.

```text
Incident
   │
   ▼
Query Generation
   │
   ▼
TF-IDF Retrieval
   │
   ▼
Top Relevant Runbook Sections
   │
   ▼
OpenAI Analysis
   │
   ▼
Evidence-Grounded Diagnosis
```

Retrieved evidence is also displayed directly in the dashboard so users can inspect what documentation influenced the investigation.

---

## Evidence-Aware AI Design

A core design principle of the project is:

```text
Runbook guidance ≠ Observed telemetry ≠ Confirmed root cause
```

A runbook may describe database connection-pool exhaustion as a possible cause of HTTP 500 errors, but the AI must not claim that exhaustion is confirmed unless incident-specific evidence supports it.

The AI is instructed to:

- avoid inventing logs, metrics, traces, or deployments
- distinguish facts from hypotheses
- remain conservative when evidence is incomplete
- reduce confidence when direct telemetry is unavailable
- prioritize evidence collection
- recommend reversible actions before disruptive actions
- treat retrieved runbooks as guidance rather than proof

---

## Webhook Ingestion

External monitoring systems can automatically create incidents through:

```http
POST /webhooks/incidents
```

Example payload:

```json
{
  "source": "production-apm",
  "external_id": "checkout-alert-001",
  "title": "Checkout database connection saturation",
  "description": "Checkout HTTP 500 responses increased while database connection acquisition timeouts were observed.",
  "severity": "critical",
  "auto_analyze": true
}
```

Webhook ingestion supports:

- source tracking
- external event IDs
- shared-secret authentication
- automatic incident creation
- automatic AI analysis
- RAG retrieval
- duplicate-event protection

Duplicate protection uses the combination:

```text
source + external_id
```

If the same external alert is delivered multiple times, the original incident is returned rather than creating duplicates.

---

## Slack Alerts

High and critical incidents can automatically trigger Slack notifications.

Slack alerts include:

- incident ID
- title
- severity
- current status
- AI confidence
- root-cause hypothesis
- recommended action
- dashboard link

Example workflow:

```text
Critical Alert
     │
     ▼
FastAPI Webhook
     │
     ▼
Incident Created
     │
     ▼
RAG Retrieval
     │
     ▼
AI Analysis
     │
     ▼
Analysis Saved
     │
     ▼
Slack Notification
```

Slack notification failures are isolated so they do not interrupt the main incident-processing workflow.

---

## API Authentication

Protected incident endpoints require:

```http
X-API-Key: <application-api-key>
```

External monitoring webhooks use a separate secret:

```http
X-Webhook-Secret: <webhook-secret>
```

This separation prevents monitoring integrations from automatically receiving access to normal incident-management endpoints.

Sensitive credentials are stored using environment variables and are excluded from version control.

---

## Streamlit Operations Dashboard

The dashboard provides an operator-facing interface for managing incidents.

Features include:

- operational incident metrics
- total incident count
- open incident count
- investigating incident count
- critical incident count
- incident queue
- severity filtering
- status filtering
- incident details
- status updates
- manual AI analysis
- RAG evidence inspection
- AI confidence scores
- root-cause hypotheses
- troubleshooting steps
- recommended actions
- analysis history
- incident creation
- webhook simulation

The interface is designed around a simple incident-response workflow rather than a conversational chatbot.

---

## Architecture

```text
┌──────────────────────────────┐
│       Monitoring / APM       │
│      External Systems        │
└──────────────┬───────────────┘
               │
               │ Webhook
               ▼
┌──────────────────────────────┐
│           FastAPI            │
│          REST API            │
└──────────────┬───────────────┘
               │
      ┌────────┼─────────┐
      │        │         │
      ▼        ▼         ▼
 Incident    RAG      Webhook
   CRUD    Retrieval  Handling
      │        │         │
      │        ▼         │
      │   Internal       │
      │   Runbooks       │
      │        │         │
      │        ▼         │
      │  OpenAI Analysis │
      │        │         │
      └────────┼─────────┘
               │
        ┌──────┴──────┐
        │             │
        ▼             ▼
      SQLite         Slack
 Incident History    Alerts
        │
        ▼
┌──────────────────────────────┐
│     Streamlit Dashboard      │
└──────────────────────────────┘
```

---

## Technology Stack

### Backend

- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite
- Uvicorn

### AI and Retrieval

- OpenAI Responses API
- Structured Outputs
- Retrieval-Augmented Generation
- TF-IDF
- cosine similarity
- scikit-learn

### Frontend

- Streamlit
- Requests

### Integrations

- Slack Incoming Webhooks
- Generic monitoring webhooks

### Testing

- pytest
- FastAPI TestClient
- HTTPX
- isolated SQLite test database
- mocked AI analysis

### Infrastructure

- Docker
- Docker Compose
- persistent Docker volumes

---

## Project Structure

```text
ai-incident-copilot/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   │
│   ├── routers/
│   │   ├── incidents.py
│   │   └── webhooks.py
│   │
│   └── services/
│       ├── ai_service.py
│       ├── rag_service.py
│       ├── webhook_service.py
│       └── slack_service.py
│
├── docs/
│   └── runbooks/
│       ├── payment-api.md
│       ├── authentication.md
│       └── service-latency.md
│
├── frontend/
│   └── dashboard.py
│
├── scripts/
│   └── simulate_incidents.py
│
├── tests/
│   ├── conftest.py
│   ├── test_incidents.py
│   ├── test_analysis.py
│   ├── test_rag.py
│   └── test_webhooks.py
│
├── .dockerignore
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── README.md
```

---

## API Overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API health check |
| `GET` | `/incidents` | List incidents |
| `POST` | `/incidents` | Create an incident |
| `GET` | `/incidents/{id}` | Retrieve an incident |
| `PATCH` | `/incidents/{id}` | Update incident status/details |
| `DELETE` | `/incidents/{id}` | Delete an incident |
| `GET` | `/incidents/{id}/evidence` | Retrieve relevant RAG evidence |
| `POST` | `/incidents/{id}/analyze` | Run AI investigation |
| `GET` | `/incidents/{id}/analyses` | Retrieve analysis history |
| `POST` | `/webhooks/incidents` | Receive external monitoring alert |

Interactive API documentation is available through FastAPI Swagger UI:

```text
http://localhost:8000/docs
```

---

## Running Locally

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd ai-incident-copilot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

On Windows Git Bash:

```bash
source .venv/Scripts/activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file:

```env
DATABASE_URL=sqlite:///./incidents.db

OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=your-openai-model

APP_API_KEY=your-application-api-key
WEBHOOK_SECRET=your-webhook-secret

SLACK_ALERTS_ENABLED=true
SLACK_WEBHOOK_URL=your-slack-webhook-url

DASHBOARD_URL=http://localhost:8501
```

Never commit `.env` to Git.

### 5. Start FastAPI

```bash
uvicorn app.main:app --reload
```

FastAPI:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

### 6. Start Streamlit

In a second terminal:

```bash
streamlit run frontend/dashboard.py
```

Dashboard:

```text
http://localhost:8501
```

---

## Running with Docker

The easiest way to run the complete application is Docker Compose.

Build and start:

```bash
docker compose up -d --build
```

Dashboard:

```text
http://localhost:8501
```

API documentation:

```text
http://localhost:8000/docs
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

View running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Stop the application:

```bash
docker compose down
```

The SQLite database is stored in a persistent Docker volume so incidents survive container restarts.

---

## Automated Tests

Run the complete test suite with:

```bash
python -m pytest -v
```

Current result:

```text
15 passed
```

The tests cover:

- health endpoint
- missing API key
- invalid API key
- incident creation
- incident retrieval
- incident update
- incident deletion
- missing incident handling
- RAG retrieval
- evidence schema
- mocked AI analysis
- analysis persistence
- webhook authentication
- webhook incident creation
- webhook idempotency

OpenAI calls are mocked during automated tests, so running the test suite does not consume API credits.

Slack notifications are also disabled during testing.

---

## Simulating Incidents

The project contains a simulation script that creates multiple realistic incident types.

Run:

```bash
python scripts/simulate_incidents.py
```

Example simulated incidents include:

```text
CRITICAL  Production checkout HTTP 500 spike
HIGH      Authentication latency and login failures
HIGH      Orders API severe latency degradation
CRITICAL  Checkout failures after application deployment
MEDIUM    Intermittent inventory synchronization failures
```

These scenarios demonstrate how the RAG system behaves differently depending on the available evidence.

For example, a vague inventory incident should produce a conservative diagnosis, while an incident containing connection acquisition timeouts and near-saturated database pools can justify a stronger database-related hypothesis.

---

## Example AI Analysis

Example structured response:

```json
{
  "incident_id": 8,
  "summary": "Checkout HTTP 500 responses increased while database connection acquisition timeouts were observed.",
  "likely_root_cause": "Database connection-pool saturation is the leading hypothesis based on the available evidence.",
  "confidence": 0.74,
  "troubleshooting_steps": [
    "Inspect current database connection-pool utilization",
    "Review connection acquisition timeout logs",
    "Inspect slow and long-running database queries",
    "Compare pool utilization with the last healthy period",
    "Review recent application or database configuration changes"
  ],
  "recommended_action": "Collect database telemetry and identify the source of connection saturation before modifying pool configuration."
}
```

The confidence value varies depending on the incident evidence supplied.

---

## Example RAG Evidence

For a checkout HTTP 500 incident, the retrieval system may return:

```text
Source:
runbooks/payment-api.md

Section:
HTTP 500 Error Spike
```

and:

```text
Source:
runbooks/payment-api.md

Section:
Database Connection Pool Exhaustion
```

The AI receives these documents as investigation guidance.

The system explicitly prevents the model from treating retrieved documentation as direct evidence that the failure mode is occurring.

---

## Example End-to-End Workflow

```text
1. Monitoring system detects elevated checkout HTTP 500 errors.

2. Monitoring system sends:
   POST /webhooks/incidents

3. FastAPI validates the webhook secret.

4. The external event ID is checked for duplicates.

5. A new incident is stored.

6. RAG searches internal runbooks.

7. Relevant evidence is supplied to the OpenAI model.

8. OpenAI returns structured analysis.

9. The analysis is persisted.

10. The Streamlit dashboard displays:
    - incident information
    - retrieved evidence
    - confidence
    - root-cause hypothesis
    - troubleshooting steps
    - recommended action

11. If severity is HIGH or CRITICAL,
    Slack receives an operational alert.
```

---

## Security

The project includes several security controls appropriate for a prototype:

- `.env` is excluded from Git
- OpenAI keys are never stored in source code
- Slack webhook URLs are treated as secrets
- normal incident endpoints require an application API key
- webhook ingestion uses a separate webhook secret
- secrets are compared using constant-time comparison
- test credentials are isolated from production credentials
- Docker secrets are loaded at runtime
- SQLite databases are excluded from Git
- virtual environments are excluded from Git

Before publishing or deploying the project, all exposed development credentials should be rotated.

---

## Design Decisions

### Why FastAPI?

FastAPI provides:

- type-safe request validation
- automatic OpenAPI generation
- Swagger documentation
- dependency injection
- lightweight REST API development

### Why Streamlit?

Streamlit allows the project to provide an operator-facing interface without requiring a separate JavaScript frontend framework.

The focus of the project is the incident-response architecture and AI workflow rather than frontend engineering.

### Why RAG?

Sending only the incident description to an LLM can encourage generic troubleshooting advice.

Retrieving relevant internal runbooks provides domain context and allows the model to produce more targeted investigation guidance.

### Why TF-IDF instead of a vector database?

The current knowledge base is intentionally small.

TF-IDF provides:

- deterministic retrieval
- low infrastructure complexity
- easy debugging
- interpretable relevance scores

The retrieval layer can later be replaced with embeddings and a vector database without changing the surrounding API architecture.

### Why structured AI outputs?

Structured JSON responses make AI analysis easier to:

- validate
- persist
- test
- display
- integrate with other systems

This is more reliable for operational software than parsing free-form model responses.

### Why separate webhook and application authentication?

External monitoring systems only need permission to submit alerts.

They should not automatically receive permission to:

- update incidents
- delete incidents
- retrieve analysis history
- trigger arbitrary AI operations

Using separate secrets reduces unnecessary access.

---

## Current Limitations

This project is a portfolio prototype rather than a production incident-management platform.

Current limitations include:

- SQLite rather than a distributed production database
- local TF-IDF retrieval rather than a vector database
- synchronous AI processing
- basic API-key authentication
- no multi-user RBAC
- no real infrastructure telemetry connection
- Slack notifications are outbound only
- no distributed worker queue

---

## Future Improvements

Potential extensions include:

- PostgreSQL
- embeddings and vector database retrieval
- Prometheus integration
- Grafana integration
- Datadog integration
- PagerDuty integration
- real-time log ingestion
- traces and metrics ingestion
- background task queues
- Redis
- user accounts
- role-based access control
- interactive Slack buttons
- incident acknowledgement from Slack
- automated postmortem generation
- service dependency graphs
- Kubernetes deployment
- GitHub Actions CI/CD
- cloud deployment

---

## Testing Philosophy

External systems should not be required for the test suite.

The automated tests therefore use:

```text
OpenAI     → mocked
Slack      → disabled
Database   → isolated test SQLite database
FastAPI    → TestClient
```

This keeps tests:

- fast
- repeatable
- inexpensive
- independent of external service availability

---

## Project Motivation

Incident response is a useful example of where generative AI can add value without replacing human decision-making.

The project focuses on the question:

> How can AI help engineers investigate operational incidents while remaining transparent about uncertainty and evidence?

The system therefore emphasizes:

```text
Evidence
   ↓
Retrieval
   ↓
Hypothesis
   ↓
Confidence
   ↓
Recommended Investigation
   ↓
Human Decision
```

rather than:

```text
Alert
   ↓
AI declares root cause
```

The goal is decision support, not autonomous operational control.

---

## Portfolio Highlights

This project demonstrates practical experience with:

- REST API design
- backend architecture
- relational persistence
- API authentication
- webhook integrations
- event-driven workflows
- generative AI
- structured model outputs
- retrieval-augmented generation
- evidence grounding
- Slack integrations
- automated testing
- mocking external services
- Docker
- Docker Compose
- frontend/dashboard development
- security-conscious secret handling

---

## License

This project was created as an educational and portfolio demonstration.

