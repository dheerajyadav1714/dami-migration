# agents/license_advisor.py
"""
D.A.M.I. License Risk Intelligence Agent

Detects license compliance risks during cloud migration:
- Oracle per-core licensing cost explosions
- SQL Server edition mapping risks
- Windows Server licensing model changes
- Open-source migration opportunities

This is the #1 cause of cloud migration cost overruns.
No other migration tool detects or warns about this.
"""
import os
import json
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

# Oracle per-core license costs (annual, USD)
ORACLE_LICENSE_COSTS = {
    "Enterprise": {
        "named_user_plus": 950,   # per Named User Plus
        "processor": 47_500,       # per Processor (core)
        "description": "Oracle Database Enterprise Edition",
    },
    "Standard": {
        "named_user_plus": 350,
        "processor": 17_500,
        "description": "Oracle Database Standard Edition 2",
    },
}

# SQL Server per-core license costs (annual, USD)
SQLSERVER_LICENSE_COSTS = {
    "Enterprise": {
        "per_core_pack": 15_123,  # 2-core pack
        "description": "SQL Server Enterprise (per 2-core pack)",
    },
    "Standard": {
        "per_core_pack": 3_945,
        "description": "SQL Server Standard (per 2-core pack)",
    },
}

# GCP machine type vCPU mapping (common types)
MACHINE_VCPUS = {
    "e2-standard-2": 2, "e2-standard-4": 4, "e2-standard-8": 8, "e2-standard-16": 16,
    "n2-standard-2": 2, "n2-standard-4": 4, "n2-standard-8": 8, "n2-standard-16": 16,
    "n2-standard-32": 32, "n2-standard-48": 48, "n2-standard-64": 64,
    "c2-standard-4": 4, "c2-standard-8": 8, "c2-standard-16": 16,
    "o2-standard-16-192": 16, "o2-standard-32-384": 32,
    "m1-megamem-96": 96, "m1-ultramem-160": 160,
}

# Oracle core factor for Intel/AMD (used for on-prem to cloud core mapping)
# Oracle uses a 0.5 core factor for Intel/AMD processors
ORACLE_CORE_FACTOR = 0.5


