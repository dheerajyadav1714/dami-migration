# seed_database.py
import csv
import json
import os
import random
import sys
from datetime import date
from google.cloud import bigquery
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.seed.generate_seed_data import generate_rvtools_csv, generate_dependencies_json

def load_env_vars():
    load_dotenv()
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
    if not project_id:
        print("Error: GCP_PROJECT_ID not set in .env")
        sys.exit(1)
    return project_id, dataset

def classify_workload(vm_name):
    if "LB-" in vm_name:
        return "LB"
    elif "WEBAPP-" in vm_name:
        return "WEB"
    elif "APP-" in vm_name:
        return "APP"
    elif "DB-" in vm_name:
        return "DB"
    elif "CACHE-" in vm_name:
        return "CACHE"
    elif "QUEUE-" in vm_name:
        return "QUEUE"
    elif "INFRA-" in vm_name:
        return "INFRA"
    elif "LEGACY-" in vm_name:
        return "LEGACY"
    else:
        return "DEV"

def get_env_type(vm_name):
    if "-PROD" in vm_name or "LDAP" in vm_name or "DNS" in vm_name:
        return "prod"
    elif "-STAGE" in vm_name:
        return "staging"
    elif "DEV" in vm_name:
        return "dev"
    else:
        return "infra"

def get_compliance_flags(vm_name):
    if "PAYMENT" in vm_name:
        return ["PCI", "SOC2", "HIPAA"]
    elif "-PROD" in vm_name:
        return ["SOC2"]
    else:
        return []

def seed_servers(client, project_id, dataset_name, csv_path):
    table_id = f"{project_id}.{dataset_name}.servers"
    print(f"Seeding '{table_id}' from CSV using batch load job...")
    
    rows_to_insert = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            vm_name = row["VM"]
            workload = classify_workload(vm_name)
            env = get_env_type(vm_name)
            comp = get_compliance_flags(vm_name)
            
            # Convert disk from MB to GB
            disk_gb = float(row["Provisioned MiB"]) / 1024.0
            
            # Map OS End of Life date (simulated)
            eol = date(2028, 12, 31)
            if "2008" in row["OS according to the configuration file"] or "18.04" in row["OS according to the configuration file"]:
                eol = date(2023, 10, 10)  # already EOL
            elif "7" in row["OS according to the configuration file"]:
                eol = date(2024, 6, 30)   # already EOL
                
            # Random last access days
            last_access = random.randint(1, 10)
            if "LEGACY" in vm_name or "OFF" in row["Powerstate"].upper():
                last_access = random.randint(95, 300)
                
            rows_to_insert.append({
                "server_id": f"srv-{idx:04d}",
                "name": vm_name,
                "vcpu": int(row["CPUs"]),
                "ram_gb": float(row["Memory"]),
                "disk_gb": round(disk_gb, 2),
                "os": row["OS according to the configuration file"],
                "os_version": "v1.0",
                "ip_address": row["IP Address"],
                "cluster": row["Cluster"],
                "datacenter": "Datacenter-US-East",
                "power_state": row["Powerstate"],
                "cpu_utilization_avg": float(row["CPU_Avg"]),
                "ram_utilization_avg": float(row["RAM_Avg"]),
                "disk_iops_avg": round(random.uniform(50, 500), 2) if row["Powerstate"] == "poweredOn" else 0.0,
                "network_throughput_mbps": round(random.uniform(1.0, 50.0), 2) if row["Powerstate"] == "poweredOn" else 0.0,
                "workload_type": workload,
                "app_owner": "infra-team@company.com",
                "environment": env,
                "source_platform": "vmware",
                "last_access_days": last_access,
                "eol_date": eol.isoformat(),
                "compliance_flags": comp,
                "tags": json.dumps({"owner": "infrastructure", "cost_center": "104"}),
                "project_id": project_id
            })
            
    # Batch load job (WRITE_TRUNCATE clears the table and loads data in one step)
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    try:
        load_job = client.load_table_from_json(rows_to_insert, table_id, job_config=job_config)
        load_job.result()  # Wait for job to complete
        print(f"Successfully batch loaded {len(rows_to_insert)} servers.")
        return rows_to_insert
    except Exception as e:
        print(f"Failed batch loading servers: {e}")
        sys.exit(1)

