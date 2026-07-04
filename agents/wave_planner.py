# wave_planner.py
import os
import json
from datetime import date, timedelta
from google.cloud import bigquery
import networkx as nx
from dotenv import load_dotenv

load_dotenv()

class WavePlannerAgent:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini client."""
        try:
            from google import genai
            from google.genai import types
            self.genai_types = types
            vertex_project = os.getenv("VERTEX_PROJECT_ID", self.project_id)
            location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
            self.client = genai.Client(
                vertexai=True, project=vertex_project, location=location
            )
        except Exception as e:
            print(f"Gemini init failed: {e}")
            self.client = None
    
    def _ask_gemini(self, prompt: str) -> str:
        """Call Gemini for AI-powered wave analysis."""
        if not self.client:
            return None
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.genai_types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=4096,
                    response_mime_type="application/json"
                )
            )
            return response.text
        except Exception as e:
            print(f"Gemini wave analysis failed: {e}")
            return None
    
    def _ai_generate_wave_details(self, wave_num: int, server_names: list, strategies: list, risk_levels: list) -> dict:
        """Use Gemini to generate smart wave name, rationale, risk mitigation."""
        prompt = f"""You are an enterprise cloud migration architect. Generate details for Migration Wave {wave_num}.

Workloads in this wave:
- Server names: {server_names[:15]}
- Migration strategies: {list(set(strategies))}
- Risk levels: {list(set(risk_levels))}
- Count: {len(server_names)} servers

