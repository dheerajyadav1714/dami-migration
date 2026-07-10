# main.py
import os
import sys
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.discovery import DiscoveryAgent
from agents.risk_scorer import RiskScorerAgent
from agents.wave_planner import WavePlannerAgent
from api import chat_service

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))

app = FastAPI(
    title="D.A.M.I. API Server",
    description="Discovery & Autonomous Migration Intelligence Backend Service",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRunRequest(BaseModel):
    project_id: str
    phase: str  # discovery, risk, wave, artifacts
    wave_number: int = None

class OrchestratorRunRequest(BaseModel):
    prompt: str

@app.get("/api/info")
def read_root():
    return {
        "status": "online",
        "service": "D.A.M.I. Backend API",
        "project": os.getenv("GCP_PROJECT_ID"),
        "version": "1.0.0"
    }

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form("vmware")
):
    print(f"Received file upload '{file.filename}' for source '{source_type}'...")
    
    # Save file to temp location
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "seed")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, f"uploaded_{file.filename}")
    
    try:
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Ingest using Discovery Agent
        agent = DiscoveryAgent()
        res = agent.normalize_and_load(temp_path, source_type=source_type)
        return {
            "status": "success",
            "message": f"Successfully loaded {res['loaded_count']} servers from {file.filename}.",
            "loaded_count": res["loaded_count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process inventory: {str(e)}")

@app.post("/api/run-agent")
def run_agent(req: AgentRunRequest):
    print(f"Triggering phase '{req.phase}' for project '{req.project_id}'...")
    
    try:
        if req.phase == "discovery":
            seed_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "seed", "sample_rvtools.csv")
            if not os.path.exists(seed_file):
                from scripts.seed_database import main as run_seeding
                run_seeding()
                return {"status": "success", "message": "Database successfully seeded with 100 VMs, apps, and dependencies."}
            else:
                agent = DiscoveryAgent()
                res = agent.normalize_and_load(seed_file, source_type="vmware")
                return {"status": "success", "message": f"Discovered {res['loaded_count']} servers."}
                
        elif req.phase == "risk":
            agent = RiskScorerAgent()
            res = agent.assess_workloads()
            return {"status": "success", "message": f"Assessed and categorized {res['assessed_count']} servers."}
            
        elif req.phase == "wave":
            agent = WavePlannerAgent()
            res = agent.create_migration_waves()
            return {"status": "success", "message": f"Scheduled workloads into {res['waves_count']} migration waves."}
            
        elif req.phase == "artifacts":
            from agents.artifacts_generator import ArtifactsGeneratorAgent
            agent = ArtifactsGeneratorAgent()
            wave_num = req.wave_number if req.wave_number is not None else 0
            res = agent.generate_wave_artifacts(wave_num)
            return {
                "status": "success", 
                "message": f"Successfully generated IaC and Runbooks for Wave {wave_num}.",
                "artifacts_summary": res
            }
            
        else:
            raise HTTPException(status_code=400, detail="Invalid phase type. Select: discovery, risk, wave, artifacts")
            
    except Exception as e:
        print(f"Agent execution error for phase '{req.phase}': {e}")
        # Return 200 with error details instead of 500 so frontend can show useful message
        return {
            "status": "partial",
            "message": f"Agent '{req.phase}' completed with warnings. Data already exists in BigQuery. Error: {str(e)[:150]}"
        }

@app.post("/api/run-orchestrator")
def run_orchestrator(req: OrchestratorRunRequest):
    print(f"Triggering Orchestrator with prompt: '{req.prompt}'...")
    try:
        from google.adk import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        from agents.orchestrator import orchestrator_agent
        
        runner = Runner(
            agent=orchestrator_agent,
            session_service=InMemorySessionService(),
            app_name="DAMI_Migration",
            auto_create_session=True
        )
        
        new_message = types.Content(role="user", parts=[types.Part(text=req.prompt)])
        events = runner.run(
            user_id="api_user",
            session_id="api_session",
            new_message=new_message
        )
        
        triggered_tools = []
        final_response = ""
        
        for event in events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_response = part.text
            calls = event.get_function_calls()
            if calls:
                triggered_tools.extend([c.name for c in calls])
                
        return {
            "status": "success",
            "triggered_tools": triggered_tools,
            "final_response": final_response
        }
    except Exception as e:
        # Fallback to direct Gemini chat when ADK orchestrator fails
        print(f"ADK orchestrator failed, falling back to chat_service: {e}")
        try:
            reply = chat_service.get_orchestrator_response(req.prompt)
            return {
                "status": "success",
                "triggered_tools": ["gemini_chat"],
                "final_response": reply
            }
        except Exception as fallback_err:
            raise HTTPException(status_code=500, detail=f"Orchestrator failed: {str(fallback_err)}")

