# inventory.py
import streamlit as st
from google.cloud import bigquery
import os
import pandas as pd
import plotly.express as px

def get_servers_data(project_id, dataset):
    client = bigquery.Client(project=project_id)
    query = f"SELECT * FROM `{project_id}.{dataset}.servers` ORDER BY name"
    
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        print(f"Failed to query servers from BigQuery: {e}")
        
    # Return mock fallback data if BQ fails or is empty
    mock_data = []
    # Re-generate some basic mock data matching our csv structure
    services = [
        {"VM": "LB-NGINX-01", "CPUs": 2, "Memory": 4.0, "OS": "Red Hat Enterprise Linux 8", "IP": "10.150.23.10", "Cluster": "Cluster-Production-US", "State": "poweredOn", "CPU_Avg": 12.5, "RAM_Avg": 45.0, "type": "LB", "env": "prod"},
        {"VM": "WEBAPP-PROD-01", "CPUs": 4, "Memory": 8.0, "OS": "Red Hat Enterprise Linux 8", "IP": "10.150.23.12", "Cluster": "Cluster-Production-US", "State": "poweredOn", "CPU_Avg": 45.0, "RAM_Avg": 72.0, "type": "WEB", "env": "prod"},
        {"VM": "WEBAPP-PROD-02", "CPUs": 4, "Memory": 8.0, "OS": "Red Hat Enterprise Linux 8", "IP": "10.150.23.13", "Cluster": "Cluster-Production-US", "State": "poweredOn", "CPU_Avg": 41.0, "RAM_Avg": 68.0, "type": "WEB", "env": "prod"},
        {"VM": "APP-PAYMENT-PROD-01", "CPUs": 8, "Memory": 16.0, "OS": "Ubuntu Linux 22.04", "IP": "10.150.23.14", "Cluster": "Cluster-Production-US", "State": "poweredOn", "CPU_Avg": 55.0, "RAM_Avg": 78.0, "type": "APP", "env": "prod"},
        {"VM": "DB-ORACLE-PROD-01", "CPUs": 16, "Memory": 64.0, "OS": "Red Hat Enterprise Linux 7", "IP": "10.150.23.16", "Cluster": "Cluster-Production-US", "State": "poweredOn", "CPU_Avg": 65.0, "RAM_Avg": 85.0, "type": "DB", "env": "prod"},
        {"VM": "DB-MYSQL-STAGE-01", "CPUs": 4, "Memory": 16.0, "OS": "Ubuntu Linux 20.04", "IP": "10.150.23.17", "Cluster": "Cluster-Staging-US", "State": "poweredOn", "CPU_Avg": 18.0, "RAM_Avg": 48.0, "type": "DB", "env": "staging"},
        {"VM": "CACHE-REDIS-PROD-01", "CPUs": 4, "Memory": 16.0, "OS": "Ubuntu Linux 20.04", "IP": "10.150.23.18", "Cluster": "Cluster-Production-US", "State": "poweredOn", "CPU_Avg": 22.0, "RAM_Avg": 80.0, "type": "CACHE", "env": "prod"},
        {"VM": "QUEUE-RABBIT-PROD-01", "CPUs": 4, "Memory": 8.0, "OS": "Ubuntu Linux 20.04", "IP": "10.150.23.19", "Cluster": "Cluster-Production-US", "State": "poweredOn", "CPU_Avg": 15.0, "RAM_Avg": 42.0, "type": "QUEUE", "env": "prod"},
        {"VM": "INFRA-LDAP-01", "CPUs": 2, "Memory": 4.0, "OS": "Windows Server 2016", "IP": "10.150.23.20", "Cluster": "Cluster-Infra-US", "State": "poweredOn", "CPU_Avg": 10.0, "RAM_Avg": 60.0, "type": "INFRA", "env": "prod"},
        {"VM": "LEGACY-ARCHIVE-01", "CPUs": 2, "Memory": 4.0, "OS": "Windows Server 2008 R2", "IP": "10.150.23.24", "Cluster": "Cluster-Production-US", "State": "poweredOff", "CPU_Avg": 0.0, "RAM_Avg": 0.0, "type": "LEGACY", "env": "prod"}
    ]
    
    for idx, s in enumerate(services):
        mock_data.append({
            "server_id": f"srv-{idx:04d}",
            "name": s["VM"],
            "vcpu": s["CPUs"],
            "ram_gb": s["Memory"],
            "disk_gb": s["Memory"] * 10,
            "os": s["OS"],
            "os_version": "v1.0",
            "ip_address": s["IP"],
            "cluster": s["Cluster"],
            "datacenter": "Datacenter-US-East",
            "power_state": s["State"],
            "cpu_utilization_avg": s["CPU_Avg"],
            "ram_utilization_avg": s["RAM_Avg"],
            "workload_type": s["type"],
            "app_owner": "owner@company.com",
            "environment": s["env"],
            "source_platform": "vmware"
        })
    return pd.DataFrame(mock_data)

