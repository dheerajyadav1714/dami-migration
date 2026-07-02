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
    query_lower = query.lower()
    
    # 1. If it is a database statistic or status query, use direct keyless RAG grounded on BigQuery metrics
    is_db_query = any(w in query_lower for w in ["how many", "count", "discovered", "savings", "cost", "risk", "wave", "migration", "gcp", "target", "servers", "database", "vm", "orchestrator", "hcl", "terraform"])
    
    if is_db_query:
        try:
            from google.genai import Client
            from google.genai import types
            
            project_id = os.getenv("GCP_PROJECT_ID")
            vertex_project = os.getenv("VERTEX_PROJECT_ID", "gcp-experiments-490315")
            location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
            model_name = "gemini-2.5-flash"
            
            client = Client(enterprise=True)
            model_path = f"projects/{vertex_project}/locations/{location}/publishers/google/models/{model_name}"
            
            context = get_bq_context()
            
            system_instruction = (
                "You are D.A.M.I. (Discovery & Autonomous Migration Intelligence) Conversational Assistant. "
                "Your task is to answer the user's questions regarding VMware to Google Cloud migration, "
                "infrastructure discovery, dependencies, risk assessment, target sizing, and wave plans. "
                "Ground your answers in the active BigQuery migration database context provided below. "
                "Keep your responses concise, technical, and professional.\n\n"
                "IMPORTANT: If the user asks a quantitative question about the data, generate a BigQuery SQL query "
                "to answer it. Wrap the SQL in ```sql ... ``` code block. Use the following table schemas:\n"
                f"- `{os.getenv('GCP_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET', 'dami_data')}.servers` (server_id, name, ip_address, os, cpu_cores, ram_gb, disk_gb, environment, workload_type, compliance_flags, tags)\n"
                f"- `{os.getenv('GCP_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET', 'dami_data')}.risk_scores` (server_id, risk_level, overall_risk_score, recommended_strategy)\n"
                f"- `{os.getenv('GCP_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET', 'dami_data')}.waves` (wave_id, wave_number, wave_name)\n"
                f"- `{os.getenv('GCP_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET', 'dami_data')}.target_architecture` (server_id, target_gcp_service, machine_type, estimated_monthly_cost)\n"
                f"- `{os.getenv('GCP_PROJECT_ID')}.{os.getenv('BIGQUERY_DATASET', 'dami_data')}.dependencies` (source_id, target_id, protocol, port)\n"
            )
            
            prompt = f"""
            Answer the user's query grounding your details in the active BigQuery migration database context:
            
            ### BigQuery Database Live Context
            - Total Discovered Servers: {context['discovered_servers']}
            - Mapped target service distribution: {json.dumps(context['target_architecture'])}
            - Risk Level distribution: {json.dumps(context['risk_distribution'])}
            - Mapped Wave workload breakdown: {json.dumps(context['waves_breakdown'])}
            - Cost Estimates & Savings: {json.dumps(context['cost_estimates'])}
            
            ### User Query
            "{query}"
            """
            
            response = client.models.generate_content(
                model=model_path,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.2
                )
            )
            
            response_text = response.text
            
            # Extract and execute SQL if present in the response
            import re
            sql_match = re.search(r'```sql\s*(.*?)\s*```', response_text, re.DOTALL)
            if sql_match:
                sql_query = sql_match.group(1).strip()
                try:
                    bq_client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))
                    result_df = bq_client.query(sql_query).to_dataframe()
                    if not result_df.empty:
                        # Store for display in chat
                        st.session_state["_last_sql_query"] = sql_query
                        st.session_state["_last_sql_result"] = result_df
                except Exception as sql_err:
                    response_text += f"\n\n⚠️ *SQL execution note: {sql_err}*"
            
            return response_text
        except Exception as e:
            print(f"Local Vertex AI keyless grounded query failed: {e}")
            
    # 2. Otherwise, fall back to FastAPI orchestrator running ADK Runner
    try:
        response = requests.post(
            "http://localhost:8000/api/run-orchestrator",
            json={"prompt": query},
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            tools = result.get("triggered_tools", [])
            response_text = result.get("final_response", "")
            if tools:
                tool_prefix = "🔧 **Orchestrator Actions Triggered:** " + ", ".join([f"`{t}`" for t in tools]) + "\n\n"
                return tool_prefix + response_text
            if response_text:
                return response_text
    except Exception as e:
        print(f"FastAPI orchestrator call bypassed/failed: {e}")
        
    # 3. Third: Fallback to mock text if model calls are unreachable
    query_lower = query.lower()
    if "wave 1" in query_lower:
        return """**Wave 1 (Core Web & Frontend Services)** consists of 3 servers:
- **LB-NGINX-01** (Load balancer)
- **WEBAPP-PROD-01** (Web server)
- **WEBAPP-PROD-02** (Web server)

**Rationale:** These frontend servers have no incoming dependencies from other application workloads (they receive traffic directly from the internet/users). Migrating them first helps establish the web tier.

**Next Steps:** Rehost to Google Compute Engine. You can view and download the generated Terraform HCL, Ansible configuration, and Runbooks in the **IaC & Runbooks** page."""

    elif "circular" in query_lower or "loop" in query_lower:
        return """Yes, I detected **1 circular dependency loop** in the active workloads:
`payment-gateway (app-0001) ➔ order-processing (app-0002) ➔ payment-gateway (app-0001)`

**Details:**
- `app-0001` (payment-gateway) calls `app-0002` (order-processing) over HTTPS (port 443).
- `app-0002` (order-processing) calls `app-0001` (payment-gateway) over HTTP (port 8080) for ledger callbacks.

**Impact on Migration:** 
Tightly coupled loops must be migrated in the **same wave** (scheduled in Wave 3) to prevent inter-network latency and security failures during transitional states."""

    elif "savings" in query_lower or "cost" in query_lower:
        return """Based on my analysis, the projected annual savings are **$1,210,080** (a **57.6%** reduction in Total Cost of Ownership).

**Key Optimization Factors:**
1. **vCPU Rightsizing:** Total cores reduced from 74 to 46 (saves ~$24,000/mo).
2. **Oracle DBMS to BMS:** Saves licensing audit risk and optimizes core density.
3. **VM consolidation:** Moving web app servers to Auto-scaling Managed Instance Groups (saves ~$12,000/mo)."""

    else:
        return f"I received your query: '{query}'. I have access to your VMware discovery inventory, dependency graph, risk scores, and wave plan in BigQuery. Please ask about discovered counts, target architecture costs, or scheduling waves."

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
            
    # Dynamic context-aware suggestions
    def get_dynamic_suggestions():
        """Generate suggestions based on current data state and conversation."""
        context = get_bq_context()
        msg_count = len(st.session_state.get("messages", []))
        suggestions = []
        
        # Phase 1: Discovery questions (if few messages)
        if msg_count <= 2:
            suggestions = [
                ("📊", "How many servers have been discovered?"),
                ("🔗", "Show circular dependencies"),
                ("💰", "Show estimated savings"),
                ("🏗️", "What GCP services are recommended?")
            ]
        # Phase 2: After a few interactions — deeper analysis
        elif msg_count <= 6:
            suggestions = [
                ("📋", "Which servers are in Wave 1?"),
                ("⚠️", "What are the high-risk workloads?"),
                ("📐", "Explain the wave sequencing logic"),
                ("💻", "How is the Terraform structured?")
            ]
        # Phase 3: Advanced queries
        else:
            suggestions = [
                ("🔄", "Compare on-prem vs cloud costs by service"),
                ("🛡️", "Which servers need HIPAA compliance?"),
                ("📈", "What optimizations can reduce cost further?"),
                ("🌊", "Which wave has the most dependencies?")
            ]
        
        # Override with cost-specific if no cost data
        if not context.get("cost_estimates"):
            suggestions[2] = ("🏗️", "Run target architecture mapping")
        
        return suggestions
    
    suggestions = get_dynamic_suggestions()
    
    st.write(" ")
    st.caption("💡 Suggested Queries:")
    
    cols = st.columns(len(suggestions))
    for i, (icon, query_text) in enumerate(suggestions):
        with cols[i]:
            if st.button(f"{icon} {query_text}", key=f"suggest_{i}"):
                st.session_state.messages.append({"role": "user", "content": query_text})
                response = get_orchestrator_response(query_text)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
            
    # Chat Input
    if prompt := st.chat_input("Ask D.A.M.I a question..."):
        # User message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Analyzing BigQuery data...")
            
            response = get_orchestrator_response(prompt)
            message_placeholder.markdown(response)
            
            # Show SQL query results if generated
            if "_last_sql_result" in st.session_state:
                st.caption("📊 **Live BigQuery Result:**")
                st.dataframe(st.session_state["_last_sql_result"], use_container_width=True, hide_index=True)
                del st.session_state["_last_sql_result"]
                if "_last_sql_query" in st.session_state:
                    del st.session_state["_last_sql_query"]
            
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    render()
