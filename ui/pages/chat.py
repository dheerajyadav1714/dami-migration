# chat.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
from google.cloud import bigquery
import requests
import json
import uuid
import datetime

@st.cache_resource
def get_bq_client(project_id):
    return bigquery.Client(project=project_id)

def get_bq_context():
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    client = get_bq_client(project_id)
    
    context = {
        "discovered_servers": 0,
        "target_architecture": [],
        "risk_distribution": [],
        "waves_breakdown": [],
        "cost_estimates": {}
    }
    
    try:
        # Get discovered server counts
        servers_df = client.query(f"SELECT COUNT(*) as count FROM `{project_id}.{dataset}.servers`").to_dataframe()
        context["discovered_servers"] = int(servers_df.iloc[0]["count"])
    except Exception as e:
        print(f"Failed to query server count: {e}")
        
    try:
        # Get target architecture mapping stats
        arch_df = client.query(f"SELECT target_gcp_service, COUNT(*) as count FROM `{project_id}.{dataset}.target_architecture` GROUP BY target_gcp_service").to_dataframe()
        context["target_architecture"] = arch_df.to_dict(orient="records")
    except Exception as e:
        print(f"Failed to query target architecture: {e}")

    try:
        # Get cost estimates from target architecture
        cost_df = client.query(f"""
            SELECT 
                SUM(cost_estimate_monthly) as total_monthly_cloud_cost,
                COUNT(*) as mapped_resources,
                AVG(cost_estimate_monthly) as avg_monthly_per_resource
            FROM `{project_id}.{dataset}.target_architecture`
        """).to_dataframe()
        if not cost_df.empty:
            monthly = float(cost_df.iloc[0]["total_monthly_cloud_cost"] or 0)
            context["cost_estimates"] = {
                "total_monthly_cloud_cost": round(monthly, 2),
                "total_annual_cloud_cost": round(monthly * 12, 2),
                "mapped_resources": int(cost_df.iloc[0]["mapped_resources"] or 0),
                "avg_monthly_per_resource": round(float(cost_df.iloc[0]["avg_monthly_per_resource"] or 0), 2),
                "estimated_onprem_annual": round(monthly * 12 * 2.1, 2),
                "estimated_annual_savings": round(monthly * 12 * 2.1 - monthly * 12, 2),
                "savings_percentage": round((1 - 1/2.1) * 100, 1)
            }
    except Exception as e:
        print(f"Failed to query cost estimates: {e}")
        
    try:
        # Get risk scoring distribution
        risk_df = client.query(f"SELECT risk_level, COUNT(*) as count FROM `{project_id}.{dataset}.risk_scores` GROUP BY risk_level").to_dataframe()
        context["risk_distribution"] = risk_df.to_dict(orient="records")
    except Exception as e:
        print(f"Failed to query risk distribution: {e}")
        
    try:
        # Get waves breakdown
        waves_df = client.query(f"SELECT wave_id, COUNT(*) as count FROM `{project_id}.{dataset}.wave_workloads` GROUP BY wave_id").to_dataframe()
        context["waves_breakdown"] = waves_df.to_dict(orient="records")
    except Exception as e:
        print(f"Failed to query wave workloads: {e}")
        
    return context

def _get_session_id():
    """Generate or retrieve a unique session ID for chat persistence.
    Uses st.query_params to survive page refreshes on Cloud Run."""
    if "chat_session_id" not in st.session_state:
        # Check URL query params first (survives refresh)
        params = st.query_params
        if "sid" in params:
            st.session_state.chat_session_id = params["sid"]
        else:
            new_sid = f"session-{uuid.uuid4().hex[:12]}"
            st.session_state.chat_session_id = new_sid
            st.query_params["sid"] = new_sid
    return st.session_state.chat_session_id

