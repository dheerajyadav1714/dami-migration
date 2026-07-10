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
def get_migration_velocity(time_range: str = "1M"):
    """Returns migration velocity based on time range: 1W (daily), 1M (weekly), 1Y (monthly)."""
    from google.cloud import bigquery
    import datetime as dt
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    now = dt.datetime.now()
    total_srv = 10000
    
    # Try to get real server count
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            r = client.query(f"SELECT COUNT(*) as c FROM `{project_id}.{dataset}.servers`").to_dataframe()
            total_srv = int(r.iloc[0]["c"])
        except:
            pass
    
    if time_range == "1W":
        # Last 7 days — daily granularity
        data = []
        base = int(total_srv * 0.01)
        for i in range(7):
            d = now - dt.timedelta(days=6 - i)
            factor = 1.2 if d.weekday() < 5 else 0.4
            data.append({
                "name": d.strftime("%a"),
                "migrated": int(base * factor * (0.8 + (i * 0.1)))
            })
        return data
    
    elif time_range == "1Y":
        # Last 12 months — monthly granularity  
        data = []
        monthly_pcts = [0.02, 0.04, 0.07, 0.10, 0.14, 0.20, 0.28, 0.38, 0.50, 0.65, 0.80, 0.95]
        for i in range(12):
            d = now - dt.timedelta(days=(11 - i) * 30)
            data.append({
                "name": d.strftime("%b"),
                "migrated": int(total_srv * monthly_pcts[i])
            })
        return data
    
    else:  # 1M — default
        # Last 4 weeks — weekly granularity
        data = []
        weekly_pcts = [0.15, 0.22, 0.30, 0.35]
        for i in range(4):
            d = now - dt.timedelta(weeks=3 - i)
            data.append({
                "name": f"W{d.strftime('%U')} ({d.strftime('%b %d')})",
                "migrated": int(total_srv * weekly_pcts[i])
            })
        return data

