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
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
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
                
        # Wave Planning Grouping Logic - Enterprise-Grade Application-Bundled Scheduling
        srv_to_app = {}
        app_srvs = {} # app_id -> list of srv_ids
        for _, row in apps_df.iterrows():
            app_id = row["app_id"]
            server_list = row["server_ids"]
            if server_list is not None and not (isinstance(server_list, float) and str(server_list) == 'nan'):
                try:
                    for srv_id in server_list:
                        if srv_id in active_servers:
                            srv_to_app[srv_id] = app_id
                            app_srvs.setdefault(app_id, []).append(srv_id)
                except (TypeError, ValueError):
                    pass

        # Standalone servers are treated as their own apps
        for srv_id in active_servers:
            if srv_id not in srv_to_app:
                app_id = f"standalone-{srv_id}"
                srv_to_app[srv_id] = app_id
                app_srvs[app_id] = [srv_id]

        # Determine app attributes
        app_attrs = {}
        server_env_map = dict(zip(servers_df['server_id'], servers_df['environment']))
        
        for app_id, srv_ids in app_srvs.items():
            envs = [server_env_map[s] for s in srv_ids if s in server_env_map]
            is_prod = any(str(e).lower() in ["prod", "production"] for e in envs) if envs else True
            
            scores = [risk_map.get(s, {}).get("overall_risk_score", 5.0) for s in srv_ids]
            max_score = max(scores) if scores else 5.0
            
            strategies = [risk_map.get(s, {}).get("recommended_strategy", "rehost") for s in srv_ids]
            has_database = any(st.lower() == "replatform" for st in strategies)
            has_refactor = any(st.lower() == "refactor" for st in strategies)
            
            # Initial wave assignment based on real-world complexity
            if not is_prod:
                if max_score < 4.5 and len(srv_ids) <= 6:
                    wave_num = 0 # Pilot Wave (low-risk Dev/Staging)
                else:
                    wave_num = 1 # Non-Prod Standard Wave
            else:
                if has_refactor or max_score >= 7.5:
                    wave_num = 4 # High-Complexity Wave (Tier 0 refactor/legacy)
                elif has_database or max_score >= 5.5:
                    wave_num = 3 # Business Critical Databases/Replatform (Tier 1)
                else:
                    wave_num = 2 # Production Rehost Wave (Tier 2 low-med risk)
                    
            app_attrs[app_id] = {
                "wave": wave_num,
                "is_prod": is_prod,
                "max_score": max_score,
                "has_database": has_database,
                "has_refactor": has_refactor,
                "srv_ids": srv_ids
            }

        # Resolve app-to-app dependencies
        # Build App Dependency Graph
        app_G = nx.DiGraph()
        for app_id in app_attrs.keys():
            app_G.add_node(app_id)
            
        for _, row in deps_df.iterrows():
            src_app = row["source_app_id"]
            dst_app = row["target_app_id"]
            if src_app in app_attrs and dst_app in app_attrs:
                app_G.add_edge(src_app, dst_app)
                
        # Resolve topological order for dependencies: if App A depends on App B (B -> A in dependency graph)
        # then App B (the dependency) must be migrated in a wave <= App A's wave.
        changed = True
        while changed:
            changed = False
            for u, v in app_G.edges():
                if app_attrs[u]["wave"] > app_attrs[v]["wave"]:
                    # Pull the prerequisite forward to the target's wave
                    app_attrs[u]["wave"] = app_attrs[v]["wave"]
                    changed = True

        # Group servers into final waves
        temp_waves = {}
        for app_id, attr in app_attrs.items():
            w_num = attr["wave"]
            temp_waves.setdefault(w_num, []).extend(attr["srv_ids"])

        # Map to sorted continuous waves (0, 1, 2, ...)
        sorted_keys = sorted(temp_waves.keys())
        waves = {}
        for new_idx, old_key in enumerate(sorted_keys):
            waves[new_idx] = temp_waves[old_key]
                
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
                
                # Sanitization check for NaN / None values from Pandas
                import pandas as pd
                if pd.isnull(target_service) or not isinstance(target_service, str):
                    target_service = "compute-engine"
                if pd.isnull(target_machine) or not isinstance(target_machine, str):
                    target_machine = "n2-standard-4"
                if pd.isnull(target_region) or not isinstance(target_region, str):
                    target_region = "us-central1"
                if pd.isnull(strategy) or not isinstance(strategy, str):
                    strategy = "rehost"
                    
                app_id = app_by_srv.get(srv_id, "unknown")
                if pd.isnull(app_id) or not isinstance(app_id, str):
                    app_id = "unknown"
                    
                effort = risk_info.get("estimated_effort_days", 2)
                if pd.isnull(effort) or not isinstance(effort, (int, float)) or pd.isnull(effort):
                    effort = 2.0
                est_hours = float(effort * 8.0)
                
                workload_records.append({
                    "wave_id": w_id,
                    "server_id": srv_id,
                    "app_id": app_id,
                    "sequence_in_wave": idx + 1,
                    "migration_approach": strategy,
                    "target_gcp_service": target_service,
                    "target_machine_type": target_machine,
                    "target_region": target_region,
                    "prerequisites": [],
                    "estimated_hours": est_hours,
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
            print("  Loading waves table...")
            job = client.load_table_from_json(wave_records, wave_table_ref, job_config=job_config)
            job.result()
            
            # 2. Load wave workloads
            print("  Loading wave_workloads table...")
            job = client.load_table_from_json(workload_records, workload_table_ref, job_config=job_config)
            job.result()
            
            # 3. Update project status sandbox-safely
            print("  Updating projects table...")
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
            import traceback
            traceback.print_exc()
            raise Exception(f"BigQuery load errors in wave planning: {e}")
            
        print(f"Wave planning complete. Structured {len(waves)} waves. Loaded to BigQuery.")
        return {"waves_count": len(waves), "assigned_workloads_count": len(workload_records)}

if __name__ == "__main__":
    planner = WavePlannerAgent()
    print("WavePlannerAgent initialized.")
