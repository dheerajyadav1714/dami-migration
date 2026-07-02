# ui/pages/self_learning.py
"""
Self-Learning Intelligence Dashboard
Shows agent memory statistics, learning history, and allows
manual corrections that feed back into the memory store.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()


def render():
    st.markdown("<h1 class='gradient-text'>🧠 Self-Learning Intelligence</h1>", unsafe_allow_html=True)
    st.write("D.A.M.I. learns from every human correction and migration outcome to improve future decisions.")
    
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    
    # --- Backend Status ---
    status_col1, status_col2 = st.columns(2)
    with status_col1:
        st.markdown("""
        <div style="
            background: rgba(66, 133, 244, 0.08);
            border: 1px solid rgba(66, 133, 244, 0.3);
            border-radius: 10px;
            padding: 16px;
        ">
            <div style="font-weight: 700; color: #4285f4; font-size: 1rem;">☁️ BigQuery Memory Store</div>
            <div style="font-size: 0.8rem; color: #10b981; margin-top: 6px;">● Connected — Primary Backend</div>
            <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 4px;">
                Keyword-based retrieval on <code>agent_memories</code> table.
                Stores corrections, patterns, optimizations, and insights.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with status_col2:
        # Check AlloyDB status
        alloydb_status = "● Offline"
        alloydb_color = "#ef4444"
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("ALLOYDB_HOST", "localhost"),
                port=os.getenv("ALLOYDB_PORT", "5432"),
                database=os.getenv("ALLOYDB_DB", "dami_memory"),
                user=os.getenv("ALLOYDB_USER", "postgres"),
                password=os.getenv("ALLOYDB_PASSWORD", "dami2026"),
                connect_timeout=2
            )
            conn.close()
            alloydb_status = "● Connected — pgvector enabled"
            alloydb_color = "#10b981"
        except Exception:
            pass
        
        st.markdown(f"""
        <div style="
            background: rgba(118, 185, 0, 0.08);
            border: 1px solid rgba(118, 185, 0, 0.3);
            border-radius: 10px;
            padding: 16px;
        ">
            <div style="font-weight: 700; color: #76b900; font-size: 1rem;">🐘 AlloyDB</div>
            <div style="font-size: 0.8rem; color: {alloydb_color}; margin-top: 6px;">{alloydb_status}</div>
            <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 4px;">
                Optional vector similarity backend for semantic memory search via <code>pgvector</code>.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("---")
    
    # --- Learning Stats ---
    st.subheader("📊 Learning Statistics")
    
    from agents.memory_store import MemoryStore
    store = MemoryStore()
    stats = store.get_learning_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Memories", int(stats.get("total_memories") or 0))
    with col2:
        st.metric("Corrections", int(stats.get("corrections") or 0), delta="Human feedback")
    with col3:
        st.metric("Patterns Learned", int(stats.get("patterns") or 0), delta="Auto-discovered")
    with col4:
        effectiveness = float(stats.get("avg_effectiveness") or 0)
        st.metric("Avg Effectiveness", f"{effectiveness:.1%}" if effectiveness > 0 else "—")
    
    # --- Learning Type Distribution ---
    st.write("")
    learn_col1, learn_col2 = st.columns([1, 1])
    
    with learn_col1:
        st.markdown("##### 📈 Memory Distribution by Type")
        types = ["Corrections", "Patterns", "Optimizations", "Insights"]
        values = [
            int(stats.get("corrections") or 0),
            int(stats.get("patterns") or 0),
            int(stats.get("optimizations") or 0),
            int(stats.get("insights") or 0)
        ]
        
        if sum(values) > 0:
            fig = go.Figure(data=[go.Pie(
                labels=types, values=values,
                hole=0.55,
                marker=dict(colors=["#ef4444", "#6366f1", "#10b981", "#f59e0b"]),
                textinfo="label+value",
                textfont=dict(color="#e2e8f0", size=12)
            )])
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                height=300,
                margin=dict(l=0, r=0, t=20, b=20),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No memories stored yet. Submit corrections below or run the feedback processor agent.")
    
    with learn_col2:
        st.markdown("##### 🔄 How Self-Learning Works")
        st.markdown("""
        <div style="
            background: rgba(99, 102, 241, 0.08);
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 10px;
            padding: 16px;
            font-size: 0.8rem;
            color: #cbd5e1;
        ">
            <div style="margin-bottom: 8px;"><b>1. Capture</b> → Human corrections to risk scores, architecture mappings, or wave sequences are stored as learning signals.</div>
            <div style="margin-bottom: 8px;"><b>2. Index</b> → Each memory includes context (workload type, OS, risk level) for retrieval matching.</div>
            <div style="margin-bottom: 8px;"><b>3. Retrieve</b> → When agents encounter similar workloads, they query the memory store for relevant past corrections.</div>
            <div style="margin-bottom: 8px;"><b>4. Apply</b> → Retrieved corrections adjust agent confidence and modify recommendations.</div>
            <div><b>5. Evaluate</b> → Outcomes are tracked to rank memory effectiveness over time.</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("---")
    
    # --- Submit Manual Correction ---
    st.subheader("✏️ Submit Agent Correction")
    st.caption("Provide a correction to improve D.A.M.I.'s future decision-making. This feeds directly into the memory store.")
    
    with st.form("correction_form"):
        form_col1, form_col2 = st.columns(2)
        with form_col1:
            agent_name = st.selectbox("Agent to correct", [
                "risk_scorer_agent",
                "architecture_designer_agent",
                "wave_planner_agent",
                "discovery_agent",
                "dependency_mapper_agent"
            ])
            learning_type = st.selectbox("Correction type", [
                "correction", "pattern", "optimization", "insight"
            ])
        with form_col2:
            workload_type = st.selectbox("Workload context", [
                "WEB", "APP", "DB", "LB", "CACHE", "QUEUE", "INFRA"
            ])
            risk_level = st.selectbox("Risk level context", [
                "low", "medium", "high", "critical"
            ])
        
        original = st.text_area("What D.A.M.I. originally recommended:", 
                               placeholder="e.g., Recommended Rehost to Compute Engine n2-standard-4")
        corrected = st.text_area("What the correct recommendation should be:",
                                placeholder="e.g., Should be Replatform to Cloud SQL Enterprise for this Oracle DB workload")
        
        submitted = st.form_submit_button("💾 Store Correction", use_container_width=True)
        
        if submitted and original and corrected:
            context = {
                "workload_type": workload_type,
                "risk_level": risk_level,
            }
            memory_id = store.store_learning(
                agent_name=agent_name,
                learning_type=learning_type,
                context=context,
                original_output=original,
                corrected_output=corrected,
                confidence_delta=-0.1 if learning_type == "correction" else 0.05,
                tags=[workload_type, risk_level]
            )
            st.success(f"Correction stored! Memory ID: `{memory_id}`")
            st.rerun()
    
    st.write("---")
    
    # --- Memory History Table ---
    st.subheader("📋 Recent Learning History")
    
    try:
        client = bigquery.Client(project=project_id)
        df = client.query(f"""
            SELECT memory_id, agent_name, learning_type, 
                   original_output, corrected_output, confidence_delta,
                   applied_count, effectiveness_score, created_at
            FROM `{project_id}.{dataset}.agent_memories`
            ORDER BY created_at DESC
            LIMIT 20
        """).to_dataframe()
        
        if not df.empty:
            # Color code by type
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "memory_id": st.column_config.TextColumn("ID", width="small"),
                    "agent_name": st.column_config.TextColumn("Agent", width="medium"),
                    "learning_type": st.column_config.TextColumn("Type", width="small"),
                    "original_output": st.column_config.TextColumn("Original", width="large"),
                    "corrected_output": st.column_config.TextColumn("Corrected", width="large"),
                    "confidence_delta": st.column_config.NumberColumn("Δ Confidence", format="%.2f"),
                    "applied_count": st.column_config.NumberColumn("Applied", width="small"),
                    "effectiveness_score": st.column_config.NumberColumn("Effectiveness", format="%.2f"),
                }
            )
        else:
            st.info("No memories stored yet. Submit a correction above to get started.")
    except Exception as e:
        st.warning(f"Could not load memory history: {e}")
    
    st.write("---")
    
    # --- Architecture Diagram ---
    st.subheader("🏗️ Self-Learning Architecture")
    st.markdown("""
    ```
    ┌─────────────────────────────────────────────────────────────┐
    │                   D.A.M.I. Self-Learning Loop                │
    │                                                              │
    │   Human Correction ──▶ Memory Store ──▶ Agent Context        │
    │         │                   │                │                │
    │         │          ┌───────┴───────┐        │                │
    │         │          │               │        ▼                │
    │         │    ┌─────┴─────┐  ┌──────┴─────┐                  │
    │         │    │  BigQuery  │  │  AlloyDB   │  Agent Decision  │
    │         │    │  (keyword) │  │  (pgvector)│  ──▶ Output      │
    │         │    └─────┬─────┘  └──────┬─────┘        │         │
    │         │          └───────┬───────┘              │         │
    │         │                  │                       │         │
    │         │          Retrieval Ranking               │         │
    │         │          (effectiveness_score)           │         │
    │         │                  │                       │         │
    │         └──────────────────┘◀──── Outcome Tracking │         │
    │                                   (was_helpful?)   │         │
    └─────────────────────────────────────────────────────────────┘
    ```
    """)


if __name__ == "__main__":
    render()
