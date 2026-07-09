# agents/migration_advisor.py
"""
D.A.M.I. Database & App Migration Advisor

Provides AI-powered migration path recommendations:
- Oracle → AlloyDB/CloudSQL/BMS routing
- MySQL → CloudSQL/AlloyDB routing
- Stored procedure complexity scoring
- App modernization recommendations (GKE, Cloud Run, etc.)
- Migration effort estimation in person-weeks

No other tool tells you "this Oracle 19c DB with 400 stored procedures
will take 12 weeks to migrate to AlloyDB" — they just say "use Cloud SQL".
"""
import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()


# Migration path decision matrix
DB_MIGRATION_PATHS = {
    ("oracle", "Enterprise"): [
        {
            "target": "AlloyDB for PostgreSQL",
            "icon": "🟢",
            "fit": "Best",
            "effort": "High",
            "description": "Fully managed PostgreSQL-compatible DB with 100x faster analytics. "
                           "Eliminates Oracle license costs entirely.",
            "pros": ["No Oracle license cost", "100x faster analytical queries", "PostgreSQL ecosystem", "Managed HA"],
            "cons": ["Requires PL/SQL → PL/pgSQL conversion", "Application ORM changes", "Data type mapping"],
            "conditions": {"max_stored_procs": True, "max_size_gb": 10000},
        },
        {
            "target": "Bare Metal Solution (BMS)",
            "icon": "🟡",
            "fit": "Good",
            "effort": "Low",
            "description": "Lift-and-shift Oracle on dedicated bare metal. License portability, "
                           "minimal changes, but no license cost savings.",
            "pros": ["Zero app changes", "License portability (BYOL)", "Same Oracle version", "Fast migration"],
            "cons": ["No license savings", "Higher infra cost", "Not cloud-native"],
            "conditions": {"has_stored_procs": True, "complex": True},
        },
        {
            "target": "Cloud SQL for PostgreSQL",
            "icon": "🔵",
            "fit": "Moderate",
            "effort": "High",
            "description": "Managed PostgreSQL with automatic backups. Good for smaller Oracle DBs "
                           "with fewer stored procedures.",
            "pros": ["No Oracle license", "Managed service", "Cost-effective", "Auto-backups"],
            "cons": ["Limited to 64TB", "Requires full conversion", "No RAC equivalent"],
            "conditions": {"max_size_gb": 5000, "max_stored_procs": False},
        },
    ],
    ("oracle", "Standard"): [
        {
            "target": "AlloyDB for PostgreSQL",
            "icon": "🟢", "fit": "Best", "effort": "Medium",
            "description": "Ideal for Standard Edition migration — simpler conversion, big savings.",
            "pros": ["Eliminate license", "Columnar engine", "Managed HA"],
            "cons": ["PL/SQL conversion needed"],
            "conditions": {},
        },
        {
            "target": "Cloud SQL for PostgreSQL",
            "icon": "🟢", "fit": "Good", "effort": "Medium",
            "description": "Simple managed PostgreSQL for smaller Oracle Standard workloads.",
            "pros": ["Low cost", "Managed", "Auto-backups"],
            "cons": ["Limited to 64TB"],
            "conditions": {},
        },
    ],
    ("mysql", "Community"): [
        {
            "target": "Cloud SQL for MySQL",
            "icon": "🟢", "fit": "Best", "effort": "Low",
            "description": "Drop-in managed MySQL. Minimal changes, auto-backups, read replicas.",
            "pros": ["Near-zero changes", "Managed HA", "Auto-backups", "Read replicas"],
            "cons": ["Max 64TB", "Some MySQL features differ"],
            "conditions": {},
        },
        {
            "target": "AlloyDB for PostgreSQL",
            "icon": "🔵", "fit": "Good", "effort": "Medium",
            "description": "Upgrade path to PostgreSQL with superior analytics performance.",
            "pros": ["Better performance", "Columnar analytics", "PostgreSQL ecosystem"],
            "cons": ["Requires MySQL → PostgreSQL conversion"],
            "conditions": {},
        },
    ],
}

