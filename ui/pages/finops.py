# finops.py
import streamlit as st
from google.cloud import bigquery
import os
import pandas as pd
import plotly.express as px

@st.cache_resource
def get_bq_client(project_id):
    return bigquery.Client(project=project_id)

def fetch_finops_data(client, project_id, dataset):
    try:
        # Query on-premises source specs
        servers_query = f"""
            SELECT vcpu, ram_gb, disk_gb 
            FROM `{project_id}.{dataset}.servers`
        """
        servers_df = client.query(servers_query).to_dataframe()
        
        # Query target architecture costs
        target_query = f"""
            SELECT target_gcp_service, estimated_monthly_cost 
            FROM `{project_id}.{dataset}.target_architecture`
        """
        target_df = client.query(target_query).to_dataframe()
        
        if servers_df.empty or target_df.empty:
            return None, None
            
        return servers_df, target_df
    except Exception as e:
        print(f"Failed to fetch FinOps data from BigQuery: {e}")
        return None, None

def render():
    st.markdown("<h1 class='gradient-text'>FinOps TCO & Cost Optimization</h1>", unsafe_allow_html=True)
    st.write("Compare the Total Cost of Ownership (TCO) of the current on-premises data center deployment against the optimized, right-sized Google Cloud target state.")
    
    # What-If Simulator configuration sliders in Sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("💰 TCO What-If Simulator")
    st.sidebar.caption("Fine-tune rightsizing parameters to balance performance buffers against cost savings.")
    
    oversubscription = st.sidebar.slider(
        "CPU Oversubscription Ratio",
        min_value=1.0,
        max_value=4.0,
        value=2.0,
        step=0.5,
        help="Ratio of virtual CPUs mapped to a physical host core. Higher ratios increase savings for non-production workloads."
    )
    
    headroom = st.sidebar.slider(
        "Performance Safety Headroom (%)",
        min_value=10,
        max_value=50,
        value=20,
        step=5,
        help="Safety buffer added to average resource utilization to handle seasonal load spikes."
    )
    
    st.write("---")
    
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    client = get_bq_client(project_id)
    
    servers_df, target_df = fetch_finops_data(client, project_id, dataset)
    
    if servers_df is not None and not servers_df.empty and target_df is not None and not target_df.empty:
        # Calculate dynamic on-prem TCO
        # Baseline: $35/vCPU, $3.50/GB RAM, $0.12/GB Disk, plus $60/server hosting overhead
        total_vcpus = servers_df["vcpu"].sum()
        total_ram = servers_df["ram_gb"].sum()
        total_disk = servers_df["disk_gb"].sum()
        total_servers = len(servers_df)
        
        on_prem_cost = (total_vcpus * 35.0) + (total_ram * 3.50) + (total_disk * 0.12) + (total_servers * 60.0)
        
        # Calculate dynamic GCP target cost with oversubscription and headroom scaling
        base_gcp_cost = target_df["estimated_monthly_cost"].sum()
        
        # Scale based on What-If parameters (normalized to base settings of 2.0 oversubscription and 20% headroom)
        vcpu_savings_multiplier = 2.0 / oversubscription
        headroom_multiplier = (100.0 + headroom) / 120.0
        
        optimized_gcp_cost = base_gcp_cost * vcpu_savings_multiplier * headroom_multiplier
        lift_and_shift_cost = base_gcp_cost * 1.55 * headroom_multiplier
        
        annual_savings = (on_prem_cost - optimized_gcp_cost) * 12
        savings_percentage = ((on_prem_cost - optimized_gcp_cost) / on_prem_cost) * 100
        
        # Prepare service breakdown data
        service_mapping = {
            "compute-engine": "Compute Engine (VMs)",
            "gke": "Google Kubernetes Engine (GKE)",
            "cloud-sql": "Cloud SQL (Managed DB)",
            "alloydb": "AlloyDB for PostgreSQL",
            "memorystore": "Cloud Memorystore",
            "bare-metal-solution": "Bare Metal Solution (Oracle)",
            "cloud-pubsub": "Cloud Pub/Sub",
            "gcs": "Google Cloud Storage"
        }
        
        breakdown_df = target_df.groupby("target_gcp_service")["estimated_monthly_cost"].sum().reset_index()
        breakdown_df["Resource Type"] = breakdown_df["target_gcp_service"].map(lambda x: service_mapping.get(x, f"GCP Service: {x}"))
        breakdown_df["Estimated Cost ($)"] = breakdown_df["estimated_monthly_cost"] * vcpu_savings_multiplier * headroom_multiplier
        
    else:
        # Fallback to standard mock metrics if tables are empty/missing
        on_prem_cost = 175000.0
        base_gcp_cost = 74160.0
        
        vcpu_savings_multiplier = 2.0 / oversubscription
        headroom_multiplier = (100.0 + headroom) / 120.0
        
        optimized_gcp_cost = base_gcp_cost * vcpu_savings_multiplier * headroom_multiplier
        lift_and_shift_cost = base_gcp_cost * 1.55 * headroom_multiplier
        annual_savings = (on_prem_cost - optimized_gcp_cost) * 12
        savings_percentage = ((on_prem_cost - optimized_gcp_cost) / on_prem_cost) * 100
        
        breakdown_df = pd.DataFrame({
            "Resource Type": ["Compute Engine (VMs)", "GKE (Autopilot)", "Cloud SQL (Managed DB)", "Bare Metal Solution (Oracle)", "Storage & Networking", "Operations"],
            "Estimated Cost ($)": [
                12800 * vcpu_savings_multiplier * headroom_multiplier,
                18500 * vcpu_savings_multiplier * headroom_multiplier,
                7800 * vcpu_savings_multiplier * headroom_multiplier,
                24000 * vcpu_savings_multiplier * headroom_multiplier,
                6800 * vcpu_savings_multiplier * headroom_multiplier,
                4260 * vcpu_savings_multiplier * headroom_multiplier
            ]
        })
        
    # KPI metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current On-Prem Cost", f"${on_prem_cost:,.2f} / mo", delta="Depreciation + Ops")
    with col2:
        st.metric("Optimized Target Cost", f"${optimized_gcp_cost:,.2f} / mo", delta=f"-{savings_percentage:.1f}% Cost Reduction", delta_color="inverse")
    with col3:
        st.metric("Projected Annual Savings", f"${annual_savings:,.2f} / yr", delta="Reinvestable Capital")
        
    st.write("---")
    
    # Visual Chart split
    ccol1, ccol2 = st.columns(2)
    
    with ccol1:
        st.subheader("Monthly Cost Comparison")
        df_cost = pd.DataFrame({
            "Platform": ["On-Premises", "Target (Lift & Shift)", "Target (Optimized)"],
            "Monthly Cost ($)": [on_prem_cost, lift_and_shift_cost, optimized_gcp_cost],
            "Type": ["Current", "Lift & Shift", "D.A.M.I. Optimized"]
        })
        fig = px.bar(
            df_cost, 
            x="Platform", 
            y="Monthly Cost ($)", 
            color="Type",
            color_discrete_map={"Current": "#ea4335", "Lift & Shift": "#fbbc04", "D.A.M.I. Optimized": "#34a853"},
            title="TCO Optimization Tiers"
        )
        fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig, use_container_width=True)
        
    with ccol2:
        st.subheader("Monthly Cost Breakdown")
        fig_pie = px.pie(
            breakdown_df, 
            values="Estimated Cost ($)", 
            names="Resource Type",
            title="Target Budget Allocation Share",
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_pie.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    st.write("---")
    
    # Optimization Drivers List
    st.subheader("💸 D.A.M.I. Cost Optimization Drivers")
    st.write("Our FinOps Agent identifies savings using the following Google Cloud capabilities:")
    
    st.markdown("""
    - **1. Committed Use Discounts (CUDs):** Recommending 3-year resource commitments for stable VMs (saves up to 57% on compute).
    - **2. Core Rightsizing:** Converting idle and over-provisioned source cores (on-prem VMs are typically allocated 8 cores but run at 5% load).
    - **3. Serverless Storage:** Moving backup archives and cold data from expensive SAN arrays to Google Cloud Storage Archive/Coldline classes ($0.0012 per GB/mo).
    - **4. DB Licensing Optimization:** Consolidating databases and migrating MySQL instances onto Cloud SQL managed engines (reduces software licensing overhead).
    """)
    
    # ── What-If Scenario Simulator ──
    st.write("---")
    st.subheader("🔮 What-If Scenario Simulator")
    st.write("Compare different migration strategies side-by-side to find the optimal cost/performance balance.")
    
    sim_tab1, sim_tab2 = st.tabs(["📐 Service Swap Analysis", "📅 Timeline Impact"])
    
    with sim_tab1:
        st.caption("Change target GCP services and see cost impact instantly.")
        
        sim_col1, sim_col2, sim_col3 = st.columns(3)
        with sim_col1:
            db_choice = st.selectbox("Database Strategy", ["Cloud SQL (Standard)", "AlloyDB (High-Perf)", "Bare Metal (Oracle BYOL)", "Spanner (Global)"], index=0)
        with sim_col2:
            compute_choice = st.selectbox("Compute Strategy", ["Compute Engine VMs", "GKE Autopilot", "Cloud Run (Serverless)", "Mix (VMs + GKE)"], index=0)
        with sim_col3:
            commitment = st.selectbox("Commitment Level", ["On-Demand (No Discount)", "1-Year CUD (-37%)", "3-Year CUD (-57%)"], index=1)
        
        # Cost multipliers
        db_costs = {"Cloud SQL (Standard)": 1.0, "AlloyDB (High-Perf)": 1.35, "Bare Metal (Oracle BYOL)": 2.1, "Spanner (Global)": 1.85}
        compute_costs = {"Compute Engine VMs": 1.0, "GKE Autopilot": 0.85, "Cloud Run (Serverless)": 0.6, "Mix (VMs + GKE)": 0.9}
        commit_discounts = {"On-Demand (No Discount)": 1.0, "1-Year CUD (-37%)": 0.63, "3-Year CUD (-57%)": 0.43}
        
        db_mult = db_costs[db_choice]
        compute_mult = compute_costs[compute_choice]
        commit_mult = commit_discounts[commitment]
        
        # Scenario calculations
        base_monthly = optimized_gcp_cost
        scenario_db_cost = base_monthly * 0.35 * db_mult  # 35% is DB portion
        scenario_compute_cost = base_monthly * 0.45 * compute_mult * commit_mult  # 45% is compute
        scenario_other = base_monthly * 0.20  # 20% is storage/network
        scenario_total = scenario_db_cost + scenario_compute_cost + scenario_other
        
        scenario_savings = on_prem_cost - scenario_total
        scenario_pct = (scenario_savings / on_prem_cost) * 100
        
        # Display comparison
        st.write("")
        comp_col1, comp_col2, comp_col3, comp_col4 = st.columns(4)
        with comp_col1:
            st.metric("Scenario Monthly", f"${scenario_total:,.0f}", delta=f"vs ${optimized_gcp_cost:,.0f} baseline")
        with comp_col2:
            diff = optimized_gcp_cost - scenario_total
            st.metric("Scenario Delta", f"${diff:+,.0f}/mo", delta="Savings" if diff > 0 else "Additional cost", delta_color="inverse" if diff > 0 else "normal")
        with comp_col3:
            st.metric("Annual Savings", f"${scenario_savings*12:,.0f}", delta=f"{scenario_pct:.1f}% reduction")
        with comp_col4:
            roi_years = (50000) / max(scenario_savings * 12, 1)  # Migration investment / annual savings
            st.metric("Migration ROI", f"{roi_years:.1f} months", delta="Payback period")
        
        # Side-by-side bar chart
        import plotly.graph_objects as go_sim
        fig_sim = go_sim.Figure()
        categories = ["Database", "Compute", "Storage/Network"]
        baseline_vals = [base_monthly * 0.35, base_monthly * 0.45, base_monthly * 0.20]
        scenario_vals = [scenario_db_cost, scenario_compute_cost, scenario_other]
        
        fig_sim.add_trace(go_sim.Bar(name="Baseline", x=categories, y=baseline_vals, marker_color="#6366f1"))
        fig_sim.add_trace(go_sim.Bar(name="Your Scenario", x=categories, y=scenario_vals, marker_color="#10b981"))
        fig_sim.update_layout(
            barmode="group",
            title="Cost Component Comparison: Baseline vs Scenario",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
            height=350, margin=dict(l=0, r=0, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_sim, use_container_width=True)
    
    with sim_tab2:
        st.caption("Adjust wave timing and see how it affects project duration and parallel migration costs.")
        
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            wave_delay = st.slider("Delay Between Waves (weeks)", min_value=1, max_value=6, value=2, help="Time gap between consecutive migration waves")
        with t_col2:
            parallel_waves = st.slider("Parallel Wave Execution", min_value=1, max_value=3, value=1, help="Number of waves running simultaneously")
        
        total_waves = stats.get("total_waves", 5) if 'stats' in dir() else 5
        base_duration = total_waves * 2  # 2 weeks per wave baseline
        scenario_duration = max(2, (total_waves * wave_delay) / parallel_waves)
        
        migration_labor_weekly = 15000  # Migration team cost per week
        base_labor = base_duration * migration_labor_weekly
        scenario_labor = scenario_duration * migration_labor_weekly
        
        # Dual cost during migration (running both on-prem + cloud)
        dual_run_weekly = on_prem_cost * 0.25  # Weekly on-prem cost during migration
        base_dual = base_duration * dual_run_weekly
        scenario_dual = scenario_duration * dual_run_weekly
        
        tl_col1, tl_col2, tl_col3 = st.columns(3)
        with tl_col1:
            st.metric("Project Duration", f"{scenario_duration:.0f} weeks", delta=f"vs {base_duration} weeks baseline")
        with tl_col2:
            st.metric("Migration Labor Cost", f"${scenario_labor:,.0f}", delta=f"${scenario_labor - base_labor:+,.0f}")
        with tl_col3:
            st.metric("Dual-Run Overhead", f"${scenario_dual:,.0f}", delta=f"${scenario_dual - base_dual:+,.0f}")
        
        # Timeline visualization
        import plotly.graph_objects as go_tl
        fig_tl = go_tl.Figure()
        for i in range(total_waves):
            start_week = (i * wave_delay) / parallel_waves
            end_week = start_week + 2  # Each wave takes 2 weeks
            fig_tl.add_trace(go_tl.Bar(
                y=[f"Wave {i}"], x=[end_week - start_week], base=[start_week],
                orientation="h", name=f"Wave {i}",
                marker_color=["#ef4444", "#f59e0b", "#6366f1", "#10b981", "#22d3ee"][i % 5],
                hovertext=f"Wave {i}: Week {start_week:.0f}-{end_week:.0f}",
                showlegend=False
            ))
        fig_tl.update_layout(
            title=f"Migration Timeline ({scenario_duration:.0f} weeks total)",
            xaxis_title="Weeks", barmode="stack",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="#e2e8f0",
            height=250, margin=dict(l=10, r=10, t=40, b=30)
        )
        st.plotly_chart(fig_tl, use_container_width=True)

if __name__ == "__main__":
    render()