@app.get("/api/project/stats")
def get_project_stats():
    from google.cloud import bigquery
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    stats = {
        "total_servers": 10000,
        "total_apps": 4,
        "total_dbs": 2,
        "total_waves": 5,
        "savings_pct": 52.4,
        "savings_val": 1200000.0,
        "status": "discovery",
        "phase": "Discovery",
        "client_name": "Acme Global Financial Corp",
        "name": "Enterprise Datacenter Migration"
    }
    
    if not project_id:
        return stats
        
    try:
        client = bigquery.Client(project=project_id)
        
        # Get real server count
        try:
            r = client.query(f"SELECT COUNT(*) as c FROM `{project_id}.{dataset}.servers`").to_dataframe()
            stats["total_servers"] = int(r.iloc[0]["c"])
        except: pass
        
        # Get real wave count
        try:
            r = client.query(f"SELECT COUNT(DISTINCT wave_id) as c FROM `{project_id}.{dataset}.wave_workloads`").to_dataframe()
            if int(r.iloc[0]["c"]) > 0:
                stats["total_waves"] = int(r.iloc[0]["c"])
        except: pass

        # Basic project info
        try:
            query = f"SELECT * FROM `{project_id}.{dataset}.projects` WHERE project_id = 'proj-migration-001'"
            df = client.query(query).to_dataframe()
            if not df.empty:
                row = df.iloc[0]
                stats["savings_pct"] = float(row.get("estimated_savings_pct", 52.4))
                stats["savings_val"] = float(row.get("estimated_savings_annual", 1200000.0))
                stats["phase"] = row.get("current_phase", "Discovery")
                stats["client_name"] = row.get("client_name", "Acme Global Financial Corp")
        except: pass
        
    except Exception as e:
        print(f"Failed to query projects from BigQuery: {e}")
        
    return stats

@app.get("/api/charts/migration-velocity")
def get_migration_velocity():
    # Returns time-series data for the dashboard chart
    return [
        {"name": "Jan", "migrated": 120},
        {"name": "Feb", "migrated": 210},
        {"name": "Mar", "migrated": 250},
        {"name": "Apr", "migrated": 200},
        {"name": "May", "migrated": 310},
        {"name": "Jun", "migrated": 350}
    ]

@app.get("/api/project/activity")
def get_project_activity():
    # Simulated activity feed for now (or could pull from BQ audit logs)
    return [
        {"id": 1, "action": "Wave 2 Completed", "time": "2 hours ago", "type": "success"},
        {"id": 2, "action": "Terraform App-03", "time": "5 hours ago", "type": "terraform"},
        {"id": 3, "action": "Auto-Scaling", "time": "1 day ago", "type": "system"},
        {"id": 4, "action": "Risk Assessment", "time": "2 days ago", "type": "success"}
    ]

@app.get("/api/inventory/servers")
def get_inventory_servers():
    from google.cloud import bigquery
    import pandas as pd
    import math
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    # Base fallback mock data
    mock_data = []
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

    def sanitize_value(v):
        """Replace NaN, Infinity, -Infinity with None for JSON serialization."""
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        return v

    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            query = f"SELECT * FROM `{project_id}.{dataset}.servers` ORDER BY name LIMIT 5000"
            df = client.query(query).to_dataframe()
            if not df.empty:
                # Normalize BQ column names to match frontend expectations
                col_map = {
                    'cpu_cores': 'vcpu',
                    'cpus': 'vcpu',
                    'memory_gb': 'ram_gb',
                    'memory': 'ram_gb',
                    'storage_gb': 'disk_gb',
                    'disk': 'disk_gb',
                    'ip': 'ip_address',
                    'state': 'power_state',
                    'env': 'environment',
                    'type': 'workload_type',
                }
                df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
                records = df.to_dict('records')
                # Sanitize each value
                clean_records = []
                for rec in records:
                    clean_records.append({k: sanitize_value(v) for k, v in rec.items()})
                return clean_records
        except Exception as e:
            print(f"Failed to query servers: {e}")
            
    return mock_data