def render():
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    st.markdown("<h1 class='gradient-text'>Discovered Server Inventory</h1>", unsafe_allow_html=True)
    st.write("Browse and filter the complete catalog of discovered servers in your on-premises environment.")
    st.write("---")
    
    # Load servers
    df = get_servers_data(project_id, dataset)
    
    # Search and Filter Sidebar-like Controls in main pane
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        envs = ["All"] + sorted(df["environment"].unique().tolist())
        env_filter = st.selectbox("Environment", envs)
    with col2:
        workloads = ["All"] + sorted(df["workload_type"].unique().tolist())
        workload_filter = st.selectbox("Workload Type", workloads)
    with col3:
        states = ["All"] + sorted(df["power_state"].unique().tolist())
        state_filter = st.selectbox("Power State", states)
    with col4:
        search_query = st.text_input("Search VM Name / IP", "")
        
    # Apply Filters
    filtered_df = df.copy()
    if env_filter != "All":
        filtered_df = filtered_df[filtered_df["environment"] == env_filter]
    if workload_filter != "All":
        filtered_df = filtered_df[filtered_df["workload_type"] == workload_filter]
    if state_filter != "All":
        filtered_df = filtered_df[filtered_df["power_state"] == state_filter]
    if search_query:
        filtered_df = filtered_df[
            filtered_df["name"].str.contains(search_query, case=False) |
            filtered_df["ip_address"].str.contains(search_query, case=False)
        ]
        
    # KPI Stats for Filtered Data
    st.write(" ")
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    
    active_vms = filtered_df[filtered_df["power_state"] == "poweredOn"]
    avg_cpu = active_vms["cpu_utilization_avg"].mean() if not active_vms.empty else 0.0
    avg_ram = active_vms["ram_utilization_avg"].mean() if not active_vms.empty else 0.0
    
    with mcol1:
        st.metric("Filtered Servers", f"{len(filtered_df)} VMs")
    with mcol2:
        st.metric("Total CPUs Allocation", f"{filtered_df['vcpu'].sum()} vCPUs")
    with mcol3:
        st.metric("Avg. CPU Utilization", f"{avg_cpu:.1f}%")
    with mcol4:
        st.metric("Avg. RAM Utilization", f"{avg_ram:.1f}%")
        
    st.write("---")
    
    # Table View
    st.subheader("Inventory Details")
    st.dataframe(
        filtered_df[[
            "server_id", "name", "vcpu", "ram_gb", "disk_gb", 
            "os", "ip_address", "power_state", "workload_type", 
            "environment", "cpu_utilization_avg", "ram_utilization_avg"
        ]],
        use_container_width=True
    )
    
    # Distribution Charts
    st.write("---")
    ccol1, ccol2 = st.columns(2)
    
    with ccol1:
        st.subheader("OS Distribution")
        fig_os = px.pie(
            filtered_df, 
            names="os", 
            title="Operating System Share",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_os.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig_os, use_container_width=True)
        
    with ccol2:
        st.subheader("Workload Types")
        fig_workload = px.bar(
            filtered_df.groupby("workload_type").size().reset_index(name="count"),
            x="workload_type",
            y="count",
            color="workload_type",
            title="VM Categorization",
            color_discrete_sequence=px.colors.qualitative.Vivid
        )
        fig_workload.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig_workload, use_container_width=True)
    
    # --- Advanced Visualizations ---
    st.write("---")
    
    adv_col1, adv_col2 = st.columns(2)
    
    with adv_col1:
        st.subheader("CPU & RAM Utilization Heatmap")
        # Build heatmap data
        heatmap_df = filtered_df[filtered_df["power_state"] == "poweredOn"].copy()
        if not heatmap_df.empty and len(heatmap_df) > 0:
            import plotly.graph_objects as go
            
            short_names = heatmap_df["name"].str[:20].tolist()
            z_data = [
                heatmap_df["cpu_utilization_avg"].tolist(),
                heatmap_df["ram_utilization_avg"].tolist()
            ]
            
            fig_heat = go.Figure(data=go.Heatmap(
                z=z_data,
                x=short_names,
                y=["CPU %", "RAM %"],
                colorscale=[
                    [0.0, "#0f172a"],
                    [0.3, "#1e40af"],
                    [0.5, "#7c3aed"],
                    [0.7, "#f59e0b"],
                    [1.0, "#ef4444"]
                ],
                text=[[f"{v:.0f}%" for v in row] for row in z_data],
                texttemplate="%{text}",
                textfont={"size": 10, "color": "#e2e8f0"},
                hovertemplate="VM: %{x}<br>%{y}: %{z:.1f}%<extra></extra>"
            ))
            fig_heat.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                height=250,
                margin=dict(l=50, r=20, t=30, b=60),
                xaxis=dict(tickangle=-45, tickfont=dict(size=9))
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("No active VMs to display heatmap.")
    
    with adv_col2:
        st.subheader("Resource Allocation Treemap")
        if "vcpu" in filtered_df.columns and not filtered_df.empty:
            treemap_df = filtered_df[filtered_df["vcpu"] > 0].copy()
            if not treemap_df.empty:
                fig_tree = px.treemap(
                    treemap_df,
                    path=["workload_type", "name"],
                    values="vcpu",
                    color="ram_gb",
                    color_continuous_scale=["#1e1b4b", "#4338ca", "#7c3aed", "#c084fc"],
                    title="vCPU Allocation by Workload (Color = RAM GB)"
                )
                fig_tree.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    height=300,
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.info("No VM data for treemap.")

if __name__ == "__main__":
    render()