# App modernization paths
APP_MODERNIZATION_PATHS = {
    "Java": {
        "current": "Java VM-based",
        "recommendations": [
            {"target": "Cloud Run", "fit": "Best", "effort": "Medium",
             "description": "Containerize Java app and deploy serverless. Auto-scaling, pay-per-use."},
            {"target": "GKE Autopilot", "fit": "Good", "effort": "Medium",
             "description": "Kubernetes-managed deployment for complex Java microservices."},
            {"target": "Compute Engine", "fit": "Lift-Shift", "effort": "Low",
             "description": "Direct VM migration with minimal changes."},
        ]
    },
    ".NET": {
        "current": ".NET Framework/Core",
        "recommendations": [
            {"target": "Cloud Run", "fit": "Best", "effort": "Medium",
             "description": "Containerize .NET app. Cloud Run supports .NET natively."},
            {"target": "GKE Autopilot", "fit": "Good", "effort": "Medium",
             "description": "Kubernetes for .NET microservices architecture."},
            {"target": "Compute Engine (Windows)", "fit": "Lift-Shift", "effort": "Low",
             "description": "Windows VM migration. Requires Windows Server license."},
        ]
    },
    "Python": {
        "current": "Python Application",
        "recommendations": [
            {"target": "Cloud Run", "fit": "Best", "effort": "Low",
             "description": "Containerize and deploy serverless. Ideal for Python apps."},
            {"target": "Cloud Functions", "fit": "Good", "effort": "Low",
             "description": "Serverless functions for event-driven Python workloads."},
            {"target": "App Engine", "fit": "Good", "effort": "Low",
             "description": "PaaS deployment for standard Python web frameworks."},
        ]
    },
    "Node.js": {
        "current": "Node.js Application",
        "recommendations": [
            {"target": "Cloud Run", "fit": "Best", "effort": "Low",
             "description": "Containerize Node.js app with auto-scaling."},
            {"target": "Cloud Functions", "fit": "Good", "effort": "Low",
             "description": "Event-driven serverless for Node.js APIs."},
        ]
    },
}