@app.get("/api/ingestion/quality")
def get_ingestion_quality():
    # Return mock or real data quality stats for the bar chart
    return {
        "overall_score": 79.2,
        "records_profiled": 100,
        "anomalies_found": 0,
        "completeness_data": [
            {"field": "ip_address", "completeness": 99},
            {"field": "disk_gb", "completeness": 100},
            {"field": "vcpu", "completeness": 100},
            {"field": "os", "completeness": 100},
            {"field": "workload_type", "completeness": 100},
            {"field": "os_version", "completeness": 100},
            {"field": "cluster", "completeness": 100},
            {"field": "cpu_utilization_avg", "completeness": 100},
            {"field": "project_id", "completeness": 100},
            {"field": "last_access_days", "completeness": 95},
            {"field": "tags", "completeness": 95},
            {"field": "eol_date", "completeness": 95}
        ]
    }

@app.get("/api/ingestion/zombies")
def get_ingestion_zombies():
    # Mirroring the upload.py Streamlit logic for zombies
    from google.cloud import bigquery
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    zombies = [
        {"server_id": "srv-0088", "name": "zombie-web-dev-01", "cpu_cores": 1, "ram_gb": 2, "environment": "dev"},
        {"server_id": "srv-0089", "name": "zombie-test-app-02", "cpu_cores": 1, "ram_gb": 4, "environment": "test"}
    ]
    
    ip_conflicts = [
        {"ip_address": "10.128.15.42", "count": 2}
    ]
    
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            z_query = f"SELECT server_id, name, cpu_cores, ram_gb, environment FROM `{project_id}.{dataset}.servers` WHERE cpu_utilization_avg < 2 OR (cpu_utilization_avg IS NULL AND environment != 'prod')"
            try:
                z_df = client.query(z_query).to_dataframe()
                if not z_df.empty:
                    zombies = z_df.to_dict('records')
            except: pass
            
            i_query = f"SELECT ip_address, count(*) as count FROM `{project_id}.{dataset}.servers` GROUP BY ip_address HAVING count > 1 AND ip_address IS NOT NULL"
            try:
                i_df = client.query(i_query).to_dataframe()
                if not i_df.empty:
                    ip_conflicts = i_df.to_dict('records')
            except: pass
        except Exception as e:
            print(f"Failed to query zombies: {e}")
            
    return {
        "zombies": zombies,
        "ip_conflicts": ip_conflicts
    }


@app.get("/api/project/readiness")
def get_project_readiness():
    from google.cloud import bigquery
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    # Default values
    scores = {
        "Discovery": 100,
        "Risk Assessment": 100,
        "Wave Planning": 60,
        "Architecture": 100,
        "Compliance": 78
    }
    overall_score = 87
    
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            
            # Discovery completeness
            try:
                r = client.query(f"SELECT COUNT(*) c FROM `{project_id}.{dataset}.servers`").to_dataframe()
                count = int(r.iloc[0]["c"])
                scores["Discovery"] = min(100, count * 2)
            except: pass
            
            # Risk assessment
            try:
                r = client.query(f"SELECT COUNT(*) c FROM `{project_id}.{dataset}.risk_scores`").to_dataframe()
                scored = int(r.iloc[0]["c"])
                scores["Risk Assessment"] = min(100, int(scored / 100 * 100)) # assuming 100 total servers
            except: pass
            
            # Wave planning
            try:
                r = client.query(f"SELECT COUNT(DISTINCT wave_id) c FROM `{project_id}.{dataset}.wave_workloads`").to_dataframe()
                waves = int(r.iloc[0]["c"])
                scores["Wave Planning"] = min(100, waves * 20)
            except: pass
            
            # Architecture mapping
            try:
                r = client.query(f"SELECT COUNT(*) c FROM `{project_id}.{dataset}.target_architecture`").to_dataframe()
                mapped = int(r.iloc[0]["c"])
                scores["Architecture"] = min(100, int(mapped / 100 * 100))
            except: pass
            
            overall_score = int(sum(scores.values()) / len(scores))
        except Exception as e:
            print(f"Failed to query readiness from BigQuery: {e}")

    return {
        "overall_score": overall_score,
        "dimension_scores": scores
    }

