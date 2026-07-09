# agents/validation_agent.py
"""
D.A.M.I. Validation & Go/No-Go Engine

Auto-generates migration-specific validation checklists from assessment data:
- Per-wave contextual checks (not generic templates)
- Traffic light Go/No-Go decision
- Tracks validation progress
- Flags blockers automatically

Nobody else auto-generates migration-specific validation checklists from
actual assessment data. This is the "bridge" between planning and execution.
"""
import os
import json
from datetime import datetime
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()


# Checklist item templates with conditions
CHECKLIST_TEMPLATES = [
    {
        "id": "backup_snapshot",
        "category": "Data Protection",
        "title": "Full backup/snapshot taken for all servers in this wave",
        "critical": True,
        "condition": "always",  # Always required
        "detail": "Ensure VM-level snapshots and database backups are current (< 24 hours old)",
    },
    {
        "id": "rollback_plan",
        "category": "Data Protection",
        "title": "Rollback procedure documented and tested",
        "critical": True,
        "condition": "always",
        "detail": "Verify rollback steps have been tested in non-production environment",
    },
    {
        "id": "dns_ttl",
        "category": "Network",
        "title": "DNS TTL reduced to 60 seconds",
        "critical": False,
        "condition": "has_public_facing",
        "detail": "Reduce TTL for public-facing services to enable fast DNS failover",
    },
    {
        "id": "firewall_rules",
        "category": "Network",
        "title": "GCP firewall rules verified and tested",
        "critical": True,
        "condition": "has_dependencies",
        "detail": "Ensure all required ports/protocols are open between migrated and remaining servers",
    },
    {
        "id": "db_snapshot",
        "category": "Database",
        "title": "Database snapshots created and verified",
        "critical": True,
        "condition": "has_databases",
        "detail": "Point-in-time recovery snapshots for all databases in this wave",
    },
    {
        "id": "db_replication",
        "category": "Database",
        "title": "Database replication lag verified < threshold",
        "critical": True,
        "condition": "has_databases",
        "detail": "Ensure replication is caught up before cutover window",
    },
    {
        "id": "license_compliance",
        "category": "Compliance",
        "title": "License compliance verified for commercial software",
        "critical": True,
        "condition": "has_commercial_license",
        "detail": "Oracle/SQL Server/Windows Server licenses validated for cloud deployment",
    },
    {
        "id": "stakeholder_notify",
        "category": "Communication",
        "title": "Stakeholders notified of migration window",
        "critical": True,
        "condition": "high_criticality",
        "detail": "Business owners and dependent team leads notified of planned downtime",
    },
    {
        "id": "monitoring_setup",
        "category": "Operations",
        "title": "Cloud monitoring and alerting configured",
        "critical": False,
        "condition": "always",
        "detail": "GCP Cloud Monitoring dashboards and alert policies ready for migrated workloads",
    },
    {
        "id": "performance_baseline",
        "category": "Operations",
        "title": "Performance baseline metrics recorded",
        "critical": False,
        "condition": "always",
        "detail": "CPU, memory, disk IOPS, and network throughput baselines documented for comparison",
    },
    {
        "id": "iam_permissions",
        "category": "Security",
        "title": "IAM roles and service accounts configured",
        "critical": True,
        "condition": "always",
        "detail": "Principle of least privilege applied to all service accounts and user roles",
    },
    {
        "id": "encryption_verified",
        "category": "Security",
        "title": "Data encryption at rest and in transit verified",
        "critical": True,
        "condition": "has_compliance",
        "detail": "CMEK or default encryption configured per compliance requirements",
    },
    {
        "id": "app_testing",
        "category": "Testing",
        "title": "Application smoke tests passed on target",
        "critical": True,
        "condition": "has_applications",
        "detail": "Critical application flows verified on GCP infrastructure before cutover",
    },
    {
        "id": "load_testing",
        "category": "Testing",
        "title": "Load testing completed on target infrastructure",
        "critical": False,
        "condition": "high_criticality",
        "detail": "Simulate production-level traffic to verify GCP capacity and performance",
    },
    {
        "id": "dependency_check",
        "category": "Dependencies",
        "title": "Cross-wave dependency conflicts resolved",
        "critical": True,
        "condition": "has_dependencies",
        "detail": "Ensure no circular dependencies between this wave and subsequent waves",
    },
]