def seed_applications_and_databases(client, project_id, dataset_name, seeded_servers):
    app_table_id = f"{project_id}.{dataset_name}.applications"
    db_table_id = f"{project_id}.{dataset_name}.databases"
    
    print("Grouping servers into applications & databases...")
    
    # Map Server ID to Name for lookup
    srv_by_name = {s["name"]: s for s in seeded_servers}
    
    # Define Applications
    apps_data = [
        {
            "app_id": "app-0001",
            "name": "payment-gateway",
            "tier": "web",
            "tech_stack": ["nginx", "spring-boot", "java 17", "oracle"],
            "framework": "Spring",
            "language": "Java",
            "owner": "payments-team@company.com",
            "business_unit": "Finance",
            "business_criticality": 10,
            "sla_requirement": "99.99%",
            "compliance_flags": ["PCI", "SOC2", "HIPAA"],
            "data_classification": "restricted",
            "server_names": ["LB-NGINX", "WEBAPP-PROD", "APP-PAYMENT-PROD", "DB-ORACLE-PROD", "CACHE-REDIS-PROD", "QUEUE-RABBIT-PROD"],
            "annual_revenue_impact": 15000000.0,
            "user_count": 500000
        },
        {
            "app_id": "app-0002",
            "name": "order-processing",
            "tier": "app",
            "tech_stack": ["haproxy", "nodejs", "express", "mysql", "redis"],
            "framework": "Express",
            "language": "JavaScript",
            "owner": "orders-team@company.com",
            "business_unit": "Retail",
            "business_criticality": 8,
            "sla_requirement": "99.9%",
            "compliance_flags": ["SOC2"],
            "data_classification": "confidential",
            "server_names": ["LB-HAProxy", "APP-ORDER-PROD", "DB-MYSQL-STAGE", "DEV-TEST-VM"],
            "annual_revenue_impact": 5000000.0,
            "user_count": 120000
        },
        {
            "app_id": "app-0003",
            "name": "inventory-management",
            "tier": "app",
            "tech_stack": ["python", "django", "postgresql"],
            "framework": "Django",
            "language": "Python",
            "owner": "inventory-team@company.com",
            "business_unit": "Logistics",
            "business_criticality": 6,
            "sla_requirement": "99.5%",
            "compliance_flags": [],
            "data_classification": "internal",
            "server_names": ["APP-INVENTORY-PROD"],
            "annual_revenue_impact": 1200000.0,
            "user_count": 2500
        },
        {
            "app_id": "app-0004",
            "name": "shared-infrastructure",
            "tier": "middleware",
            "tech_stack": ["active-directory", "bind", "ntpd", "nagios"],
            "framework": "ActiveDirectory",
            "language": "Multiple",
            "owner": "infra-team@company.com",
            "business_unit": "IT Infrastructure",
            "business_criticality": 9,
            "sla_requirement": "99.999%",
            "compliance_flags": ["SOC2", "PCI"],
            "data_classification": "confidential",
            "server_names": ["INFRA-LDAP", "INFRA-DNS", "INFRA-NTP", "MONITORING-NAGIOS"],
            "annual_revenue_impact": 0.0,
            "user_count": 25000
        }
    ]
    
    app_rows = []
    db_rows = []
    db_idx = 1
    
    for app in apps_data:
        # Collect server IDs that belong to this app based on name prefixes
        matched_ids = []
        for name_prefix in app["server_names"]:
            for sname, sinfo in srv_by_name.items():
                if name_prefix in sname:
                    matched_ids.append(sinfo["server_id"])
                    
                    # If this server is a DB, also create a database record
                    if sinfo["workload_type"] == "DB":
                        db_engine = "oracle" if "ORACLE" in sname else "mysql" if "MYSQL" in sname else "unknown"
                        db_rows.append({
                            "db_id": f"db-{db_idx:04d}",
                            "name": f"db_{app['name']}_{db_engine}",
                            "db_engine": db_engine,
                            "version": "19c" if db_engine == "oracle" else "8.0",
                            "edition": "Enterprise" if db_engine == "oracle" else "Community",
                            "size_gb": float(sinfo["disk_gb"]) * 0.8, # DB size is subset of disk
                            "table_count": random.randint(20, 200),
                            "connection_count": int(sinfo["cpu_utilization_avg"] * 3),
                            "has_stored_procedures": True if db_engine == "oracle" else False,
                            "has_custom_extensions": False,
                            "has_linked_servers": False,
                            "replication_type": "async",
                            "backup_frequency": "daily",
                            "rpo_hours": 24.0,
                            "rto_hours": 4.0,
                            "licensing_model": "BYOL" if db_engine == "oracle" else "Included",
                            "server_id": sinfo["server_id"],
                            "project_id": project_id
                        })
                        db_idx += 1
                        
        app_rows.append({
            "app_id": app["app_id"],
            "name": app["name"],
            "tier": app["tier"],
            "tech_stack": app["tech_stack"],
            "framework": app["framework"],
            "language": app["language"],
            "owner": app["owner"],
            "business_unit": app["business_unit"],
            "business_criticality": app["business_criticality"],
            "sla_requirement": app["sla_requirement"],
            "compliance_flags": app["compliance_flags"],
            "data_classification": app["data_classification"],
            "server_ids": matched_ids,
            "annual_revenue_impact": app["annual_revenue_impact"],
            "user_count": app["user_count"],
            "project_id": project_id
        })
        
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    # Batch load Applications
    try:
        load_job = client.load_table_from_json(app_rows, app_table_id, job_config=job_config)
        load_job.result()
        print(f"Successfully batch loaded {len(app_rows)} applications.")
    except Exception as e:
        print(f"Failed batch loading apps: {e}")
        
    # Batch load Databases
    if db_rows:
        try:
            load_job = client.load_table_from_json(db_rows, db_table_id, job_config=job_config)
            load_job.result()
            print(f"Successfully batch loaded {len(db_rows)} databases.")
        except Exception as e:
            print(f"Failed batch loading databases: {e}")
            
    return app_rows, db_rows