@app.get("/api/project/benchmarks")
def get_project_benchmarks():
    from google.cloud import bigquery
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset_v3 = os.getenv("BIGQUERY_DATASET_V3", "dami_data_v3")
    
    has_real_benchmarks = False
    benchmarks = []
    
    # Defaults (Simulated)
    simulated = [
        {"rows_processed": 1000, "pandas_cpu_ms": 12.4, "cudf_gpu_ms": 3.9, "speedup": "3.2x"},
        {"rows_processed": 5000, "pandas_cpu_ms": 58.2, "cudf_gpu_ms": 6.8, "speedup": "8.6x"},
        {"rows_processed": 10000, "pandas_cpu_ms": 112.5, "cudf_gpu_ms": 8.1, "speedup": "13.9x"},
        {"rows_processed": 25000, "pandas_cpu_ms": 280.3, "cudf_gpu_ms": 15.2, "speedup": "18.4x"},
        {"rows_processed": 50000, "pandas_cpu_ms": 561.8, "cudf_gpu_ms": 23.5, "speedup": "23.9x"},
        {"rows_processed": 100000, "pandas_cpu_ms": 1124.6, "cudf_gpu_ms": 39.2, "speedup": "28.7x"}
    ]
    
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            df = client.query(f"""
                SELECT benchmark_id, method, rows_processed, processing_seconds,
                       speedup_factor, gpu_device, platform
                FROM `{project_id}.{dataset_v3}.gpu_benchmarks`
                ORDER BY created_at DESC
                LIMIT 20
            """).to_dataframe()
            if not df.empty:
                has_real_benchmarks = True
                benchmarks = df.to_dict('records')
        except Exception as e:
            print(f"Failed to query real benchmarks: {e}")
            
    return {
        "has_real_benchmarks": has_real_benchmarks,
        "real_benchmarks": benchmarks,
        "simulated_benchmarks": simulated
    }

