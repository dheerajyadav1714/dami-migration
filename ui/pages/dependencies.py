# dependencies.py
import streamlit as st
import streamlit.components.v1 as components
from google.cloud import bigquery
import os
import pandas as pd
import graphviz
import plotly.graph_objects as go

def get_dependencies_data(project_id, dataset):
    client = bigquery.Client(project=project_id)
    query = f"SELECT * FROM `{project_id}.{dataset}.app_dependencies`"
    
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        print(f"Failed to query dependencies: {e}")
        
    # Return mock data
    mock_deps = [
        {"source_app_id": "app-0001", "target_app_id": "app-0004", "protocol": "LDAP", "port": 389, "traffic_volume": "medium"},
        {"source_app_id": "app-0002", "target_app_id": "app-0004", "protocol": "LDAP", "port": 389, "traffic_volume": "medium"},
        {"source_app_id": "app-0003", "target_app_id": "app-0004", "protocol": "LDAP", "port": 389, "traffic_volume": "low"},
        {"source_app_id": "app-0001", "target_app_id": "app-0002", "protocol": "HTTPS", "port": 443, "traffic_volume": "high"},
        {"source_app_id": "app-0002", "target_app_id": "app-0001", "protocol": "HTTP", "port": 8080, "traffic_volume": "high"} # Circular dep
    ]
    return pd.DataFrame(mock_deps)

def get_apps_list(project_id, dataset):
    client = bigquery.Client(project=project_id)
    try:
        df = client.query(f"SELECT app_id, name, tier FROM `{project_id}.{dataset}.applications`").to_dataframe()
        if not df.empty:
            return df
    except Exception:
        pass
        
    return pd.DataFrame([
        {"app_id": "app-0001", "name": "payment-gateway", "tier": "web"},
        {"app_id": "app-0002", "name": "order-processing", "tier": "app"},
        {"app_id": "app-0003", "name": "inventory-management", "tier": "app"},
        {"app_id": "app-0004", "name": "shared-infrastructure", "tier": "middleware"}
    ])

