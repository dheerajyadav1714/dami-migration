# chat.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
import pandas as pd
from google.cloud import bigquery
import requests
import json

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
        risk_df = client.query(f"SELECT risk_level, COUNT(*) as count FROM `{project_id}.{dataset}.servers` GROUP BY risk_level").to_dataframe()
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

def get_orchestrator_response(query):
    """Route all queries through Gemini grounded on live BigQuery data."""
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    
    try:
        from google.genai import Client
        from google.genai import types
        
        vertex_project = os.getenv("VERTEX_PROJECT_ID", "gcp-experiments-490315")
        location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        model_name = "gemini-2.5-flash"
        
        client = Client(enterprise=True)
        model_path = f"projects/{vertex_project}/locations/{location}/publishers/google/models/{model_name}"
        
        context = get_bq_context()
        
        system_instruction = (
            "You are D.A.M.I. (Discovery & Autonomous Migration Intelligence) Conversational Assistant. "
            "You help migration architects with VMware-to-Google Cloud migration planning. "
            "Ground ALL answers in the live BigQuery migration database context provided. "
            "Be concise, technical, and professional. Use markdown formatting.\n\n"
            "When the user asks a quantitative question, generate a BigQuery SQL query inside ```sql ... ``` blocks. "
            "IMPORTANT SQL RULES:\n"
            "- ALWAYS use column aliases for aggregations (e.g. COUNT(*) AS server_count, not bare COUNT(*)).\n"
            "- All string values are LOWERCASE (e.g. risk_level='high' NOT 'High').\n"
            "- compliance_flags is ARRAY<STRING>. Use UNNEST() to filter (e.g. WHERE flag IN UNNEST(compliance_flags)).\n"
            "- Use LIMIT 20 for large result sets.\n\n"
            "Use ONLY these verified table schemas:\n"
            f"- `{project_id}.{dataset}.servers` — columns: server_id, name, vcpu, ram_gb, disk_gb, os, os_version, "
            "ip_address, cluster, datacenter, power_state, cpu_utilization_avg, ram_utilization_avg, "
            "workload_type, app_owner, environment, source_platform, compliance_flags (ARRAY<STRING>), risk_level\n"
            f"  VALUES: risk_level IN ('low','medium','high','critical'), power_state IN ('poweredOn','poweredOff'), "
            "environment IN ('Production','Development','Staging','DR')\n"
            f"- `{project_id}.{dataset}.risk_scores` — columns: server_id, overall_risk_score, risk_level, "
            "complexity_score, dependency_risk, data_sensitivity, business_criticality, recommended_strategy, "
            "migration_effort_days, risk_factors, mitigation_plan\n"
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
        print(f"Gemini query failed: {e}")
        # Graceful fallback with BQ context summary
        try:
            context = get_bq_context()
            return (
                f"I have access to your migration database with **{context['discovered_servers']} discovered servers**, "
                f"mapped across **{len(context.get('waves_breakdown', []))} waves**. "
                f"The estimated annual cloud cost savings is **${context.get('cost_estimates', {}).get('estimated_annual_savings', 'N/A'):,.0f}**.\n\n"
                f"I was unable to generate a detailed AI response at this time. Please try again or ask a more specific question about your migration data."
            )
        except:
            return "I'm currently experiencing connectivity issues with the AI backend. Please try again in a moment."

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
    st.markdown("<h1 class='gradient-text'>Conversational Migration Assistant</h1>", unsafe_allow_html=True)
    st.write("Interact with D.A.M.I using natural language queries to fetch migration statistics, check dependencies, and get architectural recommendations.")
    st.write("---")
    
    # Initialize Chat History
    if "messages" not in st.session_state:
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
        st.rerun()

if __name__ == "__main__":
    render()