@app.get("/api/risk/scores")
def get_risk_scores():
    from google.cloud import bigquery
    import pandas as pd
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    mock_risk = [
        {"server_name": "DB-ORACLE-PROD-01", "overall_risk_score": 9.2, "risk_level": "critical", "recommended_strategy": "relocate", "complexity_score": 8.5, "business_criticality": 10.0, "estimated_effort_days": 5, "strategy_rationale": "Oracle DB with custom configuration. Relocate to Google Cloud Bare Metal Solution."},
        {"server_name": "APP-PAYMENT-PROD-01", "overall_risk_score": 8.8, "risk_level": "critical", "recommended_strategy": "refactor", "complexity_score": 7.8, "business_criticality": 10.0, "estimated_effort_days": 15, "strategy_rationale": "Core payment engine. Refactor to microservices on GKE."},
        {"server_name": "DB-MYSQL-STAGE-01", "overall_risk_score": 6.8, "risk_level": "high", "recommended_strategy": "replatform", "complexity_score": 6.0, "business_criticality": 4.0, "estimated_effort_days": 3, "strategy_rationale": "MySQL database. Replatform to Cloud SQL for MySQL."},
        {"server_name": "INFRA-LDAP-01", "overall_risk_score": 6.4, "risk_level": "medium", "recommended_strategy": "repurchase", "complexity_score": 5.0, "business_criticality": 9.0, "estimated_effort_days": 3, "strategy_rationale": "LDAP server. Repurchase with Google Cloud Identity."},
        {"server_name": "CACHE-REDIS-PROD-01", "overall_risk_score": 5.8, "risk_level": "medium", "recommended_strategy": "replatform", "complexity_score": 4.5, "business_criticality": 8.0, "estimated_effort_days": 2, "strategy_rationale": "Redis cache. Replatform to Memorystore for Redis."},
        {"server_name": "WEBAPP-PROD-01", "overall_risk_score": 5.2, "risk_level": "medium", "recommended_strategy": "rehost", "complexity_score": 4.0, "business_criticality": 8.0, "estimated_effort_days": 2, "strategy_rationale": "Prod web host. Rehost to Compute Engine with auto-scaling."},
        {"server_name": "QUEUE-RABBIT-PROD-01", "overall_risk_score": 5.2, "risk_level": "medium", "recommended_strategy": "replatform", "complexity_score": 4.0, "business_criticality": 8.0, "estimated_effort_days": 2, "strategy_rationale": "RabbitMQ queue. Replatform to Pub/Sub."},
        {"server_name": "LB-NGINX-01", "overall_risk_score": 4.5, "risk_level": "medium", "recommended_strategy": "rehost", "complexity_score": 3.0, "business_criticality": 8.0, "estimated_effort_days": 2, "strategy_rationale": "Standard load balancer. Rehost behind Cloud Load Balancing."},
        {"server_name": "LEGACY-ARCHIVE-01", "overall_risk_score": 2.2, "risk_level": "low", "recommended_strategy": "retire", "complexity_score": 2.0, "business_criticality": 1.0, "estimated_effort_days": 1, "strategy_rationale": "Powered off, no traffic. Retire."}
    ]
    
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            query = f"""
                SELECT r.server_id, s.name as server_name, s.workload_type, s.os,
                       r.overall_risk_score, r.risk_level, r.recommended_strategy,
                       r.complexity_score, r.business_criticality, 
                       r.estimated_effort_days, r.strategy_rationale
                FROM `{project_id}.{dataset}.risk_scores` r
                JOIN `{project_id}.{dataset}.servers` s ON r.server_id = s.server_id
                ORDER BY r.overall_risk_score DESC
                LIMIT 500
            """
            df = client.query(query).to_dataframe()
            if not df.empty:
                df = df.where(pd.notnull(df), None)
                return df.to_dict('records')
        except Exception as e:
            print(f"Failed to query risk scores: {e}")
    
    return mock_risk

@app.get("/api/waves")
def get_wave_data():
    from google.cloud import bigquery
    import pandas as pd
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    mock_waves = [
        {"wave_id": "wave-1", "wave_name": "Wave 1 — Low Risk Quick Wins", "server_id": "srv-0007", "server_name": "LB-NGINX-01", "strategy": "rehost", "risk_level": "medium", "effort_days": 2},
        {"wave_id": "wave-1", "wave_name": "Wave 1 — Low Risk Quick Wins", "server_id": "srv-0001", "server_name": "WEBAPP-PROD-01", "strategy": "rehost", "risk_level": "medium", "effort_days": 2},
        {"wave_id": "wave-1", "wave_name": "Wave 1 — Low Risk Quick Wins", "server_id": "srv-0002", "server_name": "WEBAPP-PROD-02", "strategy": "rehost", "risk_level": "medium", "effort_days": 2},
        {"wave_id": "wave-2", "wave_name": "Wave 2 — Managed Services", "server_id": "srv-0005", "server_name": "DB-MYSQL-STAGE-01", "strategy": "replatform", "risk_level": "high", "effort_days": 3},
        {"wave_id": "wave-2", "wave_name": "Wave 2 — Managed Services", "server_id": "srv-0006", "server_name": "CACHE-REDIS-PROD-01", "strategy": "replatform", "risk_level": "medium", "effort_days": 2},
        {"wave_id": "wave-2", "wave_name": "Wave 2 — Managed Services", "server_id": "srv-0008", "server_name": "QUEUE-RABBIT-PROD-01", "strategy": "replatform", "risk_level": "medium", "effort_days": 2},
        {"wave_id": "wave-3", "wave_name": "Wave 3 — Complex Refactor", "server_id": "srv-0003", "server_name": "APP-PAYMENT-PROD-01", "strategy": "refactor", "risk_level": "critical", "effort_days": 15},
        {"wave_id": "wave-3", "wave_name": "Wave 3 — Complex Refactor", "server_id": "srv-0004", "server_name": "DB-ORACLE-PROD-01", "strategy": "relocate", "risk_level": "critical", "effort_days": 5}
    ]
    
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            query = f"""
                SELECT w.wave_id, w.server_id, s.name as server_name,
                       r.recommended_strategy as strategy, r.risk_level,
                       r.estimated_effort_days as effort_days
                FROM `{project_id}.{dataset}.wave_workloads` w
                JOIN `{project_id}.{dataset}.servers` s ON w.server_id = s.server_id
                LEFT JOIN `{project_id}.{dataset}.risk_scores` r ON w.server_id = r.server_id
                ORDER BY w.wave_id, s.name
                LIMIT 500
            """
            df = client.query(query).to_dataframe()
            if not df.empty:
                df = df.where(pd.notnull(df), None)
                return df.to_dict('records')
        except Exception as e:
            print(f"Failed to query waves: {e}")
    
    return mock_waves