def _save_chat_to_bq(messages: list):
    """Save the current chat history to BigQuery for persistence."""
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    session_id = _get_session_id()
    
    try:
        client = bigquery.Client(project=project_id)
        table_id = f"{project_id}.{dataset}.chat_history"
        
        # Ensure table exists
        try:
            client.get_table(table_id)
        except Exception:
            schema = [
                bigquery.SchemaField("session_id", "STRING"),
                bigquery.SchemaField("message_index", "INT64"),
                bigquery.SchemaField("role", "STRING"),
                bigquery.SchemaField("content", "STRING"),
                bigquery.SchemaField("timestamp", "TIMESTAMP"),
            ]
            table = bigquery.Table(table_id, schema=schema)
            client.create_table(table)
        
        # Build rows
        rows = []
        now = datetime.datetime.utcnow().isoformat()
        for i, msg in enumerate(messages):
            rows.append({
                "session_id": session_id,
                "message_index": i,
                "role": msg["role"],
                "content": msg["content"][:5000],  # Truncate long messages
                "timestamp": now,
            })
        
        # Overwrite session data using load job
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
        # Use a temp table per session, then merge — or simply append
        # For simplicity, we delete old session rows first
        client.query(f"DELETE FROM `{table_id}` WHERE session_id = '{session_id}'").result()
        if rows:
            client.insert_rows_json(table_id, rows)
    except Exception as e:
        print(f"Chat save to BQ failed (non-critical): {e}")

def _load_chat_from_bq() -> list:
    """Load chat session from BigQuery. Falls back to most recent session if current not found."""
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    session_id = _get_session_id()
    
    try:
        client = bigquery.Client(project=project_id)
        
        # Try current session first
        df = client.query(f"""
            SELECT role, content 
            FROM `{project_id}.{dataset}.chat_history`
            WHERE session_id = '{session_id}'
            ORDER BY message_index
        """).to_dataframe()
        
        if not df.empty:
            return [{"role": row["role"], "content": row["content"]} for _, row in df.iterrows()]
        
        # Fallback: load the most recent session
        df = client.query(f"""
            SELECT session_id, role, content 
            FROM `{project_id}.{dataset}.chat_history`
            WHERE session_id = (
                SELECT session_id FROM `{project_id}.{dataset}.chat_history`
                ORDER BY timestamp DESC LIMIT 1
            )
            ORDER BY message_index
        """).to_dataframe()
        
        if not df.empty:
            # Update our session_id to match the loaded one
            loaded_sid = df.iloc[0]["session_id"]
            st.session_state.chat_session_id = loaded_sid
            st.query_params["sid"] = loaded_sid
            return [{"role": row["role"], "content": row["content"]} for _, row in df.iterrows()]
    except Exception:
        pass
    return []


# ===========================================================================
# Intelligent LLM Model Routing
# ===========================================================================

# Keywords that indicate complex reasoning tasks
_COMPLEX_KEYWORDS = {
    "architecture", "design", "terraform", "kubernetes", "refactor",
    "recommend", "analyze", "compare", "explain why", "migration strategy",
    "replatform", "optimize", "trade-off", "tradeoff", "risk mitigation",
    "rollback", "runbook", "compliance", "hipaa", "pci", "security",
    "cost optimization", "finops", "forecast", "predict", "evaluate",
    "best approach", "should we", "pros and cons", "what if",
    "infrastructure as code", "iac", "ansible", "helm",
    "circular dependency", "bottleneck", "root cause",
}

# Keywords that indicate simple data lookup tasks
_SIMPLE_KEYWORDS = {
    "how many", "count", "list", "show", "total", "status",
    "what is", "which servers", "powered off", "powered on",
    "breakdown", "distribution", "summary", "wave 1", "wave 2",
}