def render():
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    
    st.markdown("<h1 class='gradient-text'>Workload Dependency Map</h1>", unsafe_allow_html=True)
    st.write("Visualize directed dependencies and communication flows between applications and shared services.")
    st.write("---")
    
    # Load data
    deps_df = get_dependencies_data(project_id, dataset)
    apps_df = get_apps_list(project_id, dataset)
    
    # Analyze in Python
    from agents.dependency_mapper import DependencyMapperAgent
    agent = DependencyMapperAgent()
    
    # Construct NetworkX Graph for analytics
    import networkx as nx
    G = nx.DiGraph()
    
    # Add nodes
    app_names = {}
    app_tiers = {}
    for _, row in apps_df.iterrows():
        app_names[row["app_id"]] = row["name"]
        app_tiers[row["app_id"]] = row.get("tier", "app")
        G.add_node(row["app_id"], name=row["name"], tier=row.get("tier", "app"))
        
    # Add edges
    for _, row in deps_df.iterrows():
        src = row["source_app_id"]
        dst = row["target_app_id"]
        if src in app_names and dst in app_names:
            G.add_edge(src, dst, relation="depends_on", protocol=row["protocol"], port=row["port"])
            
    # Run analysis
    analysis = agent.analyze_dependencies(G)
    
    # Identify circular dependency edges
    try:
        cycles = list(nx.simple_cycles(G))
    except Exception:
        cycles = []
        
    cycle_edges = set()
    for cycle in cycles:
        for i in range(len(cycle)):
            cycle_edges.add((cycle[i], cycle[(i + 1) % len(cycle)]))
    
    # Left / Right Column split
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        st.subheader("Application Dependency Graph")
        
        graph_tab1, graph_tab2 = st.tabs(["🌐 Interactive Graph", "📊 Static Diagram"])
        
        with graph_tab1:
            # --- Interactive pyvis Graph ---
            from pyvis.network import Network
            import tempfile
            
            net = Network(
                height="500px", width="100%", 
                bgcolor="#0f0f1a", font_color="#e2e8f0",
                directed=True, select_menu=False, filter_menu=False
            )
            net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=150, spring_strength=0.05)
            
            tier_colors = {
                "web": "#6366f1", "app": "#8b5cf6", "db": "#22d3ee",
                "middleware": "#f59e0b", "cache": "#10b981", "queue": "#ec4899"
            }
            tier_shapes = {
                "web": "diamond", "app": "dot", "db": "database",
                "middleware": "triangle", "cache": "star", "queue": "square"
            }
            
            for node_id, data in G.nodes(data=True):
                tier = data.get("tier", "app")
                name = data.get("name", node_id)
                color = tier_colors.get(tier, "#6366f1")
                shape = tier_shapes.get(tier, "dot")
                in_deg = G.in_degree(node_id)
                size = 25 + in_deg * 8
                
                net.add_node(
                    node_id,
                    label=name,
                    title=f"<b>{name}</b><br>ID: {node_id}<br>Tier: {tier.upper()}<br>Connections: {G.degree(node_id)}",
                    color={"background": color, "border": color, "highlight": {"background": "#22d3ee", "border": "#22d3ee"}},
                    shape=shape,
                    size=size,
                    font={"size": 12, "color": "#e2e8f0"},
                    borderWidth=2
                )
            
            for u, v, data in G.edges(data=True):
                proto = data.get("protocol", "TCP")
                port = data.get("port", "80")
                is_circular = (u, v) in cycle_edges
                
                net.add_edge(
                    u, v,
                    title=f"{proto}:{port}",
                    label=f"{proto}:{port}",
                    color="#ef4444" if is_circular else "#4b556366",
                    width=3 if is_circular else 1.5,
                    dashes=is_circular,
                    arrows={"to": {"enabled": True, "scaleFactor": 0.8}},
                    font={"size": 9, "color": "#94a3b8", "strokeWidth": 0}
                )
            
            # Save to temp file and embed
            try:
                tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ui", "_temp")
                os.makedirs(tmp_dir, exist_ok=True)
                graph_path = os.path.join(tmp_dir, "dep_graph.html")
                net.save_graph(graph_path)
                
                with open(graph_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                components.html(html_content, height=520, scrolling=False)
            except Exception as e:
                st.error(f"Interactive graph rendering failed: {e}")
            
            # Legend
            st.markdown("""
            <div style="display:flex; gap:12px; flex-wrap:wrap; margin-top:8px; font-size:0.75rem;">
                <span style="color:#6366f1;">◆ Web</span>
                <span style="color:#8b5cf6;">● App</span>
                <span style="color:#f59e0b;">▲ Middleware</span>
                <span style="color:#22d3ee;">⬡ Database</span>
                <span style="color:#ef4444;">--- Circular Dep</span>
            </div>
            """, unsafe_allow_html=True)
        
        with graph_tab2:
            # --- Graphviz Static Diagram ---
            gv_tier_colors = {
                "web": "#6366f1", "app": "#8b5cf6", "db": "#22d3ee",
                "middleware": "#f59e0b", "cache": "#10b981", "queue": "#ec4899"
            }
            gv_tier_shapes = {
                "web": "hexagon", "app": "box", "db": "cylinder",
                "middleware": "diamond", "cache": "ellipse", "queue": "parallelogram"
            }
            
            dot = graphviz.Digraph(
                "dependency_map", format="svg",
                graph_attr={"rankdir": "TB", "bgcolor": "#0f0f1a", "fontcolor": "#e2e8f0", "pad": "0.5", "nodesep": "0.8", "ranksep": "1.0", "splines": "ortho", "label": ""},
                node_attr={"style": "filled,rounded", "fontname": "Inter, Helvetica, Arial", "fontsize": "11", "fontcolor": "#ffffff", "penwidth": "1.5", "margin": "0.2,0.1"},
                edge_attr={"fontname": "Inter, Helvetica, Arial", "fontsize": "9", "fontcolor": "#94a3b8", "penwidth": "1.5"}
            )
            
            for node_id, data in G.nodes(data=True):
                tier = data.get("tier", "app")
                name = data.get("name", node_id)
                color = gv_tier_colors.get(tier, "#6366f1")
                shape = gv_tier_shapes.get(tier, "box")
                width = str(max(1.8, 1.2 + G.in_degree(node_id) * 0.3))
                dot.node(node_id, label=f"<<B>{name}</B><BR/><FONT POINT-SIZE='8' COLOR='#cbd5e1'>{tier.upper()}</FONT>>", fillcolor=color, color=color, shape=shape, width=width)
            
            for u, v, data in G.edges(data=True):
                proto = data.get("protocol", "TCP")
                port = data.get("port", "80")
                if (u, v) in cycle_edges:
                    dot.edge(u, v, label=f" {proto}:{port} ", color="#ef4444", style="dashed", penwidth="2.5", fontcolor="#ef4444", arrowhead="vee", arrowsize="1.2")
                else:
                    dot.edge(u, v, label=f" {proto}:{port} ", color="#4b5563", arrowhead="normal")
            
            st.graphviz_chart(dot, use_container_width=True)
        
        # Circular dependency alert
        if cycle_edges:
            st.markdown(f"""
            <div style="
                background: rgba(239, 68, 68, 0.08);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 8px;
                padding: 10px 14px;
                margin-top: 8px;
                font-size: 0.85rem;
                color: #fca5a5;
            ">
                <b style="color: #ef4444;">Warning:</b> Red dashed edges indicate circular dependency loops.
                These must be resolved before migration wave sequencing.
            </div>
            """, unsafe_allow_html=True)
                
    with right_col:
        st.subheader("Dependency Analytics")
        
        # Summary metrics
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Total Services", G.number_of_nodes())
        with m2:
            st.metric("Total Connections", G.number_of_edges())
        
        st.write("")
        
        # 1. Circular Dependencies (critical migration blockers)
        st.markdown("**1. Circular Dependencies Detected:**")
        cycles_count = analysis["circular_dependencies_count"]
        if cycles_count > 0:
            st.markdown(f"<span class='status-badge status-danger'>Critical Blocker</span> {cycles_count} loop(s) detected:", unsafe_allow_html=True)
            for idx, cycle in enumerate(analysis["cycles"]):
                cycle_str = " -> ".join([node["name"] for node in cycle]) + f" -> {cycle[0]['name']}"
                st.error(f"Loop {idx+1}: {cycle_str}")
        else:
            st.markdown("<span class='status-badge status-success'>Clear</span> No circular dependencies.", unsafe_allow_html=True)
            
        st.write(" ")
        
        # 2. Shared Infrastructure Services
        st.markdown("**2. Shared Infrastructure Services:**")
        shared = analysis["shared_services"]
        if shared:
            for s in shared:
                st.info(f"**{s['name']}** ({(s.get('type') or 'unknown').upper()}) - referenced by {s.get('in_degree', 0)} workloads.")
        else:
            st.write("None detected.")
            
        st.write(" ")
        
        # 3. Blockers
        st.markdown("**3. Sequence Blockers:**")
        blockers = analysis["blockers"]
        if blockers:
            for b in blockers:
                st.warning(f"**{b['name']}** - blocks {b['out_degree']} downstream workloads.")
        else:
            st.write("None.")
            
        st.write(" ")
        
        # 4. Orphans
        st.markdown("**4. Orphaned Services (Retire Candidates):**")
        orphans = analysis["orphans"]
        if orphans:
            for o in orphans:
                st.success(f"**{o['name']}** - 0 active connections. (Recommend: Retire)")
        else:
            st.write("None.")

    # --- Connection Details Table ---
    st.write("---")
    st.subheader("Connection Details")
    
    conn_data = []
    for _, row in deps_df.iterrows():
        src = row["source_app_id"]
        dst = row["target_app_id"]
        is_loop = (src, dst) in cycle_edges
        conn_data.append({
            "Source": app_names.get(src, src),
            "Target": app_names.get(dst, dst),
            "Protocol": row["protocol"],
            "Port": row["port"],
            "Volume": row.get("traffic_volume", "—"),
            "Circular Loop": "YES" if is_loop else "no"
        })
    
    if conn_data:
        st.dataframe(
            pd.DataFrame(conn_data),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Source": st.column_config.TextColumn("Source Service", width="medium"),
                "Target": st.column_config.TextColumn("Target Service", width="medium"),
                "Protocol": st.column_config.TextColumn("Protocol", width="small"),
                "Port": st.column_config.NumberColumn("Port", width="small"),
                "Volume": st.column_config.TextColumn("Traffic", width="small"),
                "Circular Loop": st.column_config.TextColumn("Loop?", width="small"),
            }
        )

if __name__ == "__main__":
    render()