class LicenseAdvisor:
    """License Risk Intelligence Agent for cloud migration."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "cohort-2-497207")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
        self.client = bigquery.Client(project=self.project_id)
    
    def analyze_all_licenses(self) -> dict:
        """
        Run full license risk analysis across all databases and servers.
        Returns comprehensive risk report.
        """
        db_risks = self._analyze_database_licenses()
        os_risks = self._analyze_os_licenses()
        
        # Calculate totals
        total_annual_risk = sum(r.get("annual_cost_delta", 0) for r in db_risks)
        total_annual_risk += sum(r.get("annual_cost_delta", 0) for r in os_risks)
        
        high_risk = [r for r in db_risks + os_risks if r.get("risk_level") == "HIGH"]
        medium_risk = [r for r in db_risks + os_risks if r.get("risk_level") == "MEDIUM"]
        
        return {
            "database_risks": db_risks,
            "os_risks": os_risks,
            "summary": {
                "total_databases_analyzed": len(db_risks),
                "total_servers_analyzed": len(os_risks),
                "high_risk_count": len(high_risk),
                "medium_risk_count": len(medium_risk),
                "total_annual_cost_risk_usd": total_annual_risk,
                "total_annual_cost_risk_inr": total_annual_risk * 84,
            },
            "recommendations": self._generate_recommendations(db_risks, os_risks),
        }
    
    def _analyze_database_licenses(self) -> list:
        """Analyze database license risks by joining databases + servers + target_architecture."""
        query = f"""
            SELECT 
                d.db_id,
                d.db_engine,
                d.edition,
                d.licensing_model,
                d.version,
                d.server_id,
                d.size_gb,
                d.has_stored_procedures,
                d.has_linked_servers,
                d.has_custom_extensions,
                d.connection_count,
                d.table_count,
                s.name AS server_name,
                s.vcpu AS onprem_vcpus,
                s.os,
                s.environment,
                t.target_machine_type,
                t.target_gcp_service,
                t.cost_estimate_monthly
            FROM `{self.project_id}.{self.dataset}.databases` d
            JOIN `{self.project_id}.{self.dataset}.servers` s ON d.server_id = s.server_id
            LEFT JOIN `{self.project_id}.{self.dataset}.target_architecture` t 
                ON d.server_id = t.source_component_id
            ORDER BY d.db_engine, d.edition
        """
        df = self.client.query(query).to_dataframe()
        
        risks = []
        for _, row in df.iterrows():
            risk = self._calculate_db_license_risk(row)
            if risk:
                risks.append(risk)
        
        return risks
    
    def _calculate_db_license_risk(self, row) -> dict:
        """Calculate license cost risk for a single database."""
        db_engine = str(row.get("db_engine", "")).lower()
        edition = str(row.get("edition", ""))
        licensing_model = str(row.get("licensing_model", ""))
        onprem_vcpus = int(row.get("onprem_vcpus", 0) or 0)
        target_machine = str(row.get("target_machine_type", ""))
        target_service = str(row.get("target_gcp_service", ""))
        
        # Get target vCPUs
        target_vcpus = MACHINE_VCPUS.get(target_machine, onprem_vcpus)
        
        risk = {
            "db_id": row.get("db_id"),
            "server_name": row.get("server_name"),
            "server_id": row.get("server_id"),
            "db_engine": db_engine,
            "edition": edition,
            "version": row.get("version"),
            "licensing_model": licensing_model,
            "size_gb": float(row.get("size_gb", 0) or 0),
            "has_stored_procedures": bool(row.get("has_stored_procedures")),
            "has_linked_servers": bool(row.get("has_linked_servers")),
            "has_custom_extensions": bool(row.get("has_custom_extensions")),
            "onprem_vcpus": onprem_vcpus,
            "target_machine_type": target_machine,
            "target_gcp_service": target_service,
            "target_vcpus": target_vcpus,
            "environment": row.get("environment"),
        }
        
        if db_engine == "oracle":
            risk.update(self._calc_oracle_risk(edition, onprem_vcpus, target_vcpus, target_service))
        elif db_engine in ("sqlserver", "sql server", "mssql"):
            risk.update(self._calc_sqlserver_risk(edition, onprem_vcpus, target_vcpus))
        elif db_engine == "mysql":
            risk.update(self._calc_mysql_risk(edition, target_service))
        else:
            risk["risk_level"] = "LOW"
            risk["risk_type"] = "No commercial license"
            risk["annual_cost_onprem"] = 0
            risk["annual_cost_cloud"] = 0
            risk["annual_cost_delta"] = 0
            risk["recommendations"] = ["Open-source database — no license cost risk"]
        
        return risk
    
    def _calc_oracle_risk(self, edition, onprem_vcpus, target_vcpus, target_service) -> dict:
        """Calculate Oracle-specific license risk."""
        costs = ORACLE_LICENSE_COSTS.get(edition, ORACLE_LICENSE_COSTS["Enterprise"])
        per_core = costs["processor"]
        
        # On-prem: Oracle uses core factor 0.5 for Intel/AMD
        onprem_cores = max(1, int(onprem_vcpus * ORACLE_CORE_FACTOR))
        onprem_annual = onprem_cores * per_core
        
        # Cloud: depends on target service
        if target_service and "bare metal" in target_service.lower():
            # BMS allows license portability — same cost as on-prem
            cloud_cores = onprem_cores
            cloud_annual = onprem_annual
            risk_type = "License Portable (BMS)"
        else:
            # Standard GCE: Oracle counts all vCPUs, core factor 0.5
            cloud_cores = max(1, int(target_vcpus * ORACLE_CORE_FACTOR))
            cloud_annual = cloud_cores * per_core
            risk_type = "vCPU Expansion Risk"
        
        delta = cloud_annual - onprem_annual
        
        if delta > 100_000:
            risk_level = "HIGH"
        elif delta > 25_000:
            risk_level = "MEDIUM"
        elif delta > 0:
            risk_level = "LOW"
        else:
            risk_level = "SAFE"
        
        recommendations = []
        if delta > 0:
            recommendations.append(f"Use Bare Metal Solution for license portability (saves ${delta:,.0f}/yr)")
            recommendations.append(f"Reduce target to {onprem_vcpus} vCPUs to match on-prem core count")
        if edition == "Enterprise":
            recommendations.append("Evaluate migration to AlloyDB PostgreSQL (eliminate Oracle license entirely)")
            recommendations.append("Consider Oracle SE2 if Enterprise features not required")
        recommendations.append("Engage Oracle LMS team for cloud licensing validation")
        
        return {
            "risk_level": risk_level,
            "risk_type": risk_type,
            "onprem_cores_licensed": onprem_cores,
            "cloud_cores_licensed": cloud_cores,
            "per_core_annual": per_core,
            "annual_cost_onprem": onprem_annual,
            "annual_cost_cloud": cloud_annual,
            "annual_cost_delta": delta,
            "recommendations": recommendations,
        }
    
    def _calc_sqlserver_risk(self, edition, onprem_vcpus, target_vcpus) -> dict:
        """Calculate SQL Server-specific license risk."""
        costs = SQLSERVER_LICENSE_COSTS.get(edition, SQLSERVER_LICENSE_COSTS["Standard"])
        per_pack = costs["per_core_pack"]
        
        # SQL Server: minimum 4 core packs (2 cores each)
        onprem_packs = max(2, (onprem_vcpus + 1) // 2)
        cloud_packs = max(2, (target_vcpus + 1) // 2)
        
        onprem_annual = onprem_packs * per_pack
        cloud_annual = cloud_packs * per_pack
        delta = cloud_annual - onprem_annual
        
        risk_level = "HIGH" if delta > 50_000 else "MEDIUM" if delta > 10_000 else "LOW" if delta > 0 else "SAFE"
        
        recommendations = []
        if delta > 0:
            recommendations.append(f"Use Azure Hybrid Benefit or SQL Server on GCE with BYOL")
            recommendations.append(f"Right-size to {onprem_vcpus} vCPUs (saves ${delta:,.0f}/yr)")
        recommendations.append("Evaluate Cloud SQL for SQL Server (license included in pricing)")
        recommendations.append("Consider migration to Cloud SQL PostgreSQL or AlloyDB")
        
        return {
            "risk_level": risk_level,
            "risk_type": "Core Pack Expansion",
            "onprem_cores_licensed": onprem_packs * 2,
            "cloud_cores_licensed": cloud_packs * 2,
            "per_core_annual": per_pack,
            "annual_cost_onprem": onprem_annual,
            "annual_cost_cloud": cloud_annual,
            "annual_cost_delta": delta,
            "recommendations": recommendations,
        }
    
    def _calc_mysql_risk(self, edition, target_service) -> dict:
        """Calculate MySQL-specific license risk (usually safe)."""
        return {
            "risk_level": "SAFE",
            "risk_type": "Community Edition — No License Cost",
            "onprem_cores_licensed": 0,
            "cloud_cores_licensed": 0,
            "per_core_annual": 0,
            "annual_cost_onprem": 0,
            "annual_cost_cloud": 0,
            "annual_cost_delta": 0,
            "recommendations": [
                "MySQL Community Edition has no license cost",
                f"Target service: {target_service or 'Cloud SQL for MySQL'} — fully managed",
                "Consider AlloyDB for PostgreSQL compatibility with better performance",
            ],
        }
    
    def _analyze_os_licenses(self) -> list:
        """Analyze Windows Server license risks."""
        query = f"""
            SELECT 
                s.server_id,
                s.name AS server_name,
                s.os,
                s.vcpu,
                s.environment,
                t.target_machine_type,
                t.target_gcp_service
            FROM `{self.project_id}.{self.dataset}.servers` s
            LEFT JOIN `{self.project_id}.{self.dataset}.target_architecture` t 
                ON s.server_id = t.source_component_id
            WHERE LOWER(s.os) LIKE '%windows%'
            ORDER BY s.vcpu DESC
        """
        try:
            df = self.client.query(query).to_dataframe()
        except Exception:
            return []
        
        risks = []
        for _, row in df.iterrows():
            vcpu = int(row.get("vcpu", 0) or 0)
            target_vcpus = MACHINE_VCPUS.get(str(row.get("target_machine_type", "")), vcpu)
            
            # Windows Server Datacenter: ~$6,155/yr per 2-core pack (min 8 cores)
            onprem_packs = max(4, (vcpu + 1) // 2)
            cloud_packs = max(4, (target_vcpus + 1) // 2)
            per_pack = 6_155
            
            onprem_annual = onprem_packs * per_pack
            cloud_annual = cloud_packs * per_pack
            delta = cloud_annual - onprem_annual
            
            risk_level = "HIGH" if delta > 20_000 else "MEDIUM" if delta > 5_000 else "LOW" if delta > 0 else "SAFE"
            
            risks.append({
                "server_id": row.get("server_id"),
                "server_name": row.get("server_name"),
                "os": row.get("os"),
                "db_engine": "windows_server",
                "edition": "Datacenter",
                "onprem_vcpus": vcpu,
                "target_vcpus": target_vcpus,
                "risk_level": risk_level,
                "risk_type": "Windows Server License",
                "annual_cost_onprem": onprem_annual,
                "annual_cost_cloud": cloud_annual,
                "annual_cost_delta": delta,
                "environment": row.get("environment"),
                "recommendations": [
                    "Use GCE with Windows Server license included in pricing",
                    "Consider migrating to Linux to eliminate Windows license cost",
                    "Use premium images with license included (pay-as-you-go)",
                ],
            })
        
        return risks
    
    def _generate_recommendations(self, db_risks, os_risks) -> list:
        """Generate top-level strategic recommendations."""
        recs = []
        
        oracle_risks = [r for r in db_risks if r.get("db_engine") == "oracle"]
        if oracle_risks:
            total_oracle_risk = sum(r.get("annual_cost_delta", 0) for r in oracle_risks)
            recs.append({
                "priority": "CRITICAL",
                "title": "Oracle License Cost Risk",
                "detail": f"{len(oracle_risks)} Oracle databases with ${total_oracle_risk:,.0f}/yr potential cost increase",
                "action": "Evaluate Bare Metal Solution for license portability or AlloyDB PostgreSQL migration",
            })
        
        high_risks = [r for r in db_risks + os_risks if r.get("risk_level") == "HIGH"]
        if high_risks:
            recs.append({
                "priority": "HIGH",
                "title": f"{len(high_risks)} High-Risk License Items",
                "detail": "These items could cause significant budget overruns if not addressed before migration",
                "action": "Review each HIGH risk item and implement recommended mitigations",
            })
        
        sp_dbs = [r for r in db_risks if r.get("has_stored_procedures")]
        if sp_dbs:
            recs.append({
                "priority": "MEDIUM",
                "title": "Stored Procedure Migration Complexity",
                "detail": f"{len(sp_dbs)} databases have stored procedures requiring conversion",
                "action": "Assess stored procedure complexity before committing to open-source migration",
            })
        
        recs.append({
            "priority": "INFO",
            "title": "License Compliance Audit",
            "detail": "Schedule license compliance review with vendor before migration cutover",
            "action": "Engage Oracle LMS and/or Microsoft SAM teams for pre-migration audit",
        })
        
        return recs