def seed_dependencies(client, project_id, dataset_name, seeded_servers, seeded_apps, seeded_dbs, json_path):
    dep_table_id = f"{project_id}.{dataset_name}.app_dependencies"
    app_db_table_id = f"{project_id}.{dataset_name}.app_db_dependencies"
    shared_table_id = f"{project_id}.{dataset_name}.shared_services"
    
    print("Loading network dependencies from JSON...")
    
    with open(json_path, 'r') as f:
        flows = json.load(f)
        
    # Maps for lookup
    srv_by_ip = {s["ip_address"]: s for s in seeded_servers}
    app_by_srv = {}
    for app in seeded_apps:
        for srv_id in app["server_ids"]:
            app_by_srv[srv_id] = app
            
    db_by_srv = {db["server_id"]: db for db in seeded_dbs}
    
    dep_rows = []
    app_db_rows = []
    shared_rows = []
    
    shared_services_added = set()
    dep_idx = 1
    shared_idx = 1
    
    for flow in flows:
        src_ip = flow["source_ip"]
        dst_ip = flow["dest_ip"]
        
        src_srv = srv_by_ip.get(src_ip)
        dst_srv = srv_by_ip.get(dst_ip)
        
        if not src_srv or not dst_srv:
            continue
            
        src_app = app_by_srv.get(src_srv["server_id"])
        dst_app = app_by_srv.get(dst_srv["server_id"])
        
        # If destination is shared infrastructure
        if dst_srv["workload_type"] == "INFRA":
            if dst_srv["name"] not in shared_services_added:
                shared_services_added.add(dst_srv["name"])
                
                gcp_eq = "Cloud Identity / Managed Microsoft AD" if "LDAP" in dst_srv["name"] else "Cloud DNS" if "DNS" in dst_srv["name"] else "Google Public NTP" if "NTP" in dst_srv["name"] else "Cloud Monitoring"
                strategy = "hybrid-bridge" if "LDAP" in dst_srv["name"] or "DNS" in dst_srv["name"] else "migrate-first"
                
                shared_rows.append({
                    "service_id": f"sh-{shared_idx:04d}",
                    "service_name": dst_srv["name"],
                    "service_type": dst_srv["name"].split("-")[1] if "-" in dst_srv["name"] else "infra",
                    "ip_address": dst_ip,
                    "port": flow["dest_port"],
                    "used_by_count": 100, # default high usage
                    "migration_strategy": strategy,
                    "gcp_equivalent": gcp_eq,
                    "project_id": project_id
                })
                shared_idx += 1
            continue
            
        # App-to-App dependencies
        if src_app and dst_app and src_app["app_id"] != dst_app["app_id"]:
            dep_rows.append({
                "dep_id": f"dep-{dep_idx:04d}",
                "source_app_id": src_app["app_id"],
                "target_app_id": dst_app["app_id"],
                "protocol": flow["protocol"],
                "port": flow["dest_port"],
                "traffic_volume": "high" if flow["bytes_transferred"] > 10000000 else "medium" if flow["bytes_transferred"] > 1000000 else "low",
                "latency_sensitivity": "critical" if flow["dest_port"] in [1521, 6379, 5672] else "normal",
                "dependency_type": flow["dependency_type"],
                "data_flow_direction": "unidirectional",
                "project_id": project_id
            })
            dep_idx += 1
            
        # App-to-Database dependencies
        if src_app and dst_srv["workload_type"] == "DB":
            dst_db = db_by_srv.get(dst_srv["server_id"])
            if dst_db:
                app_db_rows.append({
                    "app_id": src_app["app_id"],
                    "db_id": dst_db["db_id"],
                    "connection_type": "direct" if "ORACLE" in dst_srv["name"] else "connection-pool",
                    "query_pattern": "OLTP"
                })
                
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    # Batch load App Dependencies
    if dep_rows:
        try:
            load_job = client.load_table_from_json(dep_rows, dep_table_id, job_config=job_config)
            load_job.result()
            print(f"Successfully batch loaded {len(dep_rows)} app-to-app dependencies.")
        except Exception as e:
            print(f"Failed batch loading app deps: {e}")
            
    # Batch load App-DB Dependencies
    if app_db_rows:
        # Remove duplicates
        unique_app_db = []
        seen = set()
        for row in app_db_rows:
            key = (row["app_id"], row["db_id"])
            if key not in seen:
                seen.add(key)
                unique_app_db.append(row)
                
        try:
            load_job = client.load_table_from_json(unique_app_db, app_db_table_id, job_config=job_config)
            load_job.result()
            print(f"Successfully batch loaded {len(unique_app_db)} app-to-db dependencies.")
        except Exception as e:
            print(f"Failed batch loading app-db deps: {e}")
            
    # Batch load Shared Services
    if shared_rows:
        try:
            load_job = client.load_table_from_json(shared_rows, shared_table_id, job_config=job_config)
            load_job.result()
            print(f"Successfully batch loaded {len(shared_rows)} shared services.")
        except Exception as e:
            print(f"Failed batch loading shared services: {e}")

