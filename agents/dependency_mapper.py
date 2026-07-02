# dependency_mapper.py
import os
from google.cloud import bigquery
import networkx as nx
from dotenv import load_dotenv

load_dotenv()

class DependencyMapperAgent:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
        
    def build_graph(self) -> nx.DiGraph:
        """
        Retrieves all servers, applications, databases, and dependencies from BigQuery 
        and constructs a NetworkX directed graph representation.
        """
        print("Dependency Mapper querying BigQuery for graph data...")
        client = bigquery.Client(project=self.project_id)
        
        # 1. Fetch servers
        servers_query = f"SELECT server_id, name, ip_address, workload_type, environment FROM `{self.project_id}.{self.dataset}.servers`"
        servers_df = client.query(servers_query).to_dataframe()
        
        # 2. Fetch applications
        apps_query = f"SELECT app_id, name, tier, server_ids FROM `{self.project_id}.{self.dataset}.applications`"
        apps_df = client.query(apps_query).to_dataframe()
        
        # 3. Fetch app-to-app dependencies
        deps_query = f"SELECT source_app_id, target_app_id, protocol, port, traffic_volume FROM `{self.project_id}.{self.dataset}.app_dependencies`"
        deps_df = client.query(deps_query).to_dataframe()
        
        # 4. Fetch app-to-db dependencies
        app_db_query = f"SELECT app_id, db_id FROM `{self.project_id}.{self.dataset}.app_db_dependencies`"
        app_db_df = client.query(app_db_query).to_dataframe()
        
        # 5. Fetch databases mapped to servers
        dbs_query = f"SELECT db_id, name, db_engine, server_id FROM `{self.project_id}.{self.dataset}.databases`"
        dbs_df = client.query(dbs_query).to_dataframe()
        
        G = nx.DiGraph()
        
        # Add servers as nodes
        for _, row in servers_df.iterrows():
            G.add_node(
                row["server_id"],
                name=row["name"],
                type="server",
                workload_type=row["workload_type"],
                ip=row["ip_address"],
                environment=row["environment"]
            )
            
        # Add applications as nodes
        for _, row in apps_df.iterrows():
            G.add_node(
                row["app_id"],
                name=row["name"],
                type="application",
                tier=row["tier"]
            )
            
            # Link servers to their application (membership edges)
            server_list = row["server_ids"]
            if server_list is not None:
                for srv_id in server_list:
                    # Only add link if server node exists
                    if G.has_node(srv_id):
                        G.add_edge(srv_id, row["app_id"], relation="member_of")
                        
        # Add databases as nodes and link to their host servers
        for _, row in dbs_df.iterrows():
            db_node_id = row["db_id"]
            G.add_node(
                db_node_id,
                name=row["name"],
                type="database",
                engine=row["db_engine"]
            )
            srv_id = row["server_id"]
            if G.has_node(srv_id):
                G.add_edge(db_node_id, srv_id, relation="hosted_on")
                
        # Add app-to-app dependencies as edges
        for _, row in deps_df.iterrows():
            src = row["source_app_id"]
            dst = row["target_app_id"]
            if G.has_node(src) and G.has_node(dst):
                G.add_edge(
                    src, dst,
                    relation="depends_on",
                    protocol=row["protocol"],
                    port=row["port"],
                    volume=row["traffic_volume"]
                )
                
        # Add app-to-db dependencies as edges
        for _, row in app_db_df.iterrows():
            src = row["app_id"]
            dst = row["db_id"]
            if G.has_node(src) and G.has_node(dst):
                G.add_edge(src, dst, relation="queries_db")
                
        print(f"Constructed migration dependency graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
        return G

    def analyze_dependencies(self, G: nx.DiGraph) -> dict:
        """
        Analyzes the networkx graph to identify circular dependencies, 
        shared services (high in-degree), and potential migration blockers.
        """
        print("Analyzing dependency graph metrics...")
        
        # 1. Detect circular dependencies (excluding membership edges)
        # Create a subgraph of just operational dependencies
        dep_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("relation") in ["depends_on", "queries_db"]]
        dep_graph = G.edge_subgraph(dep_edges).copy()
        
        cycles = list(nx.simple_cycles(dep_graph))
        
        # 2. Identify shared services (nodes with high in-degree in operational graph)
        in_degrees = dict(dep_graph.in_degree())
        # Sort by in-degree descending
        sorted_in = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)
        
        shared_services = []
        for node_id, count in sorted_in:
            if count >= 3:  # Threshold for shared services
                node_data = G.nodes[node_id]
                shared_services.append({
                    "node_id": node_id,
                    "name": node_data.get("name"),
                    "type": node_data.get("type"),
                    "in_degree": count
                })
                
        # 3. Identify migration blockers
        # Blockers are nodes with high out-degree (many things depend on them) 
        # or nodes that sit on critical paths
        out_degrees = dict(dep_graph.out_degree())
        sorted_out = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)
        
        blockers = []
        for node_id, count in sorted_out:
            if count >= 2:
                node_data = G.nodes[node_id]
                blockers.append({
                    "node_id": node_id,
                    "name": node_data.get("name"),
                    "type": node_data.get("type"),
                    "out_degree": count
                })
                
        # 4. Orphaned workloads (nodes with 0 in-degree and 0 out-degree in operational graph)
        orphans = []
        for node_id in G.nodes():
            node_data = G.nodes[node_id]
            # Only consider apps and servers (skip DBs and external)
            if node_data.get("type") in ["server", "application"]:
                if node_id not in dep_graph.nodes() or (dep_graph.in_degree(node_id) == 0 and dep_graph.out_degree(node_id) == 0):
                    # Check that it's not hosted on something active
                    orphans.append({
                        "node_id": node_id,
                        "name": node_data.get("name"),
                        "type": node_data.get("type")
                    })
                    
        analysis_result = {
            "circular_dependencies_count": len(cycles),
            "cycles": [[{"id": n, "name": G.nodes[n].get("name")} for n in cycle] for cycle in cycles],
            "shared_services": shared_services,
            "blockers": blockers,
            "orphans": orphans
        }
        
        print("Dependency analysis complete.")
        return analysis_result

if __name__ == "__main__":
    mapper = DependencyMapperAgent()
    print("DependencyMapperAgent initialized.")