class ValidationAgent:
    """Generates contextual validation checklists from assessment data."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "cohort-2-497207")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
        self.client = bigquery.Client(project=self.project_id)
    
    def generate_wave_checklists(self) -> list:
        """Generate validation checklists for all waves."""
        waves = self._get_waves()
        wave_details = self._get_wave_details()
        
        checklists = []
        for wave in waves:
            wave_id = wave.get("wave_id", "")
            details = wave_details.get(wave_id, {})
            checklist = self._build_checklist(wave, details)
            checklists.append(checklist)
        
        return checklists
    
    def get_go_nogo_status(self, wave_id: str, checked_items: list) -> dict:
        """
        Calculate Go/No-Go status for a wave based on checked items.
        Returns traffic light status.
        """
        waves = self._get_waves()
        wave = next((w for w in waves if w.get("wave_id") == wave_id), {})
        details = self._get_wave_details().get(wave_id, {})
        checklist = self._build_checklist(wave, details)
        
        total = len(checklist["items"])
        critical_items = [i for i in checklist["items"] if i["critical"]]
        critical_checked = [i for i in critical_items if i["id"] in checked_items]
        non_critical = [i for i in checklist["items"] if not i["critical"]]
        non_critical_checked = [i for i in non_critical if i["id"] in checked_items]
        
        all_critical_passed = len(critical_checked) == len(critical_items)
        all_passed = len(checked_items) >= total
        
        if all_passed:
            status = "GO"
            color = "green"
            message = "All validation checks passed. Migration wave is approved to proceed."
        elif all_critical_passed:
            status = "WARN"
            color = "yellow"
            message = f"All critical checks passed. {len(non_critical) - len(non_critical_checked)} non-critical items incomplete."
        else:
            blocked = [i for i in critical_items if i["id"] not in checked_items]
            status = "BLOCKED"
            color = "red"
            message = f"{len(blocked)} critical checks incomplete. Migration cannot proceed."
        
        return {
            "status": status,
            "color": color,
            "message": message,
            "total_checks": total,
            "checked": len(checked_items),
            "critical_total": len(critical_items),
            "critical_passed": len(critical_checked),
            "blockers": [i["title"] for i in critical_items if i["id"] not in checked_items],
        }
    
    def _get_waves(self) -> list:
        """Get wave data from BQ."""
        try:
            q = f"""SELECT wave_id, wave_name, total_servers, risk_level, 
                           estimated_duration_days, sequence_order
                    FROM `{self.project_id}.{self.dataset}.waves` 
                    ORDER BY sequence_order, wave_id"""
            return self.client.query(q).to_dataframe().to_dict("records")
        except Exception:
            return []
    
    def _get_wave_details(self) -> dict:
        """Get detailed context for each wave (servers, DBs, apps, dependencies)."""
        details = {}
        
        # Get wave workloads (which servers are in each wave)
        try:
            q = f"""SELECT ww.wave_id, ww.server_id, 
                           s.os, s.environment, s.vcpu, s.workload_type,
                           s.compliance_flags
                    FROM `{self.project_id}.{self.dataset}.wave_workloads` ww
                    JOIN `{self.project_id}.{self.dataset}.servers` s ON ww.server_id = s.server_id"""
            df = self.client.query(q).to_dataframe()
            
            for wave_id, group in df.groupby("wave_id"):
                details[wave_id] = {
                    "server_count": len(group),
                    "has_public_facing": any(str(w).lower() in ["web", "api", "frontend"] 
                                            for w in group.get("workload_type", [])),
                    "has_databases": False,  # Will be updated below
                    "has_applications": True,  # Assume yes if servers exist
                    "has_dependencies": len(group) > 1,
                    "has_commercial_license": False,  # Will be updated below
                    "has_compliance": any(len(c) > 0 if isinstance(c, list) else False 
                                        for c in group.get("compliance_flags", [])),
                    "high_criticality": any(str(e).lower() == "production" 
                                           for e in group.get("environment", [])),
                    "server_ids": list(group["server_id"]),
                    "environments": list(group["environment"].unique()),
                    "os_types": list(group["os"].unique()) if "os" in group.columns else [],
                }
        except Exception as e:
            print(f"[Validation] Wave details query failed: {e}")
        
        # Check for databases in each wave
        try:
            q = f"""SELECT d.server_id, d.db_engine, d.licensing_model
                    FROM `{self.project_id}.{self.dataset}.databases` d"""
            db_df = self.client.query(q).to_dataframe()
            
            for wave_id, d in details.items():
                wave_servers = set(d.get("server_ids", []))
                wave_dbs = db_df[db_df["server_id"].isin(wave_servers)]
                if not wave_dbs.empty:
                    d["has_databases"] = True
                    d["db_engines"] = list(wave_dbs["db_engine"].unique())
                    d["has_commercial_license"] = any(
                        str(e).lower() in ["oracle", "sqlserver", "sql server"] 
                        for e in wave_dbs["db_engine"]
                    ) or any(
                        str(l).lower() == "byol" 
                        for l in wave_dbs["licensing_model"]
                    )
        except Exception:
            pass
        
        # Check for Windows Server licenses
        for wave_id, d in details.items():
            if any("windows" in str(os_type).lower() for os_type in d.get("os_types", [])):
                d["has_commercial_license"] = True
        
        return details
    
    def _build_checklist(self, wave: dict, details: dict) -> dict:
        """Build contextual checklist for a specific wave."""
        wave_id = wave.get("wave_id", "unknown")
        wave_name = wave.get("wave_name", "Unknown Wave")
        
        items = []
        for template in CHECKLIST_TEMPLATES:
            condition = template["condition"]
            
            # Check if this checklist item applies to this wave
            if condition == "always":
                applies = True
            elif condition in details:
                applies = bool(details.get(condition, False))
            else:
                applies = False
            
            if applies:
                items.append({
                    "id": template["id"],
                    "category": template["category"],
                    "title": template["title"],
                    "detail": template["detail"],
                    "critical": template["critical"],
                    "checked": False,
                })
        
        # Calculate initial status
        critical = [i for i in items if i["critical"]]
        
        return {
            "wave_id": wave_id,
            "wave_name": wave_name,
            "total_servers": wave.get("total_servers", 0),
            "risk_level": wave.get("risk_level", "Medium"),
            "items": items,
            "total_checks": len(items),
            "critical_checks": len(critical),
            "context": {
                "has_databases": details.get("has_databases", False),
                "has_commercial_license": details.get("has_commercial_license", False),
                "environments": details.get("environments", []),
                "db_engines": details.get("db_engines", []),
            },
        }
