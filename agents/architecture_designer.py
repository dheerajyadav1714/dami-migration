# agents/architecture_designer.py
import os
import json
from google.cloud import bigquery
from google.genai import Client
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class ArchitectureDesignerAgent:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
        self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        # Check if GEMINI_API_KEY is available, otherwise use keyless Vertex AI
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = Client(api_key=api_key)
            self.use_vertex = False
        else:
            self.client = Client(enterprise=True)
            self.use_vertex = True

    def generate_architecture_mappings(self) -> dict:
        """
        Reads server, database, and risk data from BigQuery, maps each server to target 
        GCP service, performs sizing rightsizing, and saves results to target_architecture.
        """
        print("Starting architecture design mapping...")
        client = bigquery.Client(project=self.project_id)
        
        # 1. Fetch servers and risk scores
        query = f"""
            SELECT s.server_id, s.name, s.vcpu, s.ram_gb, s.disk_gb, s.os, s.workload_type, s.cpu_utilization_avg, s.ram_utilization_avg,
                   r.recommended_strategy, r.risk_level
            FROM `{self.project_id}.{self.dataset}.servers` s
            JOIN `{self.project_id}.{self.dataset}.risk_scores` r ON s.server_id = r.server_id
        """
        servers_df = client.query(query).to_dataframe()
        
        # 2. Fetch database engines
        db_query = f"SELECT server_id, db_engine, size_gb FROM `{self.project_id}.{self.dataset}.databases`"
        try:
            dbs_df = client.query(db_query).to_dataframe()
            db_map = {row["server_id"]: row for _, row in dbs_df.iterrows()}
        except Exception:
            db_map = {}
        
        mapping_entries = []
        
        for idx, row in servers_df.iterrows():
            srv_id = row["server_id"]
            name = row["name"]
            workload_type = row["workload_type"]
            strategy = row["recommended_strategy"]
            cpu_util = float(row["cpu_utilization_avg"])
            ram_util = float(row["ram_utilization_avg"])
            vcpu = int(row["vcpu"])
            ram_gb = float(row["ram_gb"])
            
            # Map target GCP service based on Gartner 7R strategy + workload analysis
            target_service = "compute-engine"
            target_resource_name = f"gce-{name.lower().replace('_', '-')}"
            target_machine_type = "n2-standard-2"
            
            if strategy == "refactor":
                # Refactor: Containerize the workload
                if workload_type == "WEB" and cpu_util < 30:
                    # Low-traffic web → Cloud Run (serverless containers)
                    target_service = "cloud-run"
                    target_resource_name = f"run-{name.lower().replace('_', '-')}"
                    target_machine_type = "serverless-2vCPU-2GB"
                elif workload_type in ("APP", "WEB"):
                    # Standard app → GKE Autopilot
                    target_service = "gke-autopilot"
                    target_resource_name = f"gke-{name.lower().replace('_', '-')}-deploy"
                    target_machine_type = "n2-standard-4"
                elif workload_type == "BATCH":
                    # Batch processing → Dataflow
                    target_service = "dataflow"
                    target_resource_name = f"df-{name.lower().replace('_', '-')}-job"
                    target_machine_type = "n1-standard-4"
                else:
                    target_service = "gke-autopilot"
                    target_resource_name = f"gke-{name.lower().replace('_', '-')}-pod"
                    target_machine_type = "n2-standard-4"
            elif strategy == "replatform":
                db_info = db_map.get(srv_id)
                if db_info is not None or workload_type == "DB":
                    db_engine = db_info["db_engine"].upper() if db_info is not None else ""
                    db_size = float(db_info["size_gb"]) if db_info is not None else 0
                    
                    if "ORACLE" in db_engine or "ORACLE" in name.upper():
                        target_service = "bare-metal-solution"
                        target_resource_name = f"bms-{name.lower().replace('_', '-')}"
                        target_machine_type = "custom-16-64"
                    elif "MYSQL" in db_engine or "MYSQL" in name.upper():
                        target_service = "cloud-sql-mysql"
                        target_resource_name = f"sql-mysql-{name.lower().replace('_', '-')}"
                        target_machine_type = "db-n2-standard-2"
                    elif "POSTGRES" in db_engine or "PG" in db_engine or "POSTGRES" in name.upper():
                        if db_size > 500:
                            # Large PG → AlloyDB for performance
                            target_service = "alloydb"
                            target_resource_name = f"alloydb-{name.lower().replace('_', '-')}"
                            target_machine_type = "alloydb-standard-4"
                        else:
                            target_service = "cloud-sql-postgres"
                            target_resource_name = f"sql-pg-{name.lower().replace('_', '-')}"
                            target_machine_type = "db-n2-standard-2"
                    elif "MSSQL" in db_engine or "SQL SERVER" in db_engine:
                        target_service = "cloud-sql-sqlserver"
                        target_resource_name = f"sql-mssql-{name.lower().replace('_', '-')}"
                        target_machine_type = "db-n2-standard-4"
                    elif "MONGO" in db_engine:
                        target_service = "mongodb-atlas"  # Partner managed
                        target_resource_name = f"atlas-{name.lower().replace('_', '-')}"
                        target_machine_type = "M30"
                    elif "SPANNER" in db_engine or db_size > 2000:
                        target_service = "cloud-spanner"
                        target_resource_name = f"spanner-{name.lower().replace('_', '-')}"
                        target_machine_type = "regional-3-nodes"
                    else:
                        target_service = "cloud-sql-mysql"
                        target_resource_name = f"sql-db-{name.lower().replace('_', '-')}"
                        target_machine_type = "db-n2-standard-2"
                elif workload_type == "CACHE":
                    target_service = "memorystore-redis"
                    target_resource_name = f"redis-{name.lower().replace('_', '-')}"
                    target_machine_type = "standard-ha-1gb"
                elif workload_type == "QUEUE":
                    target_service = "cloud-pubsub"
                    target_resource_name = f"pubsub-{name.lower().replace('_', '-')}"
                    target_machine_type = "serverless"
                elif workload_type == "NFS" or "file" in name.lower():
                    target_service = "filestore"
                    target_resource_name = f"fs-{name.lower().replace('_', '-')}"
                    target_machine_type = "enterprise-1TB"
                elif workload_type == "ANALYTICS":
                    target_service = "bigquery"
                    target_resource_name = f"bq-{name.lower().replace('_', '-')}"
                    target_machine_type = "on-demand"
                elif workload_type == "LB" or "nginx" in name.lower() or "haproxy" in name.lower():
                    target_service = "cloud-load-balancing"
                    target_resource_name = f"lb-{name.lower().replace('_', '-')}"
                    target_machine_type = "global-external-https"
                elif workload_type == "DNS":
                    target_service = "cloud-dns"
                    target_resource_name = f"dns-{name.lower().replace('_', '-')}"
                    target_machine_type = "managed-zone"
                elif workload_type == "CDN":
                    target_service = "cloud-cdn"
                    target_resource_name = f"cdn-{name.lower().replace('_', '-')}"
                    target_machine_type = "global-cache"
                elif workload_type == "LDAP" or "identity" in name.lower():
                    target_service = "cloud-identity"
                    target_resource_name = f"cid-{name.lower().replace('_', '-')}"
                    target_machine_type = "managed-service"
            elif strategy == "relocate":
                target_service = "gcve"
                target_resource_name = f"gcve-{name.lower().replace('_', '-')}-vm"
                target_machine_type = "node-type-i3"
            elif strategy == "rehost":
                # Lift-and-shift: size the VM correctly
                if workload_type == "WEB":
                    target_machine_type = f"e2-standard-{max(2, target_cpu)}"
                elif workload_type == "APP":
                    target_machine_type = f"n2-standard-{max(2, target_cpu)}"
                elif workload_type == "DB":
                    target_machine_type = f"n2-highmem-{max(2, target_cpu)}"
                else:
                    target_machine_type = f"n2-standard-{max(2, target_cpu)}"
            elif strategy == "retire":
                continue  # Do not migrate retired servers
                
            # Rightsizing logic
            rightsizing_rec = "Retained original specs."
            target_cpu = vcpu
            target_ram = ram_gb
            
            if cpu_util < 15.0 and ram_util < 30.0:
                if vcpu >= 4:
                    target_cpu = max(2, int(vcpu / 2))
                    target_ram = max(4.0, ram_gb / 2)
                    rightsizing_rec = f"Rightsized from {vcpu}vCPU/{ram_gb}GB to {target_cpu}vCPU/{target_ram}GB based on low avg utilization (CPU={cpu_util}%, RAM={ram_util}%)."
            
            # Machine type refinement for Compute Engine
            if target_service == "compute-engine":
                target_machine_type = f"n2-standard-{target_cpu}" if target_cpu in [2, 4, 8, 16, 32, 48, 64] else "n2-standard-2"
                
            # Estimate monthly cost (based on GCP public pricing approximations)
            cost_map = {
                "compute-engine": 24.25 * target_cpu,
                "gke-autopilot": 48.50 * (target_cpu / 2),
                "cloud-run": 18.00,
                "cloud-sql-mysql": 95.00 * target_cpu,
                "cloud-sql-postgres": 95.00 * target_cpu,
                "cloud-sql-sqlserver": 120.00 * target_cpu,
                "alloydb": 135.00 * target_cpu,
                "cloud-spanner": 450.00,
                "mongodb-atlas": 200.00,
                "memorystore-redis": 45.00,
                "cloud-pubsub": 12.00,
                "bare-metal-solution": 850.00,
                "gcve": 180.00,
                "cloud-load-balancing": 25.00,
                "cloud-cdn": 15.00,
                "cloud-dns": 5.00,
                "cloud-identity": 6.00,
                "filestore": 180.00,
                "bigquery": 35.00,
                "dataflow": 65.00 * target_cpu,
                "dataproc": 48.50 * target_cpu
            }
            cost_estimate = cost_map.get(target_service, 48.50)
            
            # Simple config JSON structure
            target_config = {
                "vpc_network": "dami-vpc",
                "subnet": f"subnet-{target_service}",
                "disk_type": "pd-ssd",
                "disk_size_gb": float(row["disk_gb"]),
                "backup_enabled": True if target_service in ["cloud-sql", "alloydb", "bare-metal-solution"] else False,
                "high_availability": True if row["risk_level"] in ["high", "critical"] else False
            }
            
            # Generate AI reasoning for this mapping
            ai_reasoning = f"Strategy: {strategy}. "
            if strategy == "refactor":
                ai_reasoning += f"Workload '{workload_type}' at {cpu_util:.0f}% CPU utilization is a candidate for containerization → {target_service}."
            elif strategy == "replatform":
                db_info_val = db_map.get(srv_id)
                if db_info_val is not None:
                    ai_reasoning += f"Database engine '{db_info_val['db_engine']}' replatformed to managed {target_service} for reduced ops overhead."
                else:
                    ai_reasoning += f"Workload '{workload_type}' mapped to managed {target_service} service."
            elif strategy == "rehost":
                ai_reasoning += f"Lift-and-shift to {target_service}. Rightsized from {vcpu}vCPU/{ram_gb}GB based on utilization ({cpu_util:.0f}% CPU, {ram_util:.0f}% RAM)."
            elif strategy == "relocate":
                ai_reasoning += f"VM-level relocation to GCVE preserving VMware tooling."
            elif strategy == "repurchase":
                ai_reasoning += f"Legacy {workload_type} replaced with managed SaaS equivalent."
            else:
                ai_reasoning += f"Mapped to {target_service} based on workload profile."
            
            mapping_entries.append({
                "mapping_id": f"map-{idx:04d}",
                "source_component_id": srv_id,
                "source_component_type": "server",
                "source_technology": f"VMware VM ({row['os']})",
                "target_gcp_service": target_service,
                "target_resource_name": target_resource_name,
                "target_machine_type": target_machine_type,
                "target_region": "us-central1",
                "target_configuration": json.dumps(target_config),
                "rightsizing_recommendation": rightsizing_rec,
                "ai_reasoning": ai_reasoning,
                "cost_estimate_monthly": float(cost_estimate),
                "project_id": self.project_id
            })
            
        # Write to BigQuery using sandbox-friendly WRITE_TRUNCATE batch load
        table_ref = client.dataset(self.dataset).table("target_architecture")
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
        )
        
        try:
            job = client.load_table_from_json(mapping_entries, table_ref, job_config=job_config)
            job.result()
        except Exception as e:
            raise Exception(f"BigQuery load error in target_architecture: {e}")
            
        print(f"Architecture mappings generation complete. Mapped {len(mapping_entries)} resources to GCP.")
        return {"mapped_count": len(mapping_entries)}

if __name__ == "__main__":
    designer = ArchitectureDesignerAgent()
    print("ArchitectureDesignerAgent initialized.")