def seed_project(client, project_id, dataset_name, server_count, app_count, db_count):
    table_id = f"{project_id}.{dataset_name}.projects"
    print(f"Seeding '{table_id}' using batch load...")
    
    project_rows = [
        {
            "project_id": "proj-migration-001",
            "name": "Enterprise Datacenter Migration",
            "client_name": "Acme Global Financial Corp",
            "description": "On-prem VMware cluster migration containing core e-commerce, transaction engines, and shared services to Google Cloud Platform.",
            "status": "discovery",
            "migration_type": "datacenter_exit",
            "source_platform": "vmware",
            "target_cloud": "gcp",
            "total_servers": server_count,
            "total_applications": app_count,
            "total_databases": db_count,
            "total_waves": 0,  # to be computed by agent
            "current_phase": "Discovery",
            "estimated_savings_pct": 52.4,
            "estimated_savings_annual": 1200000.0,
            "created_at": date.today().isoformat(),
            "updated_at": date.today().isoformat()
        }
    ]
    
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
    )
    
    try:
        load_job = client.load_table_from_json(project_rows, table_id, job_config=job_config)
        load_job.result()
        print("Successfully batch loaded migration project metadata.")
    except Exception as e:
        print(f"Failed batch loading project metadata: {e}")

def main():
    project_id, dataset = load_env_vars()
    
    # Paths for seed data files
    seed_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "seed")
    csv_path = os.path.join(seed_dir, "sample_rvtools.csv")
    json_path = os.path.join(seed_dir, "dependencies.json")
    
    # 1. Generate files locally
    os.makedirs(seed_dir, exist_ok=True)
    generate_rvtools_csv()
    generate_dependencies_json()
    
    # 2. Write to BigQuery
    client = bigquery.Client(project=project_id)
    
    # Note: DML deletes are removed to fit the BigQuery Sandbox free tier constraints.
    # We use WRITE_TRUNCATE in our load jobs to automatically overwrite and clear existing data!
    
    # Seed data
    seeded_servers = seed_servers(client, project_id, dataset, csv_path)
    if seeded_servers:
        seeded_apps, seeded_dbs = seed_applications_and_databases(client, project_id, dataset, seeded_servers)
        seed_dependencies(client, project_id, dataset, seeded_servers, seeded_apps, seeded_dbs, json_path)
        seed_project(client, project_id, dataset, len(seeded_servers), len(seeded_apps), len(seeded_dbs))
        print("\nDatabase seeding completed successfully! Ready for agent processing.")
    else:
        print("\nSeeding failed: could not load servers inventory.")
        sys.exit(1)

if __name__ == "__main__":
    main()