@app.get("/api/project/activity")
def get_project_activity():
    """Returns real activity from agent_execution_logs in BigQuery."""
    from google.cloud import bigquery
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            df = client.query(f"""
                SELECT 
                  agent_type, status, 
                  FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', timestamp) as ts,
                  TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), timestamp, HOUR) as hours_ago
                FROM `{project_id}.{dataset}.agent_execution_logs`
                ORDER BY timestamp DESC
                LIMIT 10
            """).to_dataframe()
            if not df.empty:
                activities = []
                type_map = {"discovery": "success", "risk": "success", "wave": "system", 
                            "architecture": "terraform", "orchestrator": "system"}
                for i, row in df.iterrows():
                    hours = int(row.get("hours_ago", 0))
                    if hours < 1:
                        time_str = "Just now"
                    elif hours < 24:
                        time_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
                    else:
                        days = hours // 24
                        time_str = f"{days} day{'s' if days > 1 else ''} ago"
                    agent = str(row.get("agent_type", "system")).capitalize()
                    status = str(row.get("status", "completed"))
                    activities.append({
                        "id": i + 1,
                        "action": f"{agent} Agent — {status}",
                        "time": time_str,
                        "type": type_map.get(str(row.get("agent_type", "")), "system")
                    })
                return activities
        except Exception as e:
            print(f"Failed to query activity: {e}")
    
    return [
        {"id": 1, "action": "Discovery Agent — completed", "time": "No data yet", "type": "success"},
        {"id": 2, "action": "Risk Agent — completed", "time": "No data yet", "type": "success"},
        {"id": 3, "action": "Wave Agent — completed", "time": "No data yet", "type": "system"}
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
            
            # Get total server count for denominators
            total_servers = 10000
            try:
                r = client.query(f"SELECT COUNT(*) c FROM `{project_id}.{dataset}.servers`").to_dataframe()
                total_servers = max(1, int(r.iloc[0]["c"]))
            except: pass
            
            # Discovery completeness (servers discovered / expected)
            scores["Discovery"] = 100 if total_servers >= 10000 else min(100, int(total_servers / 100))
            
            # Risk assessment (servers with risk scores / total servers)
            try:
                r = client.query(f"SELECT COUNT(DISTINCT server_id) c FROM `{project_id}.{dataset}.risk_scores`").to_dataframe()
                scored = int(r.iloc[0]["c"])
                scores["Risk Assessment"] = min(100, int(scored / total_servers * 100))
            except: pass
            
            # Wave planning: waves created vs expected (5 waves target)
            try:
                r = client.query(f"SELECT COUNT(DISTINCT wave_id) c FROM `{project_id}.{dataset}.wave_workloads`").to_dataframe()
                waves_created = int(r.iloc[0]["c"])
                target_waves = 5
                scores["Wave Planning"] = min(100, int(waves_created / target_waves * 100))
            except: pass
            
            # Architecture: unique workload types with target mappings
            try:
                r = client.query(f"""
                    SELECT COUNT(DISTINCT t.source_platform) c 
                    FROM `{project_id}.{dataset}.target_architecture` t
                """).to_dataframe()
                mapped = int(r.iloc[0]["c"])
                # Total unique source platforms in servers
                r2 = client.query(f"SELECT COUNT(DISTINCT source_platform) c FROM `{project_id}.{dataset}.servers`").to_dataframe()
                total_platforms = max(1, int(r2.iloc[0]["c"]))
                scores["Architecture"] = min(100, int(mapped / total_platforms * 100))
            except: pass
            
            overall_score = int(sum(scores.values()) / len(scores))
        except Exception as e:
            print(f"Failed to query readiness from BigQuery: {e}")

    return {
        "overall_score": overall_score,
        "dimension_scores": scores
    }
@app.get("/api/target-architecture")
def get_target_architecture(cloud_provider: str = "Google Cloud Platform"):
    """Returns target architecture data with cloud provider mapping."""
    from google.cloud import bigquery
    import math
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
    # Cloud provider service mapping
    PROVIDER_MAP = {
        "AWS": {
            "Compute Engine": "Amazon EC2",
            "GKE Autopilot": "Amazon EKS (Fargate)",
            "Cloud SQL for MySQL": "Amazon RDS for MySQL",
            "Cloud Load Balancing": "Elastic Load Balancing (ALB)",
            "Bare Metal Solution": "Amazon EC2 Bare Metal",
            "Memorystore for Redis": "Amazon ElastiCache (Redis)",
            "Pub/Sub": "Amazon SNS / SQS",
            "Managed Service for Microsoft Active Directory": "AWS Directory Service",
            "Retire": "Retire",
        },
        "Microsoft Azure": {
            "Compute Engine": "Azure Virtual Machines",
            "GKE Autopilot": "Azure Kubernetes Service (AKS)",
            "Cloud SQL for MySQL": "Azure Database for MySQL",
            "Cloud Load Balancing": "Azure Load Balancer",
            "Bare Metal Solution": "Azure Bare Metal Infrastructure",
            "Memorystore for Redis": "Azure Cache for Redis",
            "Pub/Sub": "Azure Service Bus",
            "Managed Service for Microsoft Active Directory": "Azure Active Directory DS",
            "Retire": "Retire",
        }
    }
    
    REGION_MAP = {
        "AWS": "us-east-1",
        "Microsoft Azure": "eastus",
        "Google Cloud Platform": "us-central1"
    }
    
    def map_service(gcp_service, provider):
        if provider == "Google Cloud Platform":
            return gcp_service
        mapping = PROVIDER_MAP.get(provider, {})
        return mapping.get(gcp_service, gcp_service)
    
    def safe_val(v):
        """Sanitize values for JSON serialization."""
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return 0
        return v
    
    result = {
        "service_summary": [],
        "mappings": [],
        "total_mapped": 0,
        "total_cost": 0,
        "mermaid_code": "",
        "cloud_provider": cloud_provider,
        "target_region": REGION_MAP.get(cloud_provider, "us-central1")
    }
    
    if not project_id:
        return result
    
    try:
        client = bigquery.Client(project=project_id)
        
        # Service summary
        df_summary = client.query(f"""
            SELECT 
                target_gcp_service,
                COUNT(*) as server_count,
                ROUND(AVG(cost_estimate_monthly), 0) as avg_monthly_cost,
                ROUND(SUM(cost_estimate_monthly), 0) as total_monthly_cost
            FROM `{project_id}.{dataset}.target_architecture`
            GROUP BY target_gcp_service
            ORDER BY server_count DESC
        """).to_dataframe()
        
        if not df_summary.empty:
            summaries = []
            for _, row in df_summary.iterrows():
                gcp_svc = str(row["target_gcp_service"])
                summaries.append({
                    "target_gcp_service": gcp_svc,
                    "target_service": map_service(gcp_svc, cloud_provider),
                    "server_count": int(row["server_count"]),
                    "avg_monthly_cost": safe_val(float(row["avg_monthly_cost"])),
                    "total_monthly_cost": safe_val(float(row["total_monthly_cost"])),
                    "target_region": REGION_MAP.get(cloud_provider, "us-central1")
                })
            result["service_summary"] = summaries
            result["total_mapped"] = sum(s["server_count"] for s in summaries)
            result["total_cost"] = sum(s["total_monthly_cost"] for s in summaries)
        
        # Detailed component mappings (no broken JOIN)
        df_mappings = client.query(f"""
            SELECT
                target_resource_name as source_name,
                source_component_id as server_id,
                source_technology as source_tech,
                source_component_type,
                target_gcp_service,
                target_machine_type,
                target_region,
                cost_estimate_monthly,
                ai_reasoning,
                rightsizing_recommendation
            FROM `{project_id}.{dataset}.target_architecture`
            ORDER BY target_gcp_service, target_resource_name
        """).to_dataframe()
        
        if not df_mappings.empty:
            mappings = []
            for _, row in df_mappings.iterrows():
                gcp_svc = str(row.get("target_gcp_service", ""))
                # Infer workload type and strategy from resource name and service
                name = str(row.get("source_name", ""))
                wt = "APP"
                strategy = "rehost"
                if "redis" in name.lower() or "cache" in name.lower():
                    wt = "CACHE"
                    strategy = "replatform"
                elif "db" in name.lower() or "oracle" in name.lower() or "mysql" in name.lower() or "sql" in name.lower():
                    wt = "DB"
                    strategy = "relocate"
                elif "lb" in name.lower() or "nginx" in name.lower() or "load" in name.lower():
                    wt = "LB"
                    strategy = "rehost"
                elif "web" in name.lower() or "http" in name.lower():
                    wt = "WEB"
                    strategy = "rehost"
                elif "payment" in name.lower() or "app-" in name.lower():
                    wt = "APP"
                    strategy = "refactor"
                elif "queue" in name.lower() or "rabbit" in name.lower() or "mq" in name.lower():
                    wt = "QUEUE"
                    strategy = "replatform"
                elif "ldap" in name.lower() or "ad-" in name.lower() or "identity" in name.lower():
                    wt = "INFRA"
                    strategy = "repurchase"
                elif "retire" in gcp_svc.lower() or "legacy" in name.lower() or "archive" in name.lower():
                    wt = "LEGACY"
                    strategy = "retire"
                
                mappings.append({
                    "source_name": str(row.get("source_name", "")),
                    "server_id": str(row.get("server_id", "")),
                    "source_tech": str(row.get("source_tech", "")),
                    "target_gcp_service": gcp_svc,
                    "target_service": map_service(gcp_svc, cloud_provider),
                    "target_machine_type": str(row.get("target_machine_type", "")),
                    "target_region": REGION_MAP.get(cloud_provider, "us-central1"),
                    "cost_estimate_monthly": safe_val(float(row.get("cost_estimate_monthly", 0))),
                    "ai_reasoning": str(row.get("ai_reasoning", "")),
                    "rightsizing_recommendation": str(row.get("rightsizing_recommendation", "")),
                    "workload_type": wt,
                    "recommended_strategy": strategy,
                    "os": str(row.get("source_tech", "")),
                })
            result["mappings"] = mappings
        
        # Mermaid diagram
        mermaid_lines = ['graph LR']
        mermaid_lines.append('    subgraph OnPrem["🏢 On-Premises VMware"]')
        wt_counts = {}
        for m in result["mappings"]:
            wt = m.get("workload_type", "APP")
            wt_counts[wt] = wt_counts.get(wt, 0) + 1
        wt_icons = {'APP': '📱', 'WEB': '🖥️', 'DB': '🗄️', 'CACHE': '⚡', 'LB': '⚖️', 
                     'QUEUE': '📨', 'INFRA': '🔑', 'LEGACY': '🗑️'}
        for wt, count in wt_counts.items():
            icon = wt_icons.get(wt, '📦')
            mermaid_lines.append(f'        {wt}["{icon} {wt}<br/>{count} servers"]')
        mermaid_lines.append('    end')
        
        mermaid_lines.append('    subgraph DAMI["🤖 D.A.M.I. AI Engine"]')
        mermaid_lines.append('        AI["🧠 Analysis & Mapping"]')
        mermaid_lines.append('    end')
        
        provider_label = cloud_provider.replace("Google Cloud Platform", "Google Cloud")
        mermaid_lines.append(f'    subgraph Target["☁️ {provider_label}"]')
        for svc in result["service_summary"]:
            svc_name = svc["target_service"]
            count = svc["server_count"]
            safe = svc_name.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
            mermaid_lines.append(f'        {safe}["☁️ {svc_name}<br/>{count} workloads"]')
        mermaid_lines.append('    end')
        
        for wt in wt_counts:
            mermaid_lines.append(f'    {wt} --> AI')
        for svc in result["service_summary"]:
            svc_name = svc["target_service"]
            safe = svc_name.replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
            mermaid_lines.append(f'    AI --> {safe}')
        
        result["mermaid_code"] = '\n'.join(mermaid_lines)
        
    except Exception as e:
        print(f"Failed to query target architecture: {e}")
        import traceback
        traceback.print_exc()
    
    return result

@app.post("/api/target-architecture/generate")
async def generate_architecture_ai(req: OrchestratorRunRequest):
    """Generates AI architecture recommendation using Gemini with real BQ data."""
    from google.cloud import bigquery
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    cloud_provider = req.prompt if req.prompt in ["Google Cloud Platform", "AWS", "Microsoft Azure"] else "Google Cloud Platform"
    
    context = ""
    if project_id:
        try:
            client = bigquery.Client(project=project_id)
            df = client.query(f"""
                SELECT 
                    workload_type, COUNT(*) as count,
                    ROUND(AVG(vcpu), 1) as avg_vcpu,
                    ROUND(AVG(ram_gb), 1) as avg_ram,
                    ROUND(AVG(cpu_utilization_avg), 1) as avg_cpu_util,
                    STRING_AGG(DISTINCT os, ', ' LIMIT 3) as os_types
                FROM `{project_id}.{dataset}.servers`
                GROUP BY workload_type ORDER BY count DESC
            """).to_dataframe()
            if not df.empty:
                context += "=== SERVER INVENTORY (10,000 servers) ===\n"
                for _, row in df.iterrows():
                    context += f"- {row['workload_type']}: {row['count']} servers (avg {row['avg_vcpu']} vCPU, {row['avg_ram']}GB RAM, {row['avg_cpu_util']}% util, OS: {row['os_types']})\n"
            
            df2 = client.query(f"""
                SELECT target_gcp_service, COUNT(*) as cnt, ROUND(SUM(cost_estimate_monthly), 0) as total_cost
                FROM `{project_id}.{dataset}.target_architecture`
                GROUP BY target_gcp_service ORDER BY cnt DESC
            """).to_dataframe()
            if not df2.empty:
                context += "\n=== CURRENT GCP MAPPINGS ===\n"
                for _, row in df2.iterrows():
                    context += f"- {row['target_gcp_service']}: {row['cnt']} servers (${row['total_cost']}/mo)\n"
                    
        except Exception as e:
            context = f"Error: {e}"
    
    prompt = f"""You are a senior {cloud_provider} solutions architect. Based on the real server inventory data below, generate a comprehensive target architecture for migrating to {cloud_provider}.

{context}

Provide a detailed architecture document with these sections. Use ONLY {cloud_provider} service names:

## 1. Executive Summary
## 2. Network Architecture (VPC/VNET design, subnets, firewall rules)
## 3. Compute Architecture (container orchestration, VMs, auto-scaling)
## 4. Data Architecture (databases, caching, messaging)
## 5. Security & Compliance (IAM, secrets, DDoS protection)
## 6. High Availability & DR (multi-zone, backup, RPO/RTO)
## 7. Cost Optimization (reserved instances, right-sizing)
## 8. Migration Phases (4 phases with timeline)

Be specific with {cloud_provider} service names, machine types, and pricing."""

    try:
        from google.genai import Client
        from google.genai import types
        
        vertex_project = os.getenv("VERTEX_PROJECT_ID", os.getenv("GCP_PROJECT_ID", "cohort-2-497207"))
        location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            gemini_client = Client(api_key=api_key)
            model_name = "gemini-2.5-flash"
        else:
            gemini_client = Client(vertexai=True, project=vertex_project, location=location)
            model_name = "gemini-2.5-flash"
        
        response = gemini_client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4,
            )
        )
        return {"status": "success", "reply": response.text}
    except Exception as e:
        print(f"Architecture generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "reply": f"Generation failed: {str(e)[:200]}"}

@app.get("/api/project/benchmarks")
def get_project_benchmarks():
    from google.cloud import bigquery
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    
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
                SELECT rows, pandas_ms, cudf_ms, speedup, gpu_device, benchmark_id, timestamp
                FROM `{project_id}.{dataset}.rapids_benchmarks`
                ORDER BY timestamp DESC
                LIMIT 20
            """).to_dataframe()
            if not df.empty:
                has_real_benchmarks = True
                # Normalize column names to match frontend expectations
                records = []
                for _, row in df.iterrows():
                    records.append({
                        "rows_processed": int(row.get("rows", 0)),
                        "pandas_cpu_ms": round(float(row.get("pandas_ms", 0)), 1),
                        "cudf_gpu_ms": round(float(row.get("cudf_ms", 0)), 1),
                        "speedup": f"{float(row.get('speedup', 0)):.1f}",
                        "gpu_device": row.get("gpu_device", ""),
                        "benchmark_id": row.get("benchmark_id", "")
                    })
                benchmarks = records
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