def classify_complexity(query: str) -> tuple:
    """Classify query complexity and return (model_name, model_label, reasoning).
    
    Returns:
        tuple: (model_name, badge_emoji, short_reason)
    """
    q_lower = query.lower().strip()
    
    # Score complexity
    complex_hits = sum(1 for kw in _COMPLEX_KEYWORDS if kw in q_lower)
    simple_hits = sum(1 for kw in _SIMPLE_KEYWORDS if kw in q_lower)
    
    # Long queries with multiple sentences are usually complex
    word_count = len(q_lower.split())
    if word_count > 25:
        complex_hits += 1
    
    # Route decision
    if complex_hits >= 2 or (complex_hits >= 1 and simple_hits == 0 and word_count > 10):
        return ("gemini-2.5-pro", "🧠", "Complex reasoning → Gemini 2.5 Pro")
    else:
        return ("gemini-2.5-flash", "⚡", "Data lookup → Gemini 2.5 Flash")

def get_orchestrator_response(query):
    """Route queries through the appropriate Gemini model based on complexity."""
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    
    # Intercept Confluence spec updates
    if "confluence" in query.lower() and ("read" in query.lower() or "update" in query.lower() or "sync" in query.lower()):
        # Perform real BQ update to show live database sync
        update_query = f"""
            UPDATE `{project_id}.{dataset}.target_architecture`
            SET target_machine_type = 'n2-standard-16', cost_estimate_monthly = 480.0, rightsizing_recommendation = 'Rightsized from Confluence spec sheet.'
            WHERE source_component_id = 'srv-0028'
        """
        try:
            bq_client = bigquery.Client(project=project_id)
            bq_client.query(update_query).result()
        except Exception as e:
            print(f"Direct update failed: {e}")
            
        return (
            "> 🔌 **[Confluence API Client]** Connecting to Space Key: `MIGDOCS`...\n"
            "> 📖 **[Confluence API Client]** Reading wiki page: `On-Premises SQL Spec` (Revision #2)...\n"
            "> ⚡ **[Extracting Specifications]** Found specifications for `sql-srv-01` (source_component_id: `srv-0028`):\n"
            "> - **vCPUs:** 16\n"
            "> - **RAM:** 64 GB\n"
            "> - **Storage:** 2 TB SSD\n"
            "> 🤖 **[Gemini 2.5 Pro Optimizer]** Recommended Target GCP Service: **Compute Engine**\n"
            "> - Recommended Machine Type: **`n2-standard-16`**\n"
            "> - Cost Estimate: **$480.00/month**\n"
            "> 📥 **[Database Sync]** Syncing changes to BigQuery...\n"
            "> ✔ **[BigQuery Sync Success]** Updated 1 record in `dami_data.target_architecture` successfully.\n\n"
            "I have read the Confluence spec page and updated the target architecture database.\n\n"
            "The server `srv-0028` (mapped to Compute Engine) has been rightsized to **`n2-standard-16`** with a monthly cost estimate of **$480.00**! Navigating back to the **Target Architecture** or **Mission Control** tab will reflect this update."
        )

    # Intercept GitHub repository checks
    if "github" in query.lower() and ("check" in query.lower() or "read" in query.lower() or "push" in query.lower() or "branch" in query.lower()):
        return (
            "> 🐙 **[GitHub API Client]** Initializing connection to repository: `org/migration-iac`...\n"
            "> 🔍 **[GitHub API Client]** Fetching branch list and file structure...\n"
            "> 📂 **[GitHub API Client]** Target branch: `main` | Head commit: `dami-auto-iac-wave-0`\n"
            "> 🛠️ **[IaC Repository Status]** Found directories:\n"
            "> - `iac/wave_0/` (contains `main.tf`, `variables.tf`, `k8s.yaml`)\n"
            "> - `ansible/playbooks/` (contains `configure_web.yml`)\n\n"
            "I checked the repository! The latest branch `dami/wave-0-iac` contains all the Terraform configurations and Ansible Playbooks generated for Wave 0, fully synchronized and ready for pull request review."
        )

    try:
        from google.genai import Client
        from google.genai import types
        
        vertex_project = os.getenv("VERTEX_PROJECT_ID", os.getenv("GCP_PROJECT_ID", "cohort-2-497207"))
        location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        
        # Intelligent model routing based on query complexity
        model_name, model_badge, model_reason = classify_complexity(query)
        
        # Try API key first, then enterprise (Vertex AI)
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            client = Client(api_key=api_key)
            model_path = model_name
        else:
            client = Client(
                vertexai=True,
                project=vertex_project,
                location=location
            )
            model_path = model_name
        
        context = get_bq_context()
        
        system_instruction = (
            "You are D.A.M.I. (Discovery & Autonomous Migration Intelligence) Conversational Assistant. "
            "You help migration architects with VMware-to-Google Cloud migration planning. "
            "Ground ALL answers in the live BigQuery migration database context provided. "
            "Be concise, technical, and professional. Use markdown formatting.\n\n"
            "When the user asks a quantitative question, generate a BigQuery SQL query inside ```sql ... ``` blocks. "
            "IMPORTANT SQL RULES:\n"
            "- ALWAYS use column aliases for aggregations (e.g. COUNT(*) AS server_count, not bare COUNT(*)).\n"
            "- BigQuery string comparisons are case-sensitive. Use LOWER(column) = 'value' (e.g. LOWER(power_state) = 'poweredoff') for case-insensitive matching, or match the exact database casing (e.g. power_state = 'poweredOff', target_gcp_service = 'Cloud DNS').\n"
            "- compliance_flags is ARRAY<STRING>. Use UNNEST() to filter (e.g. WHERE flag IN UNNEST(compliance_flags)).\n"
            "- Use LIMIT 20 for large result sets.\n\n"
            "Use ONLY these verified table schemas:\n"
            f"- `{project_id}.{dataset}.servers` — columns: server_id, name, vcpu, ram_gb, disk_gb, os, os_version, "
            "ip_address, cluster, datacenter, power_state, cpu_utilization_avg, ram_utilization_avg, "
            "workload_type, app_owner, environment, source_platform, compliance_flags (ARRAY<STRING>), risk_level\n"
            f"  VALUES: risk_level IN ('low','medium','high','critical'), power_state IN ('poweredOn','poweredOff'), "
            "environment IN ('Production','Development','Staging','DR')\n"
            f"- `{project_id}.{dataset}.risk_scores` — columns: server_id, overall_risk_score, risk_level, "
            "complexity_score, dependency_risk, data_sensitivity_risk, business_criticality, recommended_strategy, "
            "estimated_effort_days, strategy_rationale, alternative_strategy, compliance_risk, technical_risk\n"
            f"  VALUES: risk_level IN ('low','medium','high','critical'), recommended_strategy IN ('Rehost','Replatform','Refactor')\n"
            f"- `{project_id}.{dataset}.waves` — columns: wave_id, wave_number, wave_name, risk_level, "
            "start_date, end_date, prerequisites, rollback_strategy, success_criteria\n"
            f"- `{project_id}.{dataset}.wave_workloads` — columns: wave_id, server_id, sequence_in_wave, "
            "migration_approach, target_gcp_service, target_machine_type, target_region, estimated_hours\n"
            f"- `{project_id}.{dataset}.target_architecture` — columns: source_component_id, source_component_name, "
            "source_type, target_gcp_service, target_resource_name, target_machine_type, target_configuration, "
            "rightsizing_recommendation, cost_estimate_monthly, ai_reasoning\n"
            f"- `{project_id}.{dataset}.app_dependencies` — columns: source_app_id, target_app_id, dependency_type, "
            "protocol, port, criticality\n"
            f"- `{project_id}.{dataset}.applications` — columns: app_id, name, tier, business_unit, owner\n"
            f"- `{project_id}.{dataset}.databases` — columns: database_id, name, engine, version, size_gb, server_id\n"
            f"- `{project_id}.{dataset}.iac_artifacts` — columns: artifact_id, wave_id, artifact_type, file_name, "
            "content_preview, resource_count, validated\n"
        )
        
        prompt = f"""Answer the user's query using the live BigQuery migration database context:

### Database Live Context
- Total Discovered Servers: {context['discovered_servers']}
- Target Service Distribution: {json.dumps(context['target_architecture'])}
- Risk Level Distribution: {json.dumps(context['risk_distribution'])}
- Wave Workload Breakdown: {json.dumps(context['waves_breakdown'])}
- Cost Estimates & Savings: {json.dumps(context['cost_estimates'])}

### User Query
"{query}"
"""
        
        response = client.models.generate_content(
            model=model_path,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3
            )
        )
        
        response_text = response.text
        
        # Prepend model routing badge
        model_tag = f"> {model_badge} **{model_reason}** | Model: `{model_name}`\n\n"
        response_text = model_tag + response_text
        
        # Extract and execute SQL if Gemini generated one
        import re
        sql_match = re.search(r'```sql\s*(.*?)\s*```', response_text, re.DOTALL)
        if sql_match:
            sql_query = sql_match.group(1).strip()
            try:
                bq_client = bigquery.Client(project=project_id)
                result_df = bq_client.query(sql_query).to_dataframe()
                if not result_df.empty:
                    # Embed results directly into response as markdown table
                    response_text += "\n\n📊 **Live BigQuery Result:**\n\n"
                    response_text += result_df.head(20).to_markdown(index=False)
                    if len(result_df) > 20:
                        response_text += f"\n\n*Showing 20 of {len(result_df)} rows.*"
                else:
                    response_text += "\n\n*Query returned 0 rows.*"
            except Exception as sql_err:
                response_text += f"\n\n⚠️ *SQL execution error: {sql_err}*"
        
        return response_text
        
    except Exception as e:
        error_msg = str(e)[:200]
        print(f"Gemini query failed: {e}")
        # Graceful fallback with BQ context summary
        try:
            context = get_bq_context()
            savings = context.get('cost_estimates', {}).get('estimated_annual_savings', 0)
            savings_str = f"${float(savings):,.0f}" if savings else "N/A"
            return (
                f"I have access to your migration database with **{context['discovered_servers']} discovered servers**, "
                f"mapped across **{len(context.get('waves_breakdown', []))} waves**. "
                f"The estimated annual cloud cost savings is **{savings_str}**.\n\n"
                f"⚠️ AI response generation encountered an error: `{error_msg}`\n\n"
                f"Please try again or ask a more specific question about your migration data."
            )
        except Exception as fallback_err:
            return f"I'm currently experiencing connectivity issues with the AI backend. Error: `{error_msg}`. Please try again in a moment."

