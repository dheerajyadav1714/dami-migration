# ui/pages/agent_trace.py
"""
Agent Execution Trace & Transparency Dashboard
Shows a real-time timeline of every agent invocation, tool calls,
execution times, and results — demonstrating human-in-the-loop oversight.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

@st.cache_resource
def get_bq_client(project_id):
    return bigquery.Client(project=project_id)

def fetch_traces(client, project_id, dataset, run_id=None):
    """Fetch agent execution traces from BigQuery."""
    if run_id:
        query = f"""
            SELECT * FROM `{project_id}.{dataset}.agent_execution_logs`
            WHERE run_id = '{run_id}'
            ORDER BY started_at ASC
        """
    else:
        query = f"""
            SELECT * FROM `{project_id}.{dataset}.agent_execution_logs`
            ORDER BY started_at DESC
            LIMIT 200
        """
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f"Failed to fetch traces: {e}")
        return pd.DataFrame()

def fetch_run_ids(client, project_id, dataset):
    """Get distinct run IDs for the dropdown."""
    query = f"""
        SELECT DISTINCT run_id, MIN(started_at) as run_start, 
               COUNT(*) as agent_count,
               COUNTIF(status = 'success') as success_count,
               COUNTIF(status = 'error') as error_count
        FROM `{project_id}.{dataset}.agent_execution_logs`
        GROUP BY run_id
        ORDER BY run_start DESC
        LIMIT 50
    """
    try:
        return client.query(query).to_dataframe()
    except Exception:
        return pd.DataFrame()

def render():
    st.markdown("<h1 class='gradient-text'>Agent Execution Trace & Observability</h1>", unsafe_allow_html=True)
    st.write("Full transparency into the multi-agent orchestration pipeline. Every agent invocation, tool call, and decision is logged and auditable.")
    st.write("---")

    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    client = get_bq_client(project_id)

    # Fetch available runs
    runs_df = fetch_run_ids(client, project_id, dataset)

    if runs_df.empty:
        # Show a demo/explanation view when no traces exist yet
        st.info("No agent execution traces recorded yet. Run the full migration pipeline from the Dashboard or Upload Center to generate traces.")
        st.write("---")

        # Show the agent architecture diagram
        st.subheader("🏗️ Multi-Agent Orchestration Architecture")
        st.markdown("""
        When the pipeline runs, D.A.M.I.'s **Orchestrator Agent** coordinates the following specialist agents.
        Each step is logged here with execution time, status, records processed, and any errors.
        """)

        # Display the agent pipeline as a visual flow
        phases = [
            {"phase": "ASSESS", "agents": [
                {"name": "Discovery Agent", "icon": "🔍", "tech": "NVIDIA RAPIDS cuDF", "desc": "GPU-accelerated inventory ingestion"},
                {"name": "Intake Agent", "icon": "🖼️", "tech": "Gemini Vision", "desc": "Architecture diagram parsing"},
                {"name": "Dependency Mapper", "icon": "🔗", "tech": "NetworkX", "desc": "Network graph & loop detection"},
                {"name": "Risk Scorer", "icon": "⚠️", "tech": "BQML + 7R Rules", "desc": "Risk prediction & strategy classification"},
            ]},
            {"phase": "PLAN", "agents": [
                {"name": "Architecture Designer", "icon": "🏗️", "tech": "Gemini + BQ", "desc": "Source-to-GCP service mapping"},
                {"name": "Wave Planner", "icon": "🌊", "tech": "Topological Sort", "desc": "Dependency-aware wave sequencing"},
            ]},
            {"phase": "DEPLOY", "agents": [
                {"name": "IaC Generator", "icon": "💻", "tech": "Gemini Structured Output", "desc": "Terraform, K8s, Ansible generation"},
                {"name": "Runbook Generator", "icon": "📋", "tech": "Gemini Templates", "desc": "Cutover procedures & rollback scripts"},
            ]},
            {"phase": "OPTIMIZE", "agents": [
                {"name": "FinOps Analyzer", "icon": "💰", "tech": "BigQuery Analytics", "desc": "TCO comparison & rightsizing"},
                {"name": "Feedback Processor", "icon": "🔄", "tech": "Gemini NLP", "desc": "Human correction loop"},
            ]},
        ]

        phase_colors = {
            "ASSESS": "#6366f1",
            "PLAN": "#8b5cf6",
            "DEPLOY": "#22d3ee",
            "OPTIMIZE": "#10b981"
        }

        for phase_data in phases:
            phase = phase_data["phase"]
            color = phase_colors[phase]
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}22, {color}11);
                border-left: 4px solid {color};
                border-radius: 8px;
                padding: 12px 16px;
                margin-bottom: 8px;
            ">
                <span style="color: {color}; font-weight: 700; font-size: 0.9rem;">
                    PHASE: {phase}
                </span>
            </div>
            """, unsafe_allow_html=True)

            cols = st.columns(len(phase_data["agents"]))
            for i, agent in enumerate(phase_data["agents"]):
                with cols[i]:
                    st.markdown(f"""
                    <div style="
                        background: rgba(30, 30, 47, 0.6);
                        border: 1px solid rgba(99, 102, 241, 0.15);
                        border-radius: 10px;
                        padding: 14px;
                        text-align: center;
                        min-height: 140px;
                    ">
                        <div style="font-size: 1.8rem;">{agent['icon']}</div>
                        <div style="font-weight: 600; color: #e2e8f0; margin: 4px 0;">{agent['name']}</div>
                        <div style="font-size: 0.7rem; color: {color}; font-weight: 500;">{agent['tech']}</div>
                        <div style="font-size: 0.72rem; color: #94a3b8; margin-top: 4px;">{agent['desc']}</div>
                    </div>
                    """, unsafe_allow_html=True)
            st.write("")

        return

    # --- Active trace data exists ---
    col_sel, col_stats = st.columns([2, 1])

    with col_sel:
        run_options = []
        for _, row in runs_df.iterrows():
            ts = pd.Timestamp(row["run_start"]).strftime("%Y-%m-%d %H:%M:%S") if pd.notna(row["run_start"]) else "Unknown"
            status_emoji = "✅" if row["error_count"] == 0 else "⚠️"
            run_options.append(f"{status_emoji} {row['run_id']} ({ts}) — {row['agent_count']} agents")
        selected_run_label = st.selectbox("Select Orchestration Run", run_options)
        selected_run_id = runs_df.iloc[run_options.index(selected_run_label)]["run_id"]

    traces_df = fetch_traces(client, project_id, dataset, run_id=selected_run_id)

    if traces_df.empty:
        st.warning("No trace data for this run.")
        return

    # KPI summary row
    with col_stats:
        total_agents = len(traces_df)
        success_count = len(traces_df[traces_df["status"] == "success"])
        error_count = len(traces_df[traces_df["status"] == "error"])
        total_duration = traces_df["duration_ms"].sum()
        total_records = traces_df["records_processed"].sum()

        st.metric("Total Agents Executed", total_agents)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("✅ Succeeded", success_count)
    kpi2.metric("❌ Failed", error_count)
    kpi3.metric("⏱️ Total Duration", f"{total_duration / 1000:.1f}s")
    kpi4.metric("📊 Records Processed", f"{int(total_records):,}")

    st.write("---")

    # --- Execution Timeline (Gantt-style) ---
    st.subheader("📊 Agent Execution Timeline")

    phase_color_map = {
        "assess": "#6366f1",
        "plan": "#8b5cf6",
        "deploy": "#22d3ee",
        "optimize": "#10b981",
        "ingest": "#f59e0b",
    }

    if "started_at" in traces_df.columns and "completed_at" in traces_df.columns:
        timeline_df = traces_df.copy()
        timeline_df["started_at"] = pd.to_datetime(timeline_df["started_at"])
        timeline_df["completed_at"] = pd.to_datetime(timeline_df["completed_at"])

        fig = px.timeline(
            timeline_df,
            x_start="started_at",
            x_end="completed_at",
            y="agent_name",
            color="phase",
            hover_data=["status", "duration_ms", "output_summary"],
            color_discrete_map=phase_color_map,
            title=""
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#e2e8f0",
            xaxis_title="Time",
            yaxis_title="",
            showlegend=True,
            height=max(300, len(timeline_df) * 45),
            margin=dict(l=0, r=0, t=10, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

    st.write("---")

    # --- Detailed Trace Table ---
    st.subheader("📋 Detailed Agent Execution Log")

    for _, row in traces_df.iterrows():
        status = row.get("status", "unknown")
        agent = row.get("agent_name", "Unknown")
        phase = row.get("phase", "—")
        dur = row.get("duration_ms", 0)
        output = row.get("output_summary", "")
        tools = row.get("tools_called", [])
        records = row.get("records_processed", 0)
        error = row.get("error_message", "")

        if status == "success":
            icon = "✅"
            border_color = "#10b981"
        elif status == "error":
            icon = "❌"
            border_color = "#ef4444"
        else:
            icon = "⏳"
            border_color = "#f59e0b"

        phase_color = phase_color_map.get(phase.lower(), "#6366f1")

        try:
            # Convert numpy arrays to list first to avoid truth value ambiguity
            if hasattr(tools, 'tolist'):
                tools = tools.tolist()
            if isinstance(tools, str):
                tools_str = tools if tools else "—"
            elif isinstance(tools, (list, tuple)) and len(tools) > 0:
                tools_str = ", ".join(str(t) for t in tools)
            else:
                tools_str = str(tools) if tools else "—"
        except (TypeError, ValueError):
            tools_str = "—"

        st.markdown(f"""
        <div style="
            background: rgba(30, 30, 47, 0.5);
            border-left: 4px solid {border_color};
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 16px;
        ">
            <div style="font-size: 1.4rem;">{icon}</div>
            <div style="flex: 1;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; color: #e2e8f0;">{agent}</span>
                    <span style="
                        background: {phase_color}22;
                        color: {phase_color};
                        padding: 2px 8px;
                        border-radius: 4px;
                        font-size: 0.7rem;
                        font-weight: 600;
                        text-transform: uppercase;
                    ">{phase}</span>
                </div>
                <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">
                    {output[:120]}
                </div>
                <div style="font-size: 0.72rem; color: #64748b; margin-top: 4px;">
                    ⏱️ {dur}ms &nbsp;|&nbsp; 📊 {records:,} records &nbsp;|&nbsp; 🔧 Tools: {tools_str}
                </div>
                {"<div style='font-size: 0.72rem; color: #ef4444; margin-top: 2px;'>⚠️ " + error[:100] + "</div>" if error else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")

    # --- Performance Breakdown ---
    st.subheader("⚡ Agent Performance Breakdown")

    col_pie, col_bar = st.columns(2)

    with col_pie:
        phase_dur = traces_df.groupby("phase")["duration_ms"].sum().reset_index()
        if not phase_dur.empty:
            fig_pie = px.pie(
                phase_dur, names="phase", values="duration_ms",
                color="phase", color_discrete_map=phase_color_map,
                hole=0.45
            )
            fig_pie.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                title="Time by Phase",
                margin=dict(l=0, r=0, t=40, b=0),
                height=300
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        agent_dur = traces_df[["agent_name", "duration_ms"]].copy()
        if not agent_dur.empty:
            fig_bar = px.bar(
                agent_dur, x="duration_ms", y="agent_name",
                orientation="h",
                color_discrete_sequence=["#6366f1"]
            )
            fig_bar.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                title="Duration per Agent (ms)",
                xaxis_title="",
                yaxis_title="",
                margin=dict(l=0, r=0, t=40, b=0),
                height=300
            )
            fig_bar.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_bar, use_container_width=True)


if __name__ == "__main__":
    render()