Return a JSON object with:
{{
  "wave_name": "<descriptive 3-5 word name based on workload types, e.g. 'Core Database Migration', 'Frontend Web Services', 'Legacy System Replatform'>",
  "rationale": "<2-3 sentence technical rationale for why these workloads are grouped together and sequenced at this point>",
  "risk_mitigation": "<specific risk mitigation strategy for this wave's workloads>",
  "success_criteria": "<measurable success criteria specific to these workloads>",
  "rollback_strategy": "<specific rollback plan for this wave>"
}}"""
        result = self._ask_gemini(prompt)
        if result:
            try:
                return json.loads(result)
            except (json.JSONDecodeError, TypeError):
                pass
        return None
        
    def create_migration_waves(self, max_per_wave: int = 25) -> dict:
        """
        Retrieves dependency graph and risk scores, runs topological sorting,
        and assigns workloads to migration waves.
        """
        print("Starting wave planning algorithm...")
        client = bigquery.Client(project=self.project_id)
        
        # 1. Fetch servers
        servers_df = client.query(
            f"SELECT server_id, name, workload_type, environment FROM `{self.project_id}.{self.dataset}.servers`"
        ).to_dataframe()
        
        # 2. Fetch risk scores
        risk_df = client.query(
            f"SELECT server_id, overall_risk_score, risk_level, recommended_strategy FROM `{self.project_id}.{self.dataset}.risk_scores`"
        ).to_dataframe()
        risk_map = {row["server_id"]: row.to_dict() for _, row in risk_df.iterrows()}
        
        # 3. Fetch app mappings & dependencies
        apps_df = client.query(
            f"SELECT app_id, name, server_ids FROM `{self.project_id}.{self.dataset}.applications`"
        ).to_dataframe()
        
        deps_df = client.query(
            f"SELECT source_app_id, target_app_id FROM `{self.project_id}.{self.dataset}.app_dependencies`"
        ).to_dataframe()
        
        # Map server to application
        app_by_srv = {}
        srv_name_by_id = {}
        for _, row in servers_df.iterrows():
            srv_name_by_id[row["server_id"]] = row["name"]
            
        for _, row in apps_df.iterrows():
            server_list = row["server_ids"]
            if server_list is not None and not (isinstance(server_list, float) and str(server_list) == 'nan'):
                try:
                    for srv_id in server_list:
                        app_by_srv[srv_id] = row["app_id"]
                except (TypeError, ValueError):
                    pass
                    
        # Construct graph at the server level (for fine-grained migration scheduling)
        G = nx.DiGraph()
        
        # Add all active servers (exclude RETIRE strategy servers)
        active_servers = []
        retired_servers = []
        
        for _, row in servers_df.iterrows():
            srv_id = row["server_id"]
            risk_info = risk_map.get(srv_id, {})
            strategy = risk_info.get("recommended_strategy", "rehost")
            
            if strategy == "retire":
                retired_servers.append(srv_id)
            else:
                active_servers.append(srv_id)
                G.add_node(srv_id)
                
        # Add server-to-server dependencies
        # First: App-to-App dependency translates to edges between all their constituent servers
        app_srvs = {}
        for srv_id, app_id in app_by_srv.items():
            if srv_id in active_servers:
                app_srvs.setdefault(app_id, []).append(srv_id)
                
        for _, row in deps_df.iterrows():
            src_app = row["source_app_id"]
            dst_app = row["target_app_id"]
            
            src_srvs = app_srvs.get(src_app, [])
            dst_srvs = app_srvs.get(dst_app, [])
            
            # Draw edges from source app servers to destination app servers
            for s in src_srvs:
                for d in dst_srvs:
                    G.add_edge(s, d)
                    
        # Find strongly connected components (circular dependencies)
        # Tightly coupled servers must be migrated in the same wave
        sccs = list(nx.strongly_connected_components(G))
        scc_map = {}
        for idx, scc in enumerate(sccs):
            if len(scc) > 1:
                # Tightly coupled group
                for srv_id in scc:
                    scc_map[srv_id] = f"scc-{idx}"
                    
        # Condense graph for topological sorting (treat SCCs as single nodes)
        # But for simplification in hackathon, we will run topological sort on DAG-version 
        # (remove back-edges or break cycles for sorting)
        acyclic_G = G.copy()
        while True:
            try:
                cycle = nx.find_cycle(acyclic_G, orientation="original")
                # Remove the first edge of the cycle
                acyclic_G.remove_edge(cycle[0][0], cycle[0][1])
            except nx.NetworkXNoCycle:
                break
                
        sorted_servers = list(nx.topological_sort(acyclic_G))
        
        # Wave Planning Grouping Logic
        waves = {}
        migrated = set()
        
        # 1. Wave 0: Pilot Wave
        # Conditions: low risk, no dependencies (in-degree 0 in original graph), non-critical environment
        pilot_candidates = []
        for srv_id in sorted_servers:
            risk_info = risk_map.get(srv_id, {})
            score = risk_info.get("overall_risk_score", 5.0)
            in_degree = G.in_degree(srv_id)
            
            if score < 4.0 and in_degree == 0 and srv_id not in migrated:
                pilot_candidates.append(srv_id)
                if len(pilot_candidates) >= 10:  # Pilot cap
                    break
                    
        for srv_id in pilot_candidates:
            waves.setdefault(0, []).append(srv_id)
            migrated.add(srv_id)
            
        # 2. Sequential Waves (topological order)
        current_wave = 1
        wave_capacity = max_per_wave
        
        # Add remaining servers in topological order
        for srv_id in sorted_servers:
            if srv_id in migrated:
                continue
                
            # If server belongs to a circular group, try to migrate all of them together
            scc_id = scc_map.get(srv_id)
            group_to_add = [srv_id]
            
            if scc_id:
                # Find all unmigrated servers in this group
                group_to_add = [s for s, gid in scc_map.items() if gid == scc_id and s not in migrated]
                
            # If adding this group exceeds current wave capacity, increment wave
            if len(waves.get(current_wave, [])) + len(group_to_add) > wave_capacity:
                current_wave += 1
                
            for s in group_to_add:
                waves.setdefault(current_wave, []).append(s)
                migrated.add(s)
                
        # Prepare BQ records
        wave_records = []
        workload_records = []
        
        start_date = date.today() + timedelta(days=14)
        
        # Fetch architecture mappings for target services (from AI-powered architecture designer)
        arch_map = {}
        try:
            arch_df = client.query(
                f"SELECT server_id, target_gcp_service, target_machine_type, target_region FROM `{self.project_id}.{self.dataset}.architecture_mappings`"
            ).to_dataframe()
            arch_map = {row["server_id"]: row.to_dict() for _, row in arch_df.iterrows()}
        except Exception:
            pass  # Architecture mappings may not exist yet
        
        for w_num, srv_list in waves.items():
            w_id = f"wav-000{w_num}"
            duration = len(srv_list) * 0.5 + 3.0
            duration = int(max(5, duration))
            
            end_date = start_date + timedelta(days=duration)
            
            # Risk Level of wave
            wave_scores = [risk_map.get(s, {}).get("overall_risk_score", 5.0) for s in srv_list]
            avg_score = sum(wave_scores) / len(wave_scores) if wave_scores else 0.0
            w_risk = "low" if avg_score < 4.0 else "high" if avg_score >= 7.0 else "medium"
            
            # Collect wave metadata for AI
            wave_server_names = [srv_name_by_id.get(s, s) for s in srv_list]
            wave_strategies = [risk_map.get(s, {}).get("recommended_strategy", "rehost") for s in srv_list]
            wave_risk_levels = [risk_map.get(s, {}).get("risk_level", "medium") for s in srv_list]
            
            # AI-generated wave details
            ai_details = self._ai_generate_wave_details(w_num, wave_server_names, wave_strategies, wave_risk_levels)
            
            # Fallback names if AI fails
            fallback_names = {
                0: "Pilot Wave",
                1: "Core Web & Frontend Services",
                2: "Middle-Tier Applications",
                3: "Core Databases & Backends",
                4: "Complex & Legacy Workloads",
                5: "Decommissioning & Cleanup"
            }
            
            wave_name = (ai_details or {}).get("wave_name", fallback_names.get(w_num, f"Migration Wave {w_num}"))
            rationale = (ai_details or {}).get("rationale", f"Wave {w_num} targets workloads ordered by dependency sequence. Risk Profile: {w_risk.upper()}.")
            success_criteria = (ai_details or {}).get("success_criteria", "All application traffic cutover. Target latency metrics satisfied. Zero data loss.")
            rollback_strategy = (ai_details or {}).get("rollback_strategy", "Surgical route reversion via Cloud DNS. Restore databases from final pre-migration snapshots.")
            
            wave_records.append({
                "wave_id": w_id,
                "wave_number": w_num,
                "wave_name": wave_name,
                "wave_type": "pilot" if w_num == 0 else "complex" if w_risk == "high" else "standard",
                "estimated_start_date": start_date.isoformat(),
                "estimated_end_date": end_date.isoformat(),
                "estimated_duration_days": duration,
                "rationale": rationale,
                "risk_level": w_risk,
                "workload_count": len(srv_list),
                "total_servers": len(srv_list),
                "total_databases": sum(1 for s in srv_list if risk_map.get(s, {}).get("recommended_strategy") == "replatform"),
                "prerequisites": f"Wave {w_num-1} verification completed successfully" if w_num > 0 else "Landing Zone established",
                "success_criteria": success_criteria,
                "rollback_strategy": rollback_strategy,
                "project_id": self.project_id
            })
            
            for idx, srv_id in enumerate(srv_list):
                risk_info = risk_map.get(srv_id, {})
                strategy = risk_info.get("recommended_strategy", "rehost")
                srv_name = srv_name_by_id.get(srv_id, "")
                
                # Pull target service from architecture_mappings (AI-generated) or fallback
                arch_info = arch_map.get(srv_id, {})
                target_service = arch_info.get("target_gcp_service", "compute-engine")
                target_machine = arch_info.get("target_machine_type", "n2-standard-4")
                target_region = arch_info.get("target_region", "us-central1")
                
                workload_records.append({
                    "wave_id": w_id,
                    "server_id": srv_id,
                    "app_id": app_by_srv.get(srv_id, "unknown"),
                    "sequence_in_wave": idx + 1,
                    "migration_approach": strategy,
                    "target_gcp_service": target_service,
                    "target_machine_type": target_machine,
                    "target_region": target_region,
                    "prerequisites": [],
                    "estimated_hours": float(risk_info.get("estimated_effort_days", 2) * 8.0),
                    "project_id": self.project_id
                })
                
            start_date = end_date + timedelta(days=1)
            
        # Write to BigQuery using sandbox-friendly WRITE_TRUNCATE batch load
        wave_table_ref = client.dataset(self.dataset).table("waves")
        workload_table_ref = client.dataset(self.dataset).table("wave_workloads")
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
        
        try:
            # 1. Load waves
            job = client.load_table_from_json(wave_records, wave_table_ref, job_config=job_config)
            job.result()
            
            # 2. Load wave workloads
            job = client.load_table_from_json(workload_records, workload_table_ref, job_config=job_config)
            job.result()
            
            # 3. Update project status sandbox-safely
            proj_df = client.query(f"SELECT * FROM `{self.project_id}.{self.dataset}.projects`").to_dataframe()
            if not proj_df.empty:
                import pandas as pd
                # Cast total_waves to float64 or int64 safely
                proj_df.loc[0, "status"] = "planning"
                proj_df.loc[0, "total_waves"] = float(len(waves))
                proj_df.loc[0, "current_phase"] = "Planning"
                
                # Convert any datetime/date/object columns to string
                import datetime
                for col in proj_df.columns:
                    proj_df[col] = proj_df[col].apply(lambda x: x.isoformat() if isinstance(x, (datetime.date, datetime.datetime)) and not pd.isnull(x) else x)
                
                proj_records = proj_df.to_dict(orient="records")
                proj_table_ref = client.dataset(self.dataset).table("projects")
                job = client.load_table_from_json(proj_records, proj_table_ref, job_config=job_config)
                job.result()
                
        except Exception as e:
            raise Exception(f"BigQuery load errors in wave planning: {e}")
            
        print(f"Wave planning complete. Structured {len(waves)} waves. Loaded to BigQuery.")
        return {"waves_count": len(waves), "assigned_workloads_count": len(workload_records)}

if __name__ == "__main__":
    planner = WavePlannerAgent()
    print("WavePlannerAgent initialized.")