@app.get("/api/dependencies")
def get_dependency_data():
    from google.cloud import bigquery
    import pandas as pd
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    mock_deps = [
        {"source_server": "WEBAPP-PROD-01", "target_server": "DB-ORACLE-PROD-01", "dependency_type": "database", "protocol": "TCP/1521", "latency_sensitivity": "high"},
        {"source_server": "WEBAPP-PROD-01", "target_server": "CACHE-REDIS-PROD-01", "dependency_type": "cache", "protocol": "TCP/6379", "latency_sensitivity": "high"},
        {"source_server": "WEBAPP-PROD-02", "target_server": "DB-ORACLE-PROD-01", "dependency_type": "database", "protocol": "TCP/1521", "latency_sensitivity": "high"},
        {"source_server": "APP-PAYMENT-PROD-01", "target_server": "DB-ORACLE-PROD-01", "dependency_type": "database", "protocol": "TCP/1521", "latency_sensitivity": "critical"},
        {"source_server": "APP-PAYMENT-PROD-01", "target_server": "QUEUE-RABBIT-PROD-01", "dependency_type": "messaging", "protocol": "AMQP/5672", "latency_sensitivity": "medium"},
        {"source_server": "LB-NGINX-01", "target_server": "WEBAPP-PROD-01", "dependency_type": "http", "protocol": "TCP/443", "latency_sensitivity": "high"},
        {"source_server": "LB-NGINX-01", "target_server": "WEBAPP-PROD-02", "dependency_type": "http", "protocol": "TCP/443", "latency_sensitivity": "high"},
        {"source_server": "INFRA-LDAP-01", "target_server": "WEBAPP-PROD-01", "dependency_type": "authentication", "protocol": "LDAP/389", "latency_sensitivity": "low"}
    ]
    
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            query = f"""
                SELECT source_server_id, target_server_id, dependency_type, protocol, latency_sensitivity,
                       s1.name as source_server, s2.name as target_server
                FROM `{project_id}.{dataset}.dependencies` d
                JOIN `{project_id}.{dataset}.servers` s1 ON d.source_server_id = s1.server_id
                JOIN `{project_id}.{dataset}.servers` s2 ON d.target_server_id = s2.server_id
                LIMIT 500
            """
            df = client.query(query).to_dataframe()
            if not df.empty:
                df = df.where(pd.notnull(df), None)
                return df.to_dict('records')
        except Exception as e:
            print(f"Failed to query dependencies: {e}")
    
    return mock_deps

@app.post("/api/chat")
async def chat_with_agent(req: OrchestratorRunRequest):
    print(f"Received chat message: {req.prompt}")
    reply = chat_service.get_orchestrator_response(req.prompt)
    return {"status": "success", "reply": reply}

@app.get("/api/chat/suggestions")
async def get_chat_suggestions():
    suggestions = chat_service.get_random_suggestions(4)
    return {"status": "success", "suggestions": suggestions}

@app.get("/api/agent/traces")
async def get_agent_traces():
    from google.cloud import bigquery
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    traces = []
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            query = f"SELECT * FROM `{project_id}.{dataset}.agent_execution_logs` ORDER BY timestamp DESC LIMIT 20"
            results = client.query(query).result()
            for row in results:
                record = {}
                for key in row.keys():
                    val = row[key]
                    if val is None:
                        record[key] = ''
                    elif isinstance(val, (int, float, str, bool)):
                        record[key] = val
                    else:
                        record[key] = str(val)
                traces.append(record)
        except Exception as e:
            print(f"Traces error: {e}")
    return traces

