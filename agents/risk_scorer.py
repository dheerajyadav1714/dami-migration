# risk_scorer.py
import json
import os
import random
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

class RiskScorerAgent:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
        
    def determine_7r_strategy(self, server: dict, dependency_count: int, has_db: bool) -> tuple:
        """
        Determines the Gartner 7R migration strategy and effort based on rules:
        - Rehost, Relocate, Replatform, Refactor, Repurchase, Retire, Retain
        """
        name = server.get("name", "")
        power_state = server.get("power_state", "poweredOn")
        last_access = server.get("last_access_days", 0)
        os_name = server.get("os", "")
        vcpu = server.get("vcpu", 2)
        ram_gb = server.get("ram_gb", 4.0)
        cpu_util = server.get("cpu_utilization_avg", 10.0)
        ram_util = server.get("ram_utilization_avg", 20.0)
        comp_flags = server.get("compliance_flags", [])
        
        # Rule 1: Retire
        if power_state.upper() == "POWEREDOFF" or last_access > 90:
            return (
                "retire", 
                "Workload is powered off or has not been accessed in over 90 days, indicating it is no longer needed.",
                1, 0.0 # effort days, downtime hours
            )
            
        # Rule 2: Retain
        if "HIPAA" in comp_flags and "PROD" not in name:
            # Let's say we retain staging/dev compliance workloads on prem temporarily
            return (
                "retain",
                "Workload contains sensitive HIPAA data in non-prod environment. Retained on-prem until governance controls are verified.",
                0, 0.0
            )
            
        # Rule 3: Relocate
        if "ORACLE" in name and "PROD" in name:
            # Recommending Relocate to Bare Metal Solution or GCVE for licensing reasons
            return (
                "relocate",
                "Oracle database workload requires hardware-level licensing control. Recommend Relocate to Google Cloud Bare Metal Solution.",
                5, 4.0
            )
            
        # Rule 4: Replatform
        # Replatform databases to Cloud SQL/AlloyDB
        if has_db or server.get("workload_type") == "DB":
            if "MYSQL" in name.upper():
                return (
                    "replatform",
                    "Database workload running MySQL. Recommend Replatforming to managed Cloud SQL for MySQL.",
                    3, 2.0
                )
            else:
                return (
                    "replatform",
                    "Database workload. Recommend Replatforming to Google Cloud SQL or AlloyDB to eliminate operational overhead.",
                    4, 3.0
                )
        
        # Replatform Cache / Queue to Memorystore / PubSub
        if server.get("workload_type") in ["CACHE", "QUEUE"]:
            gcp_service = "Memorystore (Redis)" if server.get("workload_type") == "CACHE" else "Pub/Sub or Managed RabbitMQ"
            return (
                "replatform",
                f"Workload functions as a cache/queue. Replatform to Google Cloud equivalent: {gcp_service}.",
                2, 1.0
            )
            
        # Rule 5: Refactor
        # High business criticality, complex dependencies, or compliance requirements
        if "PAYMENT" in name or ("PCI" in comp_flags and dependency_count >= 5):
            return (
                "refactor",
                "High-criticality payment transaction workload. Re-architect as cloud-native microservices on GKE with Cloud KMS for encryption.",
                15, 8.0
            )
            
        # Rule 6: Repurchase
        if "INFRA-LDAP" in name:
            return (
                "repurchase",
                "Shared LDAP server. Replaced with Google Cloud Identity or Managed Microsoft Active Directory SaaS model.",
                3, 2.0
            )
            
        # Rule 7: Default Rehost (Lift & Shift)
        return (
            "rehost",
            "Standard application workload with moderate utilization and standard OS. Lift & Shift to Google Compute Engine (VM).",
            2, 2.0
        )

    def assess_workloads(self) -> dict:
        """
        Reads server and dependency data from BigQuery, calculates risk scores
        via simulated BQML (if the BQML model is not yet compiled) or directly via BQML,
        and saves 7R decisions back to BigQuery risk_scores table.
        """
        print("Starting risk assessment and 7R classification...")
        client = bigquery.Client(project=self.project_id)
        
        # 1. Fetch servers
        servers_query = f"SELECT * FROM `{self.project_id}.{self.dataset}.servers`"
        servers_df = client.query(servers_query).to_dataframe()
        
        # 2. Fetch database server mappings to check if server hosts a database
        dbs_query = f"SELECT server_id FROM `{self.project_id}.{self.dataset}.databases`"
        db_servers = set(client.query(dbs_query).to_dataframe()["server_id"].tolist())
        
        # 3. Fetch dependencies to compute dependency count per server
        # We'll map application server IDs to their dependency links
        apps_query = f"SELECT app_id, server_ids FROM `{self.project_id}.{self.dataset}.applications`"
        apps_df = client.query(apps_query).to_dataframe()
        
        deps_query = f"SELECT source_app_id, target_app_id FROM `{self.project_id}.{self.dataset}.app_dependencies`"
        deps_df = client.query(deps_query).to_dataframe()
        
        # Build dependency count map
        # First map server to its app
        app_by_srv = {}
        for _, row in apps_df.iterrows():
            server_list = row["server_ids"]
            if server_list is not None and not (isinstance(server_list, float) and str(server_list) == 'nan'):
                try:
                    for srv_id in server_list:
                        app_by_srv[srv_id] = row["app_id"]
                except (TypeError, ValueError):
                    pass
                    
        # In-degree / out-degree counts per app
        app_deps = {}
        for _, row in deps_df.iterrows():
            src = row["source_app_id"]
            dst = row["target_app_id"]
            app_deps[src] = app_deps.get(src, 0) + 1
            app_deps[dst] = app_deps.get(dst, 0) + 1
            
        risk_entries = []
        
        # Execute BQML prediction if model exists, otherwise calculate using scoring formula
        model_exists = False
        bqml_predictions = {}  # server_id → predicted label (1=complex, 0=simple)
        try:
            # Quick check if BQML model exists
            client.get_model(f"{self.project_id}.{self.dataset}.migration_risk_model")
            model_exists = True
            
            if model_exists:
                # Run ML.PREDICT to get BQML predictions for all servers
                predict_query = f"""
                    SELECT
                        s.server_id,
                        predicted_label,
                        predicted_label_probs
                    FROM ML.PREDICT(
                        MODEL `{self.project_id}.{self.dataset}.migration_risk_model`,
                        (
                            SELECT server_id, vcpu, ram_gb, cpu_utilization_avg, ram_utilization_avg
                            FROM `{self.project_id}.{self.dataset}.servers`
                        )
                    ) s
                """
                pred_df = client.query(predict_query).to_dataframe()
                for _, pred_row in pred_df.iterrows():
                    bqml_predictions[pred_row["server_id"]] = int(pred_row["predicted_label"])
                print(f"BQML ML.PREDICT returned predictions for {len(bqml_predictions)} servers.")
        except Exception as e:
            print(f"BQML model check/predict failed (using heuristic fallback): {e}")
            model_exists = False
            
        for idx, row in servers_df.iterrows():
            # Convert pandas row to clean dict with safe defaults for NA/NaN values
            srv = {}
            for col in row.index:
                val = row[col]
                # Replace NA/NaN with sensible defaults
                if val is None or (isinstance(val, float) and str(val) == 'nan'):
                    if col in ('vcpu',): srv[col] = 2
                    elif col in ('ram_gb',): srv[col] = 4.0
                    elif col in ('cpu_utilization_avg', 'ram_utilization_avg'): srv[col] = 10.0
                    elif col in ('last_access_days',): srv[col] = 0
                    elif col in ('compliance_flags',): srv[col] = []
                    elif col in ('power_state',): srv[col] = 'poweredOn'
                    elif col in ('os', 'name', 'server_id', 'workload_type', 'environment'): srv[col] = ''
                    else: srv[col] = val
                else:
                    try:
                        import pandas as pd
                        if pd.isna(val):
                            srv[col] = '' if isinstance(val, str) else 0
                            continue
                    except (TypeError, ValueError):
                        pass
                    srv[col] = val
            
            srv_id = srv.get("server_id", "")
            srv_name = srv.get("name", "")
            
            # Dependency count
            app_id = app_by_srv.get(srv_id)
            dep_count = app_deps.get(app_id, 0) if app_id else 0
            
            has_db = srv_id in db_servers
            
            # Determine 7R strategy
            strategy, rationale, effort, downtime = self.determine_7r_strategy(srv, dep_count, has_db)
            
            # Calculate risk scores (0.0 to 10.0)
            # Complexity score: CPU utilization + RAM + disk size + dependency count
            complexity = (int(srv.get("vcpu", 2)) * 0.2) + (float(srv.get("ram_gb", 4.0)) * 0.05) + (dep_count * 0.8)
            complexity = min(10.0, max(1.0, complexity))
            
            # Business criticality: default to 5, higher for prod/payment
            criticality = 5.0
            if "PROD" in srv_name:
                criticality = 8.0
            if "PAYMENT" in srv_name or "ORACLE" in srv_name:
                criticality = 10.0
            elif "STAGE" in srv_name:
                criticality = 4.0
            elif "DEV" in srv_name or "TEST" in srv_name:
                criticality = 1.0
                
            # Technical risk: EOL OS, high utilization, powered off
            tech_risk = 2.0
            os_name = str(srv.get("os", ""))
            if "2008" in os_name or "7" in os_name or "18.04" in os_name:
                tech_risk += 4.0  # EOL OS risk
            if float(srv.get("cpu_utilization_avg", 10.0)) > 75.0 or float(srv.get("ram_utilization_avg", 20.0)) > 80.0:
                tech_risk += 3.0  # resource pressure risk
                
            tech_risk = min(10.0, tech_risk)
            
            # Compliance risk
            comp_risk = 0.0
            comp_flags = row.get("compliance_flags", [])
            if comp_flags is not None and not (isinstance(comp_flags, float)) and len(comp_flags) > 0:
                comp_risk = len(comp_flags) * 2.5
                
            # Overall score: weighted average boosted by BQML prediction
            heuristic_score = (complexity * 0.3) + (criticality * 0.3) + (tech_risk * 0.2) + (comp_risk * 0.2)
            heuristic_score = min(10.0, round(heuristic_score, 2))
            
            if model_exists and srv_id in bqml_predictions:
                # BQML predicted label: 1 = complex strategy needed, 0 = simple
                bqml_label = bqml_predictions[srv_id]
                # Blend: if BQML predicts complex, boost score by 1.5; if simple, reduce by 1.0
                bqml_adjustment = 1.5 if bqml_label == 1 else -1.0
                overall_score = min(10.0, max(0.0, round(heuristic_score + bqml_adjustment, 2)))
            else:
                overall_score = heuristic_score
                
            # Risk Level classification
            if overall_score >= 8.5:
                risk_level = "critical"
            elif overall_score >= 6.5:
                risk_level = "high"
            elif overall_score >= 3.5:
                risk_level = "medium"
            else:
                risk_level = "low"
                
            risk_entries.append({
                "assessment_id": f"asm-{idx:04d}",
                "server_id": srv_id,
                "app_id": app_id,
                "complexity_score": round(complexity, 2),
                "business_criticality": float(criticality),
                "technical_risk": round(tech_risk, 2),
                "dependency_risk": float(min(10.0, dep_count * 1.5)),
                "data_sensitivity_risk": float(comp_risk),
                "compliance_risk": float(comp_risk),
                "overall_risk_score": overall_score,
                "risk_level": risk_level,
                "recommended_strategy": strategy,
                "strategy_rationale": rationale,
                "alternative_strategy": "rehost" if strategy in ["replatform", "refactor"] else "retain" if strategy == "rehost" else "none",
                "estimated_effort_days": int(effort),
                "estimated_downtime_hours": float(downtime),
                "requires_code_change": True if strategy == "refactor" else False,
                "requires_data_migration": True if strategy in ["replatform", "refactor", "relocate"] else False,
                "requires_network_change": True if strategy in ["relocate", "refactor", "replatform"] else False,
                "project_id": self.project_id
            })
            
        # Write to BigQuery using sandbox-friendly WRITE_TRUNCATE batch load
        table_ref = client.dataset(self.dataset).table("risk_scores")
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
        
        try:
            job = client.load_table_from_json(risk_entries, table_ref, job_config=job_config)
            job.result() # Wait for load to complete
        except Exception as e:
            raise Exception(f"BigQuery batch load error in risk_scores: {e}")
            
        print(f"Risk assessment completed for {len(risk_entries)} servers. Results loaded to BigQuery.")
        return {"assessed_count": len(risk_entries)}

    def train_bqml_model(self) -> str:
        """
        Creates/Trains a BQML logistic regression model on BigQuery to predict
        whether a server will require a complex strategy (Refactor/Replatform/Relocate)
        based on vcpu, ram, cpu/ram average utilization, and compliance flags.
        """
        print("Training BQML logistic regression risk model...")
        client = bigquery.Client(project=self.project_id)
        
        # BQML model training query
        query = f"""
        CREATE OR REPLACE MODEL `{self.project_id}.{self.dataset}.migration_risk_model`
        OPTIONS(
            model_type='LOGISTIC_REG',
            input_label_cols=['label']
        ) AS
        SELECT
            vcpu,
            ram_gb,
            cpu_utilization_avg,
            ram_utilization_avg,
            CASE WHEN recommended_strategy IN ('refactor', 'replatform', 'relocate') THEN 1 ELSE 0 END as label
        FROM
            `{self.project_id}.{self.dataset}.servers` s
        JOIN
            `{self.project_id}.{self.dataset}.risk_scores` r
        ON s.server_id = r.server_id
        """
        
        try:
            query_job = client.query(query)
            query_job.result()  # Wait for training to complete
            return "BQML Model 'migration_risk_model' trained successfully. ML.PREDICT will be used in future risk assessments."
        except Exception as e:
            error_str = str(e)
            if "concurrent model update" in error_str.lower() or "retrain" in error_str.lower():
                return "A BQML training job is already active or finalizing in BigQuery. Please wait a moment and try again."
            return f"Failed to train BQML model: {e}"
    
    def evaluate_bqml_model(self) -> dict:
        """
        Evaluates the trained BQML model using ML.EVALUATE to check accuracy,
        precision, recall, and F1 score.
        """
        print("Evaluating BQML migration risk model...")
        client = bigquery.Client(project=self.project_id)
        
        query = f"""
        SELECT *
        FROM ML.EVALUATE(
            MODEL `{self.project_id}.{self.dataset}.migration_risk_model`,
            (
                SELECT
                    vcpu,
                    ram_gb,
                    cpu_utilization_avg,
                    ram_utilization_avg,
                    CASE WHEN recommended_strategy IN ('refactor', 'replatform', 'relocate') THEN 1 ELSE 0 END as label
                FROM
                    `{self.project_id}.{self.dataset}.servers` s
                JOIN
                    `{self.project_id}.{self.dataset}.risk_scores` r
                ON s.server_id = r.server_id
            )
        )
        """
        
        try:
            eval_df = client.query(query).to_dataframe()
            if not eval_df.empty:
                result = eval_df.iloc[0].to_dict()
                # Convert numpy types to native Python for JSON serialization
                return {k: float(v) if hasattr(v, 'item') else v for k, v in result.items()}
            return {"error": "Empty evaluation result"}
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    scorer = RiskScorerAgent()
    print("RiskScorerAgent initialized.")

