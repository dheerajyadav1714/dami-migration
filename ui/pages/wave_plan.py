# wave_plan.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

def get_waves_data(client, project_id, dataset):
    query = f"SELECT * FROM `{project_id}.{dataset}.waves` ORDER BY wave_number"
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        print(f"Failed to query waves: {e}")
        
    # Return mock data
    today = date.today()
    mock_waves = [
        {"wave_id": "wav-0000", "wave_number": 0, "wave_name": "Pilot Wave", "wave_type": "pilot", "estimated_start_date": today.isoformat(), "estimated_end_date": (today + timedelta(days=5)).isoformat(), "estimated_duration_days": 5, "risk_level": "low", "workload_count": 2, "rationale": "Non-critical servers with low complexity to validate landing zone and build team confidence.", "prerequisites": "Landing Zone Ready", "rollback_strategy": "VPC route reversion", "success_criteria": "All traffic cutover", "total_servers": 2, "total_databases": 0},
        {"wave_id": "wav-0001", "wave_number": 1, "wave_name": "Core Web & Frontend Services", "wave_type": "standard", "estimated_start_date": (today + timedelta(days=6)).isoformat(), "estimated_end_date": (today + timedelta(days=14)).isoformat(), "estimated_duration_days": 8, "risk_level": "medium", "workload_count": 3, "rationale": "Migration of web servers and load balancers to establish frontend layer.", "prerequisites": "Wave 0 Success", "rollback_strategy": "Surgical route reversion via Cloud DNS", "success_criteria": "All traffic cutover", "total_servers": 3, "total_databases": 0},
        {"wave_id": "wav-0002", "wave_number": 2, "wave_name": "Middle-Tier Applications", "wave_type": "standard", "estimated_start_date": (today + timedelta(days=15)).isoformat(), "estimated_end_date": (today + timedelta(days=25)).isoformat(), "estimated_duration_days": 10, "risk_level": "medium", "workload_count": 2, "rationale": "Business application servers. Tightly integrated with the frontend.", "prerequisites": "Wave 1 Success", "rollback_strategy": "App rollback to on-prem via backup VPN", "success_criteria": "All traffic cutover", "total_servers": 2, "total_databases": 0},
        {"wave_id": "wav-0003", "wave_number": 3, "wave_name": "Core Databases & Backends", "wave_type": "complex", "estimated_start_date": (today + timedelta(days=26)).isoformat(), "estimated_end_date": (today + timedelta(days=40)).isoformat(), "estimated_duration_days": 14, "risk_level": "high", "workload_count": 2, "rationale": "Migration of payment engines and Oracle DB. Requires data synchronization.", "prerequisites": "Wave 2 Success", "rollback_strategy": "Revert transactions, restore DB snapshot", "success_criteria": "All traffic cutover", "total_servers": 2, "total_databases": 1},
        {"wave_id": "wav-0004", "wave_number": 4, "wave_name": "Complex & Legacy Workloads", "wave_type": "complex", "estimated_start_date": (today + timedelta(days=41)).isoformat(), "estimated_end_date": (today + timedelta(days=50)).isoformat(), "estimated_duration_days": 9, "risk_level": "high", "workload_count": 1, "rationale": "Remaining infrastructure and legacy components.", "prerequisites": "Wave 3 Success", "rollback_strategy": "Cold restore on-prem", "success_criteria": "All traffic cutover", "total_servers": 1, "total_databases": 0}
    ]
    return pd.DataFrame(mock_waves)

def get_all_wave_workloads(client, project_id, dataset):
    query = f"""
        SELECT w.*, s.name as server_name, s.workload_type
        FROM `{project_id}.{dataset}.wave_workloads` w
        JOIN `{project_id}.{dataset}.servers` s ON w.server_id = s.server_id
        ORDER BY w.sequence_in_wave
    """
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        print(f"Failed to query wave workloads: {e}")
        
    # Return mock data
    mock_workloads = [
        {"wave_id": "wav-0000", "sequence_in_wave": 1, "server_name": "DEV-TEST-VM-01", "migration_approach": "rehost", "target_gcp_service": "compute-engine", "target_machine_type": "n2-standard-2", "estimated_hours": 16.0},
        {"wave_id": "wav-0000", "sequence_in_wave": 2, "server_name": "DEV-TEST-VM-02", "migration_approach": "rehost", "target_gcp_service": "compute-engine", "target_machine_type": "n2-standard-2", "estimated_hours": 16.0},
        {"wave_id": "wav-0001", "sequence_in_wave": 1, "server_name": "LB-NGINX-01", "migration_approach": "rehost", "target_gcp_service": "compute-engine", "target_machine_type": "n2-standard-2", "estimated_hours": 16.0},
        {"wave_id": "wav-0001", "sequence_in_wave": 2, "server_name": "WEBAPP-PROD-01", "migration_approach": "rehost", "target_gcp_service": "compute-engine", "target_machine_type": "n2-standard-2", "estimated_hours": 16.0},
        {"wave_id": "wav-0001", "sequence_in_wave": 3, "server_name": "WEBAPP-PROD-02", "migration_approach": "rehost", "target_gcp_service": "compute-engine", "target_machine_type": "n2-standard-2", "estimated_hours": 16.0},
        {"wave_id": "wav-0002", "sequence_in_wave": 1, "server_name": "APP-ORDER-PROD-01", "migration_approach": "rehost", "target_gcp_service": "compute-engine", "target_machine_type": "n2-standard-4", "estimated_hours": 24.0},
        {"wave_id": "wav-0002", "sequence_in_wave": 2, "server_name": "DB-MYSQL-STAGE-01", "migration_approach": "replatform", "target_gcp_service": "cloud-sql", "target_machine_type": "db-n2-standard-2", "estimated_hours": 32.0},
        {"wave_id": "wav-0003", "sequence_in_wave": 1, "server_name": "APP-PAYMENT-PROD-01", "migration_approach": "refactor", "target_gcp_service": "gke", "target_machine_type": "n2-standard-4", "estimated_hours": 120.0},
        {"wave_id": "wav-0003", "sequence_in_wave": 2, "server_name": "DB-ORACLE-PROD-01", "migration_approach": "relocate", "target_gcp_service": "bare-metal-solution", "target_machine_type": "custom-16-64", "estimated_hours": 40.0},
        {"wave_id": "wav-0004", "sequence_in_wave": 1, "server_name": "INFRA-LDAP-01", "migration_approach": "repurchase", "target_gcp_service": "cloud-identity", "target_machine_type": "serverless", "estimated_hours": 24.0}
    ]
    return pd.DataFrame(mock_workloads)