class MigrationAdvisor:
    """Database and App Migration Advisor Agent."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "cohort-2-497207")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
        self.client = bigquery.Client(project=self.project_id)
    
    def analyze_all(self) -> dict:
        """Run full migration analysis for all databases and applications."""
        db_analysis = self._analyze_databases()
        app_analysis = self._analyze_applications()
        
        total_effort = sum(d.get("estimated_effort_weeks", 0) for d in db_analysis)
        total_effort += sum(a.get("estimated_effort_weeks", 0) for a in app_analysis)
        
        return {
            "databases": db_analysis,
            "applications": app_analysis,
            "summary": {
                "total_databases": len(db_analysis),
                "total_applications": len(app_analysis),
                "total_estimated_effort_weeks": total_effort,
                "total_estimated_effort_months": round(total_effort / 4, 1),
                "oracle_count": len([d for d in db_analysis if d.get("engine") == "oracle"]),
                "mysql_count": len([d for d in db_analysis if d.get("engine") == "mysql"]),
            }
        }
    
    def _analyze_databases(self) -> list:
        """Analyze all databases and recommend migration paths."""
        query = f"""
            SELECT d.db_id, d.name, d.db_engine, d.edition, d.version, d.size_gb,
                   d.has_stored_procedures, d.has_linked_servers, d.has_custom_extensions,
                   d.connection_count, d.table_count, d.rto_hours, d.rpo_hours,
                   d.server_id, s.name AS server_name, s.environment
            FROM `{self.project_id}.{self.dataset}.databases` d
            JOIN `{self.project_id}.{self.dataset}.servers` s ON d.server_id = s.server_id
            ORDER BY d.db_engine, d.size_gb DESC
        """
        try:
            df = self.client.query(query).to_dataframe()
        except Exception:
            return []
        
        results = []
        for _, row in df.iterrows():
            engine = str(row.get("db_engine", "")).lower()
            edition = str(row.get("edition", ""))
            
            # Get migration paths for this engine/edition combo
            key = (engine, edition)
            paths = DB_MIGRATION_PATHS.get(key, DB_MIGRATION_PATHS.get((engine, "Community"), []))
            
            # Calculate complexity score
            complexity = self._calculate_db_complexity(row)
            effort = self._estimate_db_effort(row, complexity)
            
            results.append({
                "db_id": row.get("db_id"),
                "db_name": row.get("name"),
                "engine": engine,
                "edition": edition,
                "version": row.get("version"),
                "size_gb": float(row.get("size_gb", 0) or 0),
                "server_name": row.get("server_name"),
                "environment": row.get("environment"),
                "has_stored_procedures": bool(row.get("has_stored_procedures")),
                "has_linked_servers": bool(row.get("has_linked_servers")),
                "has_custom_extensions": bool(row.get("has_custom_extensions")),
                "connection_count": int(row.get("connection_count", 0) or 0),
                "table_count": int(row.get("table_count", 0) or 0),
                "rto_hours": float(row.get("rto_hours", 0) or 0),
                "rpo_hours": float(row.get("rpo_hours", 0) or 0),
                "complexity_score": complexity["score"],
                "complexity_level": complexity["level"],
                "complexity_factors": complexity["factors"],
                "migration_paths": paths,
                "recommended_path": paths[0] if paths else None,
                "estimated_effort_weeks": effort,
            })
        
        return results
    
    def _calculate_db_complexity(self, row) -> dict:
        """Calculate migration complexity score (0-100)."""
        score = 0
        factors = []
        
        # Engine complexity
        engine = str(row.get("db_engine", "")).lower()
        if engine == "oracle":
            score += 30
            factors.append("Oracle proprietary syntax (+30)")
        elif engine in ("sqlserver", "sql server"):
            score += 20
            factors.append("SQL Server T-SQL conversion (+20)")
        
        # Stored procedures
        if row.get("has_stored_procedures"):
            score += 25
            factors.append("Stored procedures require conversion (+25)")
        
        # Linked servers
        if row.get("has_linked_servers"):
            score += 15
            factors.append("Linked servers / DB Links (+15)")
        
        # Custom extensions
        if row.get("has_custom_extensions"):
            score += 10
            factors.append("Custom extensions / packages (+10)")
        
        # Size factor
        size = float(row.get("size_gb", 0) or 0)
        if size > 1000:
            score += 10
            factors.append(f"Large database: {size:.0f}GB (+10)")
        elif size > 500:
            score += 5
            factors.append(f"Medium database: {size:.0f}GB (+5)")
        
        # High connections (complex app coupling)
        conns = int(row.get("connection_count", 0) or 0)
        if conns > 100:
            score += 5
            factors.append(f"High connection count: {conns} (+5)")
        
        # Strict RTO/RPO
        rto = float(row.get("rto_hours", 0) or 0)
        if 0 < rto < 1:
            score += 5
            factors.append(f"Strict RTO: {rto}h (+5)")
        
        score = min(score, 100)
        
        if score >= 70:
            level = "HIGH"
        elif score >= 40:
            level = "MEDIUM"
        else:
            level = "LOW"
        
        return {"score": score, "level": level, "factors": factors}
    
    def _estimate_db_effort(self, row, complexity) -> float:
        """Estimate migration effort in person-weeks."""
        base = 1  # Minimum 1 week for any migration
        
        engine = str(row.get("db_engine", "")).lower()
        if engine == "oracle":
            base = 4  # Oracle migrations take longer
        elif engine in ("sqlserver", "sql server"):
            base = 3
        
        # Scale by complexity
        if complexity["score"] >= 70:
            multiplier = 3.0
        elif complexity["score"] >= 40:
            multiplier = 2.0
        else:
            multiplier = 1.0
        
        # Scale by size
        size = float(row.get("size_gb", 0) or 0)
        if size > 1000:
            multiplier *= 1.5
        elif size > 500:
            multiplier *= 1.2
        
        return round(base * multiplier, 1)
    
    def _analyze_applications(self) -> list:
        """Analyze applications and recommend modernization paths."""
        query = f"""
            SELECT app_id, name, language, framework, tech_stack, tier,
                   business_criticality, user_count, annual_revenue_impact,
                   data_classification, owner, server_ids
            FROM `{self.project_id}.{self.dataset}.applications`
            ORDER BY business_criticality DESC
        """
        try:
            df = self.client.query(query).to_dataframe()
        except Exception:
            return []
        
        results = []
        for _, row in df.iterrows():
            lang = str(row.get("language", "")).strip()
            framework = str(row.get("framework", "")).strip()
            
            # Get modernization paths
            paths = APP_MODERNIZATION_PATHS.get(lang, {}).get("recommendations", [
                {"target": "Cloud Run", "fit": "Good", "effort": "Medium",
                 "description": f"Containerize {lang} app on Cloud Run."},
                {"target": "Compute Engine", "fit": "Lift-Shift", "effort": "Low",
                 "description": "Direct VM migration with minimal changes."},
            ])
            
            # Estimate effort
            criticality = int(row.get("business_criticality", 3) or 3)
            effort = 2 if criticality >= 4 else 1  # High criticality needs more testing
            
            results.append({
                "app_id": row.get("app_id"),
                "name": row.get("name"),
                "language": lang,
                "framework": framework,
                "tech_stack": list(row.get("tech_stack", [])) if isinstance(row.get("tech_stack"), list) else [],
                "tier": row.get("tier"),
                "business_criticality": criticality,
                "user_count": int(row.get("user_count", 0) or 0),
                "annual_revenue_impact": float(row.get("annual_revenue_impact", 0) or 0),
                "owner": row.get("owner"),
                "modernization_paths": paths,
                "recommended_path": paths[0] if paths else None,
                "estimated_effort_weeks": effort,
            })
        
        return results