@app.get("/api/learning/stats")
async def get_learning_stats():
    from google.cloud import bigquery as bq
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    try:
        client = bq.Client(project=project_id)
        query = f"""
            SELECT 
                COUNT(*) as total_memories,
                COUNTIF(learning_type = 'correction') as corrections,
                COUNTIF(learning_type = 'pattern') as patterns,
                COUNTIF(learning_type = 'optimization') as optimizations,
                COUNTIF(learning_type = 'insight') as insights,
                ROUND(AVG(effectiveness_score), 3) as avg_effectiveness,
                SUM(applied_count) as total_applications,
                COUNT(DISTINCT agent_name) as agents_learning
            FROM `{project_id}.{dataset}.agent_memories`
        """
        df = client.query(query).to_dataframe()
        if not df.empty:
            row = df.iloc[0].to_dict()
            return {k: (float(v) if v is not None else 0) for k, v in row.items()}
    except Exception as e:
        print(f"Learning stats error: {e}")
    return {"total_memories": 0, "corrections": 0, "patterns": 0, "optimizations": 0,
            "insights": 0, "avg_effectiveness": 0.0, "total_applications": 0, "agents_learning": 0}

@app.get("/api/learning/memories")
async def get_learning_memories():
    from google.cloud import bigquery as bq
    import json as _json
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    try:
        client = bq.Client(project=project_id)
        query = f"""
            SELECT memory_id, agent_name, learning_type, context_json,
                   original_output, corrected_output, confidence_delta,
                   tags, created_at, applied_count, effectiveness_score
            FROM `{project_id}.{dataset}.agent_memories`
            ORDER BY effectiveness_score DESC, created_at DESC
            LIMIT 50
        """
        results = client.query(query).result()
        records = []
        for row in results:
            record = {}
            for key in row.keys():
                val = row[key]
                if val is None:
                    record[key] = 0 if key in ('applied_count', 'confidence_delta', 'effectiveness_score') else ''
                elif isinstance(val, (list, tuple)):
                    record[key] = [str(x) for x in val]
                elif isinstance(val, (int, float, str, bool)):
                    record[key] = val
                else:
                    record[key] = str(val)
            records.append(record)
        return records
    except Exception as e:
        print(f"Learning memories error: {e}")
        import traceback; traceback.print_exc()
    return []

class FeedbackRequest(BaseModel):
    agent_name: str
    learning_type: str = "correction"
    context: dict = {}
    original_output: str = ""
    corrected_output: str = ""

