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
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
        self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = Client(api_key=api_key)
        else:
            self.client = Client(vertexai=True, project=self.project_id, location=self.location)

    def _ask_gemini(self, prompt: str, json_mode: bool = False) -> str:
        """Call Gemini model and return text response."""
        try:
            config = types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=16384,
            )
            if json_mode:
                config = types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=16384,
                    response_mime_type="application/json"
                )
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            print(f"Gemini call failed: {e}")
            return None

    def _ai_recommend_services(self, servers_batch: list, db_map: dict) -> list:
        """Use Gemini AI to recommend the BEST target cloud service for each server.
        Not limited to a fixed list — AI picks from ALL GCP services.
        Enhanced with dependency graph, diagram analysis, and compliance context."""
        server_summaries = []
        for srv in servers_batch:
            db_info = db_map.get(srv["server_id"])
            db_str = f", Database: {db_info['db_engine']} ({db_info['size_gb']}GB)" if db_info else ""
            env = srv.get("environment", "unknown")
            risk_score = srv.get("overall_risk_score", 5.0)
            compliance = srv.get("compliance_risk_score", 0.0)
            server_summaries.append(
                f"- ID: {srv['server_id']}, Name: {srv['name']}, "
                f"OS: {srv['os']}, Workload: {srv['workload_type']}, Env: {env}, "
                f"CPU: {srv['vcpu']}vCPU @ {srv.get('cpu_utilization_avg', 10):.0f}% util, "
                f"RAM: {srv['ram_gb']}GB @ {srv.get('ram_utilization_avg', 20):.0f}% util, "
                f"Disk: {srv['disk_gb']}GB, "
                f"Strategy: {srv.get('recommended_strategy', 'rehost')}, "
                f"Risk: {srv.get('risk_level', 'medium')} ({risk_score:.1f}/10), "
                f"Compliance: {compliance:.1f}/10"
                f"{db_str}"
            )

        # Include enrichment context if available
        enrichment = getattr(self, '_enrichment_context', '')

        prompt = f"""You are a Senior Cloud Architect. Analyze each server and recommend the BEST target service for GCP, AWS, and Azure.

RULES:
- Choose from ALL native services for each cloud (e.g. GCP: Compute Engine, GKE; AWS: EC2, EKS; Azure: VMs, AKS).
- For "relocate": Use VMware Engine / VMware Cloud equivalents for workloads needing VMware compatibility.
- For "replatform" DB: Choose best managed DB based on engine and size for each cloud.
- For "refactor": Use Serverless/Containers as appropriate (e.g., Cloud Run / Fargate / Azure Container Apps).
- For "rehost": Use VMs with proper instance families for each cloud.
- Estimate realistic monthly cost in USD for each cloud based on the required machine type/SKU.
{enrichment}
SERVERS:
{chr(10).join(server_summaries)}

Respond with ONLY a JSON array. Each element must strictly match this format:
{{"server_id":"...","target_gcp_service":"...","target_gcp_machine":"...","target_gcp_cost":0.0,"target_aws_service":"...","target_aws_machine":"...","target_aws_cost":0.0,"target_azure_service":"...","target_azure_machine":"...","target_azure_cost":0.0,"ai_reasoning":"...","rightsizing_recommendation":"..."}}

No markdown fences. No explanation. ONLY valid JSON array."""

        result = self._ask_gemini(prompt, json_mode=True)
        if not result:
            return None

        try:
            cleaned = result.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1]
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response: {e}")
            return None

    def generate_architecture_mappings(self) -> dict:
        """Uses Gemini AI to recommend the best target GCP service for each server.
        Enriches prompts with dependency graph, diagram analysis, and compliance data.
        Falls back to heuristic rules if Gemini is unavailable."""
        print("Starting AI-powered architecture design mapping...")
        client = bigquery.Client(project=self.project_id)

        # 1. Core server + risk data
        query = f"""
            SELECT s.server_id, s.name, s.vcpu, s.ram_gb, s.disk_gb, s.os, s.workload_type,
                   s.cpu_utilization_avg, s.ram_utilization_avg, s.environment, s.power_state,
                   r.recommended_strategy, r.risk_level, r.overall_risk_score,
                   r.compliance_risk AS compliance_risk_score
            FROM `{self.project_id}.{self.dataset}.servers` s
            JOIN `{self.project_id}.{self.dataset}.risk_scores` r ON s.server_id = r.server_id
        """
        servers_df = client.query(query).to_dataframe()

        # 2. Database info
        db_query = f"SELECT server_id, db_engine, size_gb FROM `{self.project_id}.{self.dataset}.databases`"
        try:
            dbs_df = client.query(db_query).to_dataframe()
            db_map = {row["server_id"]: row.to_dict() for _, row in dbs_df.iterrows()}
        except Exception:
            db_map = {}

        # 3. Dependency graph context — helps AI understand workload relationships
        dep_context = ""
        try:
            dep_df = client.query(
                f"SELECT source_app_id, target_app_id, protocol, port FROM `{self.project_id}.{self.dataset}.app_dependencies`"
            ).to_dataframe()
            if not dep_df.empty:
                dep_summary = dep_df.groupby("protocol").size().to_dict()
                high_connectivity = dep_df["source_app_id"].value_counts().head(5).to_dict()
                dep_context = (
                    f"\nDEPENDENCY CONTEXT:\n"
                    f"- Total dependencies: {len(dep_df)}\n"
                    f"- Protocols: {dep_summary}\n"
                    f"- Highest connectivity apps: {high_connectivity}\n"
                    f"- Key ports: {sorted(dep_df['port'].unique().tolist())}\n"
                )
        except Exception:
            pass

        # 4. Uploaded architecture diagram analysis — real infrastructure patterns
        diagram_context = ""
        try:
            diag_df = client.query(
                f"SELECT analysis_json FROM `{self.project_id}.{self.dataset}.diagram_analysis` "
                f"ORDER BY analyzed_at DESC LIMIT 1"
            ).to_dataframe()
            if not diag_df.empty:
                diag_json = diag_df.iloc[0]["analysis_json"]
                # Truncate to fit token limits but include key patterns
                diagram_context = f"\nEXISTING ARCHITECTURE (from uploaded diagrams):\n{str(diag_json)[:1500]}\n"
        except Exception:
            pass

        # 5. Environment distribution summary
        env_summary = ""
        try:
            env_counts = servers_df["environment"].value_counts().to_dict()
            env_summary = f"\nENVIRONMENT DISTRIBUTION: {env_counts}\n"
        except Exception:
            pass

        # Combine enrichment context for prompts
        self._enrichment_context = dep_context + diagram_context + env_summary

        servers_list = servers_df.to_dict('records')
        BATCH_SIZE = 34  # Balance between speed (3 batches instead of 10) and JSON reliability
        all_mappings = []

        for i in range(0, len(servers_list), BATCH_SIZE):
            batch = servers_list[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (len(servers_list) + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"  AI analyzing batch {batch_num}/{total_batches} ({len(batch)} servers)...")

            ai_result = self._ai_recommend_services(batch, db_map)

            if ai_result:
                for rec in ai_result:
                    target_config = rec.get("target_config", {})
                    if isinstance(target_config, dict):
                        target_config = json.dumps(target_config)

                    os_name = next((s['os'] for s in batch if s['server_id'] == rec.get('server_id')), 'Unknown')
                    all_mappings.append({
                        "mapping_id": f"map-{len(all_mappings):04d}",
                        "source_component_id": rec.get("server_id", "unknown"),
                        "source_component_type": "server",
                        "source_technology": f"VMware VM ({os_name})",
                        "target_gcp_service": rec.get("target_gcp_service", "compute-engine"),
                        "target_gcp_machine": rec.get("target_gcp_machine", "n2-standard-2"),
                        "target_gcp_cost": float(rec.get("target_gcp_cost", 48.50)),
                        "target_aws_service": rec.get("target_aws_service", "Amazon EC2"),
                        "target_aws_machine": rec.get("target_aws_machine", "t3.large"),
                        "target_aws_cost": float(rec.get("target_aws_cost", 48.50)),
                        "target_azure_service": rec.get("target_azure_service", "Azure Virtual Machines"),
                        "target_azure_machine": rec.get("target_azure_machine", "Standard_D2s_v3"),
                        "target_azure_cost": float(rec.get("target_azure_cost", 48.50)),
                        "target_region": "us-central1",
                        "rightsizing_recommendation": rec.get("rightsizing_recommendation", "Retained original specs."),
                        "ai_reasoning": rec.get("ai_reasoning", "AI-recommended mapping."),
                        "project_id": self.project_id
                    })
            else:
                print(f"  Gemini failed for batch, using fallback heuristics...")
                for srv in batch:
                    mapping = self._fallback_mapping(srv, db_map)
                    if mapping:
                        mapping["mapping_id"] = f"map-{len(all_mappings):04d}"
                        all_mappings.append(mapping)

        # Write to BigQuery - target_architecture (full details for UI)
        table_ref = client.dataset(self.dataset).table("target_architecture")
        job_config = bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True
        )
        try:
            job = client.load_table_from_json(all_mappings, table_ref, job_config=job_config)
            job.result()
        except Exception as e:
            raise Exception(f"BigQuery load error (target_architecture): {e}")

        # Also write simplified mappings for downstream agents (wave_planner)
        try:
            arch_records = []
            for m in all_mappings:
                arch_records.append({
                    "server_id": m.get("source_component_id", ""),
                    "target_gcp_service": m.get("target_gcp_service", "compute-engine"),
                    "target_machine_type": m.get("target_machine_type", "n2-standard-4"),
                    "target_region": m.get("target_region", "us-central1"),
                    "cost_estimate_monthly": m.get("cost_estimate_monthly", 0.0),
                    "ai_reasoning": m.get("ai_reasoning", ""),
                    "project_id": self.project_id
                })
            arch_table = client.dataset(self.dataset).table("architecture_mappings")
            job = client.load_table_from_json(arch_records, arch_table, job_config=job_config)
            job.result()
            print(f"  Also wrote {len(arch_records)} records to architecture_mappings for wave planner.")
        except Exception as e:
            print(f"  Warning: Could not write architecture_mappings: {e}")

        print(f"AI architecture mapping complete. Mapped {len(all_mappings)} resources.")
        return {"mapped_count": len(all_mappings)}

    def _fallback_mapping(self, srv: dict, db_map: dict) -> dict:
        """Fallback heuristic mapping when Gemini is unavailable."""
        strategy = srv["recommended_strategy"]
        workload_type = srv["workload_type"]
        name = srv["name"]
        vcpu = int(srv["vcpu"])
        ram_gb = float(srv["ram_gb"])
        cpu_util = float(srv["cpu_utilization_avg"])
        ram_util = float(srv["ram_utilization_avg"])
        target_cpu = vcpu

        target_service = "compute-engine"
        target_resource_name = f"gce-{name.lower().replace('_', '-')}"
        target_machine_type = "n2-standard-2"

        if strategy == "refactor":
            if workload_type == "WEB" and cpu_util < 30:
                target_service, target_resource_name = "cloud-run", f"run-{name.lower().replace('_', '-')}"
                target_machine_type = "serverless-2vCPU-2GB"
            elif workload_type in ("APP", "WEB"):
                target_service, target_resource_name = "gke-autopilot", f"gke-{name.lower().replace('_', '-')}-deploy"
                target_machine_type = "n2-standard-4"
            else:
                target_service, target_resource_name = "gke-autopilot", f"gke-{name.lower().replace('_', '-')}-pod"
                target_machine_type = "n2-standard-4"
        elif strategy == "replatform":
            db_info = db_map.get(srv["server_id"])
            if db_info is not None or workload_type == "DB":
                db_engine = db_info["db_engine"].upper() if db_info is not None else ""
                if "ORACLE" in db_engine or "ORACLE" in name.upper():
                    target_service, target_resource_name = "bare-metal-solution", f"bms-{name.lower().replace('_', '-')}"
                elif "MYSQL" in db_engine:
                    target_service, target_resource_name = "cloud-sql-mysql", f"sql-mysql-{name.lower().replace('_', '-')}"
                elif "POSTGRES" in db_engine:
                    target_service, target_resource_name = "cloud-sql-postgres", f"sql-pg-{name.lower().replace('_', '-')}"
                else:
                    target_service, target_resource_name = "cloud-sql-mysql", f"sql-db-{name.lower().replace('_', '-')}"
            elif workload_type == "CACHE":
                target_service, target_resource_name = "memorystore-redis", f"redis-{name.lower().replace('_', '-')}"
            elif workload_type == "QUEUE":
                target_service, target_resource_name = "cloud-pubsub", f"pubsub-{name.lower().replace('_', '-')}"
        elif strategy == "relocate":
            target_service, target_resource_name = "gcve", f"gcve-{name.lower().replace('_', '-')}-vm"
            target_machine_type = "node-type-i3"
        elif strategy == "rehost":
            if workload_type == "WEB":
                target_machine_type = f"e2-standard-{max(2, target_cpu)}"
            elif workload_type == "DB":
                target_machine_type = f"n2-highmem-{max(2, target_cpu)}"
            else:
                target_machine_type = f"n2-standard-{max(2, target_cpu)}"
        elif strategy == "retire":
            return None

        rightsizing_rec = "Retained original specs."
        if cpu_util < 15.0 and ram_util < 30.0 and vcpu >= 4:
            target_cpu = max(2, int(vcpu / 2))
            rightsizing_rec = f"Rightsized {vcpu}vCPU/{ram_gb}GB to {target_cpu}vCPU/{ram_gb/2:.0f}GB (low utilization)."

        cost_map = {
            "compute-engine": 24.25 * target_cpu, "gke-autopilot": 48.50 * (target_cpu / 2),
            "cloud-run": 18.00, "cloud-sql-mysql": 95.00 * target_cpu,
            "cloud-sql-postgres": 95.00 * target_cpu, "bare-metal-solution": 850.00,
            "gcve": 180.00, "memorystore-redis": 45.00, "cloud-pubsub": 12.00,
        }
        return {
            "source_component_id": srv["server_id"],
            "source_component_type": "server",
            "source_technology": f"VMware VM ({srv['os']})",
            "target_gcp_service": target_service,
            "target_gcp_machine": target_machine_type,
            "target_gcp_cost": cost_map.get(target_service, 48.50),
            "target_aws_service": target_service,
            "target_aws_machine": target_machine_type,
            "target_aws_cost": cost_map.get(target_service, 48.50),
            "target_azure_service": target_service,
            "target_azure_machine": target_machine_type,
            "target_azure_cost": cost_map.get(target_service, 48.50),
            "target_region": "us-central1",
            "rightsizing_recommendation": rightsizing_rec,
            "ai_reasoning": f"Fallback: {strategy} -> {target_service}.",
            "project_id": self.project_id
        }

    def generate_topology_dot(self, target_cloud: str = "Google Cloud") -> str:
        """Use Gemini to generate a detailed Graphviz DOT diagram from actual BQ data."""
        client = bigquery.Client(project=self.project_id)

        try:
            mappings_df = client.query(
                f"SELECT target_gcp_service, target_machine_type, target_configuration "
                f"FROM `{self.project_id}.{self.dataset}.target_architecture`"
            ).to_dataframe()
            service_summary = mappings_df['target_gcp_service'].value_counts().to_dict()
            total = len(mappings_df)
            
            config_samples = []
            for _, row in mappings_df.head(10).iterrows():
                try:
                    cfg = json.loads(row.get("target_configuration", "{}"))
                    if cfg.get("subnet_cidr"):
                        config_samples.append(f"  {row['target_gcp_service']}: {cfg.get('subnet','')}, {cfg.get('subnet_cidr','')}")
                except Exception:
                    pass
            config_ctx = chr(10).join(config_samples) if config_samples else "  Auto-assign CIDRs"
        except Exception:
            service_summary = {"compute-engine": 40, "gcve": 30, "cloud-sql-mysql": 5}
            total = 75
            config_ctx = "  Auto-assign CIDRs"

        diagram_ctx = ""
        try:
            diag_df = client.query(
                f"SELECT analysis_json FROM `{self.project_id}.{self.dataset}.diagram_analysis` "
                f"ORDER BY analyzed_at DESC LIMIT 1"
            ).to_dataframe()
            if not diag_df.empty:
                diagram_ctx = f"\nUPLOADED ARCHITECTURE CONTEXT:\n{diag_df.iloc[0]['analysis_json'][:2000]}"
        except Exception:
            pass

        cloud_map = {
            "Google Cloud": "GCP services: Compute Engine, GKE, Cloud SQL, GCVE, Cloud Interconnect, Cloud NAT, Cloud Armor",
            "AWS": "AWS services: EC2, EKS, RDS, VMware Cloud on AWS, Direct Connect, NAT Gateway, WAF",
            "Microsoft Azure": "Azure services: VMs, AKS, Azure SQL, AVS, ExpressRoute, NAT Gateway, Azure Firewall"
        }

        prompt = f"""Generate a detailed Graphviz DOT diagram for a {target_cloud} enterprise landing zone.

DATA:
- Total: {total} servers
- Services: {json.dumps(service_summary)}
- Network: {config_ctx}
{diagram_ctx}

Use {cloud_map.get(target_cloud, '')}

REQUIREMENTS:
1. digraph G {{ with rankdir=TB
2. CIDR ranges: Hub=10.0.0.0/16, Spoke=10.1.0.0/20, DB=10.1.16.0/24
3. Clusters: On-Premises, Hub Network, Workload Spoke (with ACTUAL counts), VMware Engine (if any), Security & Ops
4. Dark theme: bgcolor=transparent fillcolor=#1e1e2f fontcolor=#e2e8f0 border=#6366f1
5. Cluster colors: OnPrem=#ea4335 Hub=#4285f4 Spoke=#34a853 VMware=#fbbc04 Ops=#a78bfa
6. Edge labels: VPC Peering, Private Service Access, Interconnect, L2 Stretch
7. Include: Interconnect, Firewall, LB, NAT, DNS, KMS, Logging nodes

Output ONLY the DOT code. Start with digraph. No markdown. No explanation."""

        dot = self._ask_gemini(prompt)
        if dot:
            dot = dot.strip()
            if dot.startswith("```"):
                dot = dot.split("\n", 1)[1]
                dot = dot.rsplit("```", 1)[0].strip()
            return dot
        return None

    def store_diagram_analysis(self, analysis_result: dict, source_filename: str = "uploaded") -> bool:
        """Store Gemini Vision diagram analysis in BigQuery for use by other agents."""
        client = bigquery.Client(project=self.project_id)
        import datetime

        rows = [{
            "analysis_id": f"diag-{source_filename.replace('.', '-')[:30]}",
            "source_filename": source_filename,
            "analysis_json": json.dumps(analysis_result, default=str),
            "component_count": len(analysis_result.get("components", [])),
            "connection_count": len(analysis_result.get("connections", [])),
            "observations": json.dumps(analysis_result.get("observations", [])),
            "analyzed_at": datetime.datetime.utcnow().isoformat()
        }]

        try:
            table_ref = client.dataset(self.dataset).table("diagram_analysis")
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                autodetect=True
            )
            job = client.load_table_from_json(rows, table_ref, job_config=job_config)
            job.result()
            print(f"Diagram analysis stored: {len(analysis_result.get('components', []))} components")
            return True
        except Exception as e:
            print(f"Failed to store diagram analysis: {e}")
            return False

if __name__ == "__main__":
    designer = ArchitectureDesignerAgent()
    print("ArchitectureDesignerAgent initialized.")