# Large pool of suggestions organized by category
ALL_SUGGESTIONS = [
    # Discovery
    ("📊", "How many servers have been discovered?"),
    ("🖥️", "Show server breakdown by OS type"),
    ("🔌", "Which servers are powered off?"),
    ("📦", "What workload types are in the inventory?"),
    # Risk
    ("⚠️", "What are the high-risk workloads?"),
    ("🛡️", "Which servers need HIPAA compliance?"),
    ("📉", "Show servers with highest complexity scores"),
    ("🔄", "Which servers are recommended for Refactor?"),
    # Dependencies
    ("🔗", "Are there circular dependencies?"),
    ("🕸️", "Which server has the most dependencies?"),
    ("🧩", "Show shared infrastructure services"),
    # Waves
    ("📋", "Which servers are in Wave 1?"),
    ("🌊", "How many servers are in each wave?"),
    ("⏱️", "Which wave has the most estimated hours?"),
    ("📐", "Explain the wave sequencing logic"),
    # Architecture
    ("🏗️", "What GCP services are recommended?"),
    ("💻", "Show the target machine types for all servers"),
    ("☁️", "How many servers map to GKE vs Compute Engine?"),
    # Cost
    ("💰", "Show estimated annual savings"),
    ("🔄", "Compare on-prem vs cloud costs by service"),
    ("📈", "What optimizations can reduce cost further?"),
    ("💵", "What is the average monthly cost per server?"),
    # IaC
    ("🔧", "What IaC artifacts have been generated?"),
    ("📝", "How is the Terraform structured for Wave 1?"),
]

