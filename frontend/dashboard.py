import os

import requests
import streamlit as st
from dotenv import load_dotenv


load_dotenv(dotenv_path=".env")


API_URL = os.getenv(
    "API_URL",
    "http://127.0.0.1:8000"
)

WEBHOOK_SECRET = os.getenv(
    "WEBHOOK_SECRET",
    ""
)

APP_API_KEY = os.getenv(
    "APP_API_KEY",
    ""
)


def auth_headers():
    if not APP_API_KEY:
        return {}

    return {
        "X-API-Key": APP_API_KEY
    }


st.set_page_config(
    page_title="AI Incident Copilot",
    page_icon="🚨",
    layout="wide"
)


def api_get(path):
    try:
        response = requests.get(
            f"{API_URL}{path}",
            headers=auth_headers(),
            timeout=20
        )

        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        st.error(
            f"API request failed: {exc}"
        )
        return None


def api_post(
    path,
    payload=None,
    headers=None,
    timeout=180
):
    try:
        request_headers = auth_headers()

        if headers:
            request_headers.update(headers)

        response = requests.post(
            f"{API_URL}{path}",
            json=payload,
            headers=request_headers,
            timeout=timeout
        )

        response.raise_for_status()

        if response.content:
            return response.json()

        return {}

    except requests.RequestException as exc:
        st.error(
            f"API request failed: {exc}"
        )
        return None


def api_patch(path, payload):
    try:
        response = requests.patch(
            f"{API_URL}{path}",
            json=payload,
            headers=auth_headers(),
            timeout=20
        )

        response.raise_for_status()
        return response.json()

    except requests.RequestException as exc:
        st.error(
            f"API request failed: {exc}"
        )
        return None


def severity_icon(severity):
    icons = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢"
    }

    return icons.get(
        severity,
        "⚪"
    )


def status_icon(status):
    icons = {
        "open": "🔓",
        "investigating": "🔎",
        "resolved": "✅"
    }

    return icons.get(
        status,
        "•"
    )


st.markdown(
    """
    <style>
        .block-container {
            padding-top: 4rem;
            padding-bottom: 3rem;
            max-width: 1500px;
        }

        .hero-title {
            display: block;
            font-size: 2.35rem;
            font-weight: 750;
            line-height: 1.45;
            padding: 0.65rem 0 0.35rem 0;
            margin: 0 0 0.15rem 0;
            overflow: visible;
            position: relative;
        }

        .hero-subtitle {
            font-size: 1.05rem;
            line-height: 1.5;
            color: #9ca3af;
            margin-top: 0.15rem;
            margin-bottom: 1rem;
        }

        .tech-strip {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.5rem;
            padding-top: 0.15rem;
            padding-bottom: 0.2rem;
            margin-bottom: 1.4rem;
        }

        .tech-pill {
            padding: 0.28rem 0.7rem;
            border: 1px solid #3b4252;
            border-radius: 999px;
            font-size: 0.78rem;
            color: #cbd5e1;
            background: #171b22;
        }

        div[data-testid="stMetric"] {
            background: #151922;
            border: 1px solid #292f3b;
            padding: 1rem;
            border-radius: 12px;
        }

        div[data-testid="stExpander"] {
            border: 1px solid #292f3b;
            border-radius: 10px;
        }
    </style>

    <div class="hero-title">
        🚨 AI Incident Response Copilot
    </div>

    <div class="hero-subtitle">
        Evidence-grounded incident triage, diagnosis,
        and response orchestration
    </div>

    <div class="tech-strip">
        <span class="tech-pill">FastAPI</span>
        <span class="tech-pill">RAG</span>
        <span class="tech-pill">OpenAI</span>
        <span class="tech-pill">Webhooks</span>
        <span class="tech-pill">Docker</span>
        <span class="tech-pill">Slack Alerts</span>
    </div>
    """,
    unsafe_allow_html=True
)


health = api_get(
    "/health"
)

if health is None:
    st.error(
        "FastAPI backend is offline."
    )

    st.code(
        "uvicorn app.main:app --reload"
    )

    st.stop()


st.success(
    "FastAPI backend connected",
    icon="✅"
)


incidents = api_get(
    "/incidents"
)

if incidents is None:
    st.stop()


total_incidents = len(
    incidents
)

open_count = sum(
    incident["status"] == "open"
    for incident in incidents
)

investigating_count = sum(
    incident["status"] == "investigating"
    for incident in incidents
)

critical_count = sum(
    incident["severity"] == "critical"
    for incident in incidents
)


metric1, metric2, metric3, metric4 = st.columns(
    4
)

metric1.metric(
    "Total Incidents",
    total_incidents
)

metric2.metric(
    "Open",
    open_count
)

metric3.metric(
    "Investigating",
    investigating_count
)

metric4.metric(
    "Critical",
    critical_count
)


st.divider()


tab_workspace, tab_create, tab_webhook = st.tabs(
    [
        "🧭 Incident Workspace",
        "➕ Create Incident",
        "🔗 Webhook Simulator"
    ]
)