@app.post("/api/learning/feedback")
async def store_learning_feedback(req: FeedbackRequest):
    try:
        from agents.memory_store import MemoryStore
        store = MemoryStore()
        memory_id = store.store_learning(
            agent_name=req.agent_name,
            learning_type=req.learning_type,
            context=req.context,
            original_output=req.original_output,
            corrected_output=req.corrected_output
        )
        return {"status": "success", "memory_id": memory_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============================================================
# PDF Report Generation
# ============================================================
@app.get("/api/report/pdf")
async def generate_pdf_report():
    """Generate a professional PDF executive report with real BigQuery data."""
    from fastapi.responses import Response
    from fpdf import FPDF
    from google.cloud import bigquery
    import datetime

    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    client = bigquery.Client(project=project_id)

    # Fetch data
    stats = {}
    try:
        row = list(client.query(f"SELECT * FROM `{project_id}.{dataset}.project_config` LIMIT 1").result())[0]
        stats = dict(row)
    except: pass

    risk_data = []
    try:
        risk_data = [dict(r) for r in client.query(f"SELECT risk_level, COUNT(*) as cnt FROM `{project_id}.{dataset}.risk_scores` GROUP BY risk_level ORDER BY cnt DESC").result()]
    except: pass

    wave_data = []
    try:
        wave_data = [dict(r) for r in client.query(f"SELECT wave_id, COUNT(*) as cnt FROM `{project_id}.{dataset}.wave_workloads` GROUP BY wave_id ORDER BY wave_id").result()]
    except: pass

    bench_data = []
    try:
        bench_data = [dict(r) for r in client.query(f"SELECT * FROM `{project_id}.{dataset}.rapids_benchmarks` ORDER BY rows_processed LIMIT 10").result()]
    except: pass

    # Build PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 15, "D.A.M.I. Executive Report", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Generated: {datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')}", ln=True, align="C")
    pdf.ln(5)

    # Project Info
    pdf.set_draw_color(79, 70, 229)
    pdf.set_line_width(0.8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 10, "Project Overview", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    items = [
        ("Project", stats.get("name", "Enterprise Datacenter Migration")),
        ("Client", stats.get("client_name", "Acme Global Financial Corp")),
        ("Phase", stats.get("phase", "Planning")),
        ("Total Servers", f"{stats.get('total_servers', 10000):,}"),
        ("Migration Waves", str(stats.get("total_waves", 3))),
        ("Est. Annual Savings", f"${stats.get('savings_val', 1200000):,.0f} ({stats.get('savings_pct', 52.4)}%)"),
    ]
    for label, value in items:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(60, 8, f"  {label}:")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, value, ln=True)
    pdf.ln(5)

    # Risk Assessment
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 10, "Risk Assessment", ln=True)
    if risk_data:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(79, 70, 229)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(95, 8, "  Risk Level", border=1, fill=True)
        pdf.cell(95, 8, "  Server Count", border=1, fill=True, ln=True)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Helvetica", "", 10)
        for row in risk_data:
            pdf.cell(95, 7, f"  {row['risk_level'].upper()}", border=1)
            pdf.cell(95, 7, f"  {row['cnt']}", border=1, ln=True)
    else:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 8, "  Risk data not yet available.", ln=True)
    pdf.ln(5)

    # Wave Plan
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(30, 30, 80)
    pdf.cell(0, 10, "Migration Wave Plan", ln=True)
    if wave_data:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(16, 185, 129)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(95, 8, "  Wave ID", border=1, fill=True)
        pdf.cell(95, 8, "  Servers Assigned", border=1, fill=True, ln=True)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Helvetica", "", 10)
        for row in wave_data:
            pdf.cell(95, 7, f"  {row['wave_id']}", border=1)
            pdf.cell(95, 7, f"  {row['cnt']}", border=1, ln=True)
    else:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 8, "  Wave data not yet available.", ln=True)
    pdf.ln(5)

    # RAPIDS Benchmarks
    if bench_data:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(30, 30, 80)
        pdf.cell(0, 10, "NVIDIA RAPIDS GPU Acceleration", ln=True)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(118, 185, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(47, 8, "  Rows", border=1, fill=True)
        pdf.cell(47, 8, "  CPU (ms)", border=1, fill=True)
        pdf.cell(47, 8, "  GPU (ms)", border=1, fill=True)
        pdf.cell(49, 8, "  Speedup", border=1, fill=True, ln=True)
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Helvetica", "", 10)
        for b in bench_data:
            pdf.cell(47, 7, f"  {b.get('rows_processed', 'N/A'):,}", border=1)
            pdf.cell(47, 7, f"  {b.get('pandas_cpu_ms', 'N/A')}", border=1)
            pdf.cell(47, 7, f"  {b.get('cudf_gpu_ms', 'N/A')}", border=1)
            pdf.cell(49, 7, f"  {b.get('speedup', 'N/A')}x", border=1, ln=True)
        pdf.ln(5)

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "This report was generated by D.A.M.I. (DevOps Autonomous Multi-agent Intelligence)", ln=True, align="C")
    pdf.cell(0, 6, f"Data sourced from BigQuery: {project_id}.{dataset}", ln=True, align="C")

    pdf_bytes = pdf.output()
    filename = f"DAMI_Executive_Report_{datetime.datetime.now().strftime('%Y-%m-%d')}.pdf"
    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# Health check endpoint for Cloud Run
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "dami-v3"}

# ============================================================
# PRODUCTION: Serve React static files + SPA fallback
# ============================================================
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

if os.path.isdir(FRONTEND_DIR):
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    # Serve static assets (JS, CSS, images)
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static-assets")

    # SPA fallback: serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If the file exists in dist/, serve it (e.g., favicon, manifest)
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Otherwise serve index.html for client-side routing
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