@st.cache_resource
def get_bq_client(project_id):
    return bigquery.Client(project=project_id)

def render():
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    
    st.markdown("<h1 class='gradient-text'>Migration Wave Planning</h1>", unsafe_allow_html=True)
    st.write("Examine the sequenced migration waves scheduled topologically to prevent downtime and dependency breaks.")
    st.write("---")
    
    client = get_bq_client(project_id)
    df_waves = get_waves_data(client, project_id, dataset)
    df_all_workloads = get_all_wave_workloads(client, project_id, dataset)
    
    # Render Gantt Chart using Plotly
    st.subheader("Gantt Timeline Chart")
    
    df_gantt = df_waves.copy()
    # Format for Gantt Chart
    df_gantt["Start"] = pd.to_datetime(df_gantt["estimated_start_date"])
    df_gantt["Finish"] = pd.to_datetime(df_gantt["estimated_end_date"])
    
    fig = px.timeline(
        df_gantt, 
        x_start="Start", 
        x_end="Finish", 
        y="wave_name", 
        color="risk_level",
        color_discrete_map={"high": "#ea4335", "medium": "#fbbc04", "low": "#34a853"},
        title="Scheduled Batches Timeline",
        hover_data=["estimated_duration_days", "workload_count"]
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", 
        paper_bgcolor="rgba(0,0,0,0)", 
        font_color="#e2e8f0"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("---")
    
    # Add a regenerate wave plan button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Wave Detailed Breakdown")
    with col2:
        if st.button("🌊 Regenerate Waves"):
            with st.spinner("Wave Planner sequencing workloads..."):
                from agents.wave_planner import WavePlannerAgent
                planner = WavePlannerAgent()
                try:
                    res = planner.create_migration_waves()
                    st.success(f"Success! Organized into {res['waves_count']} waves.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    
    st.write(" ")
    
    for _, row in df_waves.iterrows():
        w_id = row["wave_id"]
        w_num = row["wave_number"]
        w_name = row["wave_name"]
        
        # Color indicator based on risk
        risk = row["risk_level"].upper()
        risk_color = "status-danger" if risk == "HIGH" else "status-warning" if risk == "MEDIUM" else "status-success"
        
        with st.expander(f"🌊 Wave {w_num}: {w_name} (Risk: {risk})"):
            # Sub-metrics
            mcol1, mcol2, mcol3 = st.columns(3)
            with mcol1:
                st.write(f"**Duration:** {row['estimated_duration_days']} Days")
                st.write(f"**Start Date:** {row['estimated_start_date']}")
            with mcol2:
                st.write(f"**Prerequisites:** {row['prerequisites']}")
                st.write(f"**Success Criteria:** {row['success_criteria']}")
            with mcol3:
                st.write(f"**Rollback Strategy:** {row['rollback_strategy']}")
                
            st.write("**Rational / Target Workloads:**")
            st.write(row["rationale"])
            
            # Filter wave workloads in memory
            if not df_all_workloads.empty:
                w_df = df_all_workloads[df_all_workloads["wave_id"] == w_id]
            else:
                w_df = pd.DataFrame()
                
            if not w_df.empty:
                st.write(" ")
                st.dataframe(
                    w_df[["sequence_in_wave", "server_name", "migration_approach", "target_gcp_service", "target_machine_type", "estimated_hours"]],
                    use_container_width=True
                )
            else:
                st.info("No workloads assigned to this wave yet. Run the Wave Planner agent.")

if __name__ == "__main__":
    render()