with tab_workspace:

    filter_col1, filter_col2 = st.columns(
        2
    )

    with filter_col1:

        severity_filter = st.selectbox(
            "Filter by severity",
            [
                "All",
                "critical",
                "high",
                "medium",
                "low"
            ]
        )

    with filter_col2:

        status_filter = st.selectbox(
            "Filter by status",
            [
                "All",
                "open",
                "investigating",
                "resolved"
            ]
        )


    filtered = incidents

    if severity_filter != "All":

        filtered = [
            incident
            for incident in filtered
            if incident["severity"]
            == severity_filter
        ]

    if status_filter != "All":

        filtered = [
            incident
            for incident in filtered
            if incident["status"]
            == status_filter
        ]


    if not filtered:

        st.info(
            "No incidents match the selected filters."
        )

    else:

        st.subheader("Incident Queue")

        table_data = []

        for item in filtered:
            table_data.append(
                {
                    "ID": item["id"],
                    "Title": item["title"],
                    "Severity": item["severity"].upper(),
                    "Status": item["status"].upper(),
                    "Created": item["created_at"]
                }
            )

        st.dataframe(
            table_data,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### Incident Details")

        options = {}

        for incident in filtered:

            label = (
                f"{severity_icon(incident['severity'])} "
                f"#{incident['id']} "
                f"{incident['title']} "
                f"— "
                f"{status_icon(incident['status'])} "
                f"{incident['status']}"
            )

            options[label] = incident["id"]


        selected_label = st.selectbox(
            "Select an incident",
            list(options.keys())
        )

        incident_id = options[
            selected_label
        ]


        incident = api_get(
            f"/incidents/{incident_id}"
        )

        if incident:

            st.divider()

            detail_col, control_col = st.columns(
                [2, 1]
            )


            with detail_col:

                st.subheader(
                    f"Incident #{incident['id']}"
                )

                st.markdown(
                    f"## {incident['title']}"
                )

                st.write(
                    incident["description"]
                )

                info1, info2, info3 = st.columns(
                    3
                )

                info1.metric(
                    "Severity",
                    incident[
                        "severity"
                    ].upper()
                )

                info2.metric(
                    "Status",
                    incident[
                        "status"
                    ].upper()
                )

                info3.metric(
                    "Incident ID",
                    incident[
                        "id"
                    ]
                )

                st.caption(
                    f"Created at: "
                    f"{incident['created_at']}"
                )


            with control_col:

                st.subheader(
                    "Incident Controls"
                )

                statuses = [
                    "open",
                    "investigating",
                    "resolved"
                ]

                current_status_index = (
                    statuses.index(
                        incident["status"]
                    )
                )

                new_status = st.selectbox(
                    "Status",
                    statuses,
                    index=current_status_index
                )


                if st.button(
                    "Update Status",
                    use_container_width=True
                ):

                    updated = api_patch(
                        f"/incidents/{incident_id}",
                        {
                            "status": new_status
                        }
                    )

                    if updated:

                        st.success(
                            "Status updated."
                        )

                        st.rerun()


                if st.button(
                    "🤖 Analyze Incident",
                    type="primary",
                    use_container_width=True
                ):

                    with st.spinner(
                        "AI is investigating..."
                    ):

                        result = api_post(
                            f"/incidents/"
                            f"{incident_id}/analyze",
                            timeout=180
                        )

                    if result:

                        st.success(
                            "AI analysis completed."
                        )

                        st.rerun()


            st.divider()

            st.subheader(
                "📚 Retrieved Evidence"
            )

            st.caption(
                "Relevant internal runbook sections "
                "retrieved for this incident."
            )

            evidence = api_get(
                f"/incidents/{incident_id}/evidence"
            )

            if evidence:
                for index, item in enumerate(
                    evidence,
                    start=1
                ):
                    relevance = round(
                        item["score"] * 100,
                        1
                    )

                    with st.expander(
                        f"Evidence {index}: "
                        f"{item['section']} "
                        f"({relevance}% match)"
                    ):
                        st.markdown(
                            f"**Source:** `{item['source']}`"
                        )

                        st.write(
                            item["content"]
                        )

                        st.caption(
                            f"Retrieval score: "
                            f"{item['score']}"
                        )
            else:
                st.info(
                    "No relevant internal evidence found."
                )

            st.divider()

            st.subheader(
                "🤖 AI Investigation"
            )


            analyses = api_get(
                f"/incidents/"
                f"{incident_id}/analyses"
            )


            if analyses:

                latest = analyses[0]

                confidence = round(
                    latest[
                        "confidence"
                    ] * 100
                )


                top1, top2 = st.columns(
                    [3, 1]
                )


                with top1:

                    st.markdown(
                        "### Summary"
                    )

                    st.write(
                        latest[
                            "summary"
                        ]
                    )


                with top2:

                    st.metric(
                        "Confidence",
                        f"{confidence}%"
                    )


                st.markdown(
                    "### Root Cause Hypothesis"
                )

                st.warning(
                    latest[
                        "likely_root_cause"
                    ]
                )


                st.markdown(
                    "### Troubleshooting Steps"
                )

                for index, step in enumerate(
                    latest[
                        "troubleshooting_steps"
                    ],
                    start=1
                ):

                    st.write(
                        f"**{index}.** {step}"
                    )


                st.markdown(
                    "### Recommended Action"
                )

                st.info(
                    latest[
                        "recommended_action"
                    ]
                )


                st.caption(
                    f"Analysis #{latest['id']} "
                    f"generated at "
                    f"{latest['created_at']}"
                )


                if len(analyses) > 1:

                    with st.expander(
                        "View previous analyses"
                    ):

                        for previous in analyses[1:]:

                            st.markdown(
                                f"#### Analysis "
                                f"#{previous['id']}"
                            )

                            st.write(
                                previous[
                                    "summary"
                                ]
                            )

                            st.write(
                                "**Root cause:**",
                                previous[
                                    "likely_root_cause"
                                ]
                            )

                            st.write(
                                "**Confidence:**",
                                f"{round(previous['confidence'] * 100)}%"
                            )

                            st.caption(
                                previous[
                                    "created_at"
                                ]
                            )

                            st.divider()

            else:

                st.info(
                    "No AI analysis exists for "
                    "this incident yet."
                )


with tab_create:

    st.subheader(
        "Create Incident"
    )

    with st.form(
        "create_incident"
    ):

        title = st.text_input(
            "Incident title",
            placeholder=(
                "Example: Payment API unavailable"
            )
        )

        description = st.text_area(
            "Description",
            placeholder=(
                "Describe the symptoms, "
                "errors, impact and context..."
            ),
            height=180
        )

        severity = st.selectbox(
            "Severity",
            [
                "low",
                "medium",
                "high",
                "critical"
            ]
        )

        auto_analyze = st.checkbox(
            "Automatically run AI analysis",
            value=True
        )

        submitted = st.form_submit_button(
            "Create Incident",
            type="primary",
            use_container_width=True
        )


        if submitted:

            if len(title.strip()) < 3:

                st.error(
                    "Title must contain "
                    "at least 3 characters."
                )

            elif len(
                description.strip()
            ) < 5:

                st.error(
                    "Description must contain "
                    "at least 5 characters."
                )

            else:

                created = api_post(
                    "/incidents",
                    {
                        "title": title.strip(),
                        "description": (
                            description.strip()
                        ),
                        "severity": severity
                    }
                )

                if created:

                    st.success(
                        f"Incident "
                        f"#{created['id']} "
                        f"created."
                    )

                    if auto_analyze:

                        with st.spinner(
                            "Running AI analysis..."
                        ):

                            analysis = api_post(
                                f"/incidents/"
                                f"{created['id']}/"
                                f"analyze",
                                timeout=180
                            )

                        if analysis:

                            st.success(
                                "AI analysis completed."
                            )

                    st.rerun()


with tab_webhook:

    st.subheader(
        "Webhook Simulator"
    )

    st.write(
        "Simulate an alert from an external "
        "monitoring platform."
    )


    with st.form(
        "webhook_form"
    ):

        source = st.text_input(
            "Source",
            value="monitoring-demo"
        )

        external_id = st.text_input(
            "External event ID",
            value="dashboard-alert-001"
        )

        webhook_title = st.text_input(
            "Alert title",
            value="Production API error spike"
        )

        webhook_description = st.text_area(
            "Alert description",
            value=(
                "HTTP 500 error rate exceeded "
                "10 percent for five minutes."
            ),
            height=150
        )

        webhook_severity = st.selectbox(
            "Alert severity",
            [
                "low",
                "medium",
                "high",
                "critical"
            ],
            index=3
        )

        webhook_auto_analyze = st.checkbox(
            "Automatically analyze alert",
            value=True
        )

        webhook_submit = (
            st.form_submit_button(
                "Send Webhook",
                type="primary",
                use_container_width=True
            )
        )


        if webhook_submit:

            if not WEBHOOK_SECRET:

                st.error(
                    "WEBHOOK_SECRET is not "
                    "configured in .env."
                )

            else:

                with st.spinner(
                    "Processing webhook..."
                ):

                    result = api_post(
                        "/webhooks/incidents",
                        payload={
                            "source": source,
                            "external_id": (
                                external_id
                            ),
                            "title": webhook_title,
                            "description": (
                                webhook_description
                            ),
                            "severity": (
                                webhook_severity
                            ),
                            "auto_analyze": (
                                webhook_auto_analyze
                            )
                        },
                        headers={
                            "X-Webhook-Secret": (
                                WEBHOOK_SECRET
                            )
                        },
                        timeout=180
                    )


                if result:

                    if result[
                        "duplicate"
                    ]:

                        st.warning(
                            "Duplicate webhook detected. "
                            "Existing incident returned."
                        )

                    else:

                        st.success(
                            "Webhook accepted and "
                            "incident created."
                        )


                    st.markdown(
                        "### Result"
                    )

                    st.json(
                        result
                    )