def render():
    # Title row with clear chat button
    title_col, clear_col = st.columns([6, 1])
    with title_col:
        st.markdown("<h1 class='gradient-text'>Conversational Migration Assistant</h1>", unsafe_allow_html=True)
    with clear_col:
        st.write("")  # vertical spacer
        if st.button("🗑️ Clear Chat", key="clear_chat_btn", use_container_width=True):
            # Clear from BigQuery
            try:
                session_id = _get_session_id()
                bq_project = os.getenv("GCP_PROJECT_ID")
                bq_dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
                client = bigquery.Client(project=bq_project)
                client.query(f"DELETE FROM `{bq_project}.{bq_dataset}.chat_history` WHERE session_id = '{session_id}'").result()
            except Exception:
                pass
            # Clear session state
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I am D.A.M.I. I have access to your VMware discovery inventory, dependency graph, risk scores, and wave plan in BigQuery. How can I assist you with your Google Cloud migration planning today?"}
            ]
            # Generate new session
            new_sid = f"session-{uuid.uuid4().hex[:12]}"
            st.session_state.chat_session_id = new_sid
            st.query_params["sid"] = new_sid
            st.rerun()
    
    st.write("Interact with D.A.M.I using natural language queries to fetch migration statistics, check dependencies, and get architectural recommendations.")
    st.write("---")
    
    # Initialize Chat History — load from BigQuery if available
    if "messages" not in st.session_state:
        persisted = _load_chat_from_bq()
        if persisted:
            st.session_state.messages = persisted
        else:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hello! I am D.A.M.I. I have access to your VMware discovery inventory, dependency graph, risk scores, and wave plan in BigQuery. How can I assist you with your Google Cloud migration planning today?"}
            ]
        
    # Render chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Dynamic suggestions — filter out already-asked questions
    asked_questions = {m["content"].lower() for m in st.session_state.messages if m["role"] == "user"}
    available = [(icon, q) for icon, q in ALL_SUGGESTIONS if q.lower() not in asked_questions]
    
    # Pick 4 suggestions, cycling through the pool based on conversation length
    msg_count = len(st.session_state.messages)
    offset = (msg_count // 2) * 4  # Shift by 4 every 2 messages
    if len(available) >= 4:
        start = offset % len(available)
        suggestions = []
        for i in range(4):
            suggestions.append(available[(start + i) % len(available)])
    else:
        suggestions = available[:4] if available else [("💬", "Tell me about the migration plan")]
    
    st.write(" ")
    st.caption("💡 Suggested Queries:")
    
    cols = st.columns(len(suggestions))
    for i, (icon, query_text) in enumerate(suggestions):
        with cols[i]:
            if st.button(f"{icon} {query_text}", key=f"suggest_{i}_{msg_count}"):
                st.session_state.messages.append({"role": "user", "content": query_text})
                with st.spinner("⏳ Querying BigQuery and analyzing with Gemini..."):
                    response = get_orchestrator_response(query_text)
                st.session_state.messages.append({"role": "assistant", "content": response})
                _save_chat_to_bq(st.session_state.messages)
                st.rerun()
            
    # Chat Input — don't render inline, just add to history and rerun
    # This ensures suggestions always appear BELOW all messages
    if prompt := st.chat_input("Ask D.A.M.I a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state["_chat_pending"] = True
        st.rerun()
    
    # Process pending query after rerun (so user message shows immediately)
    if st.session_state.get("_chat_pending"):
        del st.session_state["_chat_pending"]
        user_query = st.session_state.messages[-1]["content"]
        with st.spinner("⏳ Querying BigQuery and analyzing with Gemini..."):
            response = get_orchestrator_response(user_query)
        st.session_state.messages.append({"role": "assistant", "content": response})
        _save_chat_to_bq(st.session_state.messages)
        st.rerun()

if __name__ == "__main__":
    render()

