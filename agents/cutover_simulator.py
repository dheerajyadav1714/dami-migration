# agents/cutover_simulator.py
"""
D.A.M.I. Cutover Simulation & Runbook Engine

Simulates migration cutover for each wave:
- Estimates downtime windows based on data volume and network bandwidth
- Generates minute-by-minute cutover runbook
- Calculates rollback time
- Identifies parallel vs sequential tasks

Nobody else simulates the actual cutover — they just say "migrate".
"""
import os
import math
from datetime import datetime, timedelta
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()


class CutoverSimulator:
    """Simulate migration cutover and generate runbooks."""
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "cohort-2-497207")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
        self.client = bigquery.Client(project=self.project_id)
    
    def simulate_wave(self, wave_id: str) -> dict:
        """Run cutover simulation for a specific wave."""
        wave = self._get_wave(wave_id)
        servers = self._get_wave_servers(wave_id)
        databases = self._get_wave_databases(servers)
        
        # Calculate phase timings
        phases = self._calculate_phases(servers, databases)
        runbook = self._generate_runbook(wave, servers, databases, phases)
        
        total_minutes = sum(p["duration_min"] for p in phases)
        rollback_minutes = self._estimate_rollback(servers, databases)
        
        return {
            "wave_id": wave_id,
            "wave_name": wave.get("wave_name", "Unknown"),
            "total_servers": len(servers),
            "total_databases": len(databases),
            "phases": phases,
            "runbook": runbook,
            "total_duration_minutes": total_minutes,
            "total_duration_hours": round(total_minutes / 60, 1),
            "rollback_time_minutes": rollback_minutes,
            "rollback_time_hours": round(rollback_minutes / 60, 1),
            "recommended_window": self._recommend_window(total_minutes),
            "data_volume_gb": sum(float(s.get("disk_gb", 0) or 0) for s in servers),
            "db_volume_gb": sum(float(d.get("size_gb", 0) or 0) for d in databases),
        }
    
    def simulate_all_waves(self) -> list:
        """Simulate cutover for all waves."""
        waves = self._get_all_waves()
        results = []
        for wave in waves:
            result = self.simulate_wave(wave["wave_id"])
            results.append(result)
        return results
    
    def _get_wave(self, wave_id):
        try:
            q = f"SELECT * FROM `{self.project_id}.{self.dataset}.waves` WHERE wave_id = '{wave_id}'"
            df = self.client.query(q).to_dataframe()
            return df.iloc[0].to_dict() if not df.empty else {}
        except Exception:
            return {}
    
    def _get_all_waves(self):
        try:
            q = f"SELECT wave_id, wave_name, total_servers, risk_level FROM `{self.project_id}.{self.dataset}.waves` ORDER BY wave_id"
            return self.client.query(q).to_dataframe().to_dict("records")
        except Exception:
            return []
    
    def _get_wave_servers(self, wave_id):
        try:
            q = f"""SELECT s.* FROM `{self.project_id}.{self.dataset}.wave_workloads` ww
                    JOIN `{self.project_id}.{self.dataset}.servers` s ON ww.server_id = s.server_id
                    WHERE ww.wave_id = '{wave_id}'"""
            return self.client.query(q).to_dataframe().to_dict("records")
        except Exception:
            return []
    
    def _get_wave_databases(self, servers):
        server_ids = [s.get("server_id", "") for s in servers]
        if not server_ids:
            return []
        try:
            ids_str = ",".join(f"'{s}'" for s in server_ids)
            q = f"SELECT * FROM `{self.project_id}.{self.dataset}.databases` WHERE server_id IN ({ids_str})"
            return self.client.query(q).to_dataframe().to_dict("records")
        except Exception:
            return []
    
    def _calculate_phases(self, servers, databases) -> list:
        """Calculate cutover phase durations."""
        total_disk_gb = sum(float(s.get("disk_gb", 0) or 0) for s in servers)
        total_db_gb = sum(float(d.get("size_gb", 0) or 0) for d in databases)
        server_count = len(servers)
        
        # Assume 500 Mbps network throughput for initial sync
        transfer_rate_gbps = 0.5  # GB/s  
        transfer_rate_gpm = transfer_rate_gbps * 60  # GB/min
        
        phases = [
            {
                "phase": "Pre-Checks",
                "description": "Verify backups, DNS TTL, monitoring, stakeholder notification",
                "duration_min": 15,
                "parallel": True,
                "icon": "🔍",
            },
            {
                "phase": "Quiesce Applications",
                "description": f"Stop application services on {server_count} servers, drain connections",
                "duration_min": max(5, server_count * 2),
                "parallel": True,
                "icon": "⏸️",
            },
            {
                "phase": "Final Data Sync",
                "description": f"Delta sync {total_disk_gb:.0f}GB disk + {total_db_gb:.0f}GB database data",
                "duration_min": max(10, int((total_disk_gb * 0.05 + total_db_gb * 0.1) / transfer_rate_gpm) + 5),
                "parallel": False,
                "icon": "📡",
            },
        ]
        
        if databases:
            phases.append({
                "phase": "Database Cutover",
                "description": f"Switch {len(databases)} database(s) to cloud target, verify replication",
                "duration_min": max(10, len(databases) * 8),
                "parallel": False,
                "icon": "🗄️",
            })
        
        phases.extend([
            {
                "phase": "DNS/LB Switch",
                "description": "Update DNS records, reconfigure load balancers to cloud targets",
                "duration_min": 5,
                "parallel": True,
                "icon": "🌐",
            },
            {
                "phase": "Smoke Tests",
                "description": "Execute application smoke tests, verify connectivity and data integrity",
                "duration_min": max(10, server_count * 3),
                "parallel": True,
                "icon": "🧪",
            },
            {
                "phase": "Monitoring Validation",
                "description": "Verify Cloud Monitoring alerts, check error rates, confirm SLA metrics",
                "duration_min": 10,
                "parallel": True,
                "icon": "📊",
            },
            {
                "phase": "Go/No-Go Decision",
                "description": "Stakeholder sign-off: proceed or initiate rollback",
                "duration_min": 5,
                "parallel": False,
                "icon": "✅",
            },
        ])
        
        return phases
    
    def _generate_runbook(self, wave, servers, databases, phases) -> list:
        """Generate minute-by-minute runbook steps."""
        runbook = []
        current_time = 0  # T+0
        
        for phase in phases:
            start = current_time
            end = current_time + phase["duration_min"]
            
            runbook.append({
                "time": f"T+{start}min",
                "end_time": f"T+{end}min",
                "phase": phase["phase"],
                "description": phase["description"],
                "owner": self._assign_owner(phase["phase"]),
                "duration_min": phase["duration_min"],
                "icon": phase["icon"],
            })
            current_time = end
        
        return runbook
    
    def _estimate_rollback(self, servers, databases) -> int:
        """Estimate rollback time in minutes."""
        base = 15  # DNS revert + app restart
        db_time = len(databases) * 10  # Database failback
        server_time = len(servers) * 2  # VM revert
        return base + db_time + server_time
    
    def _recommend_window(self, total_minutes) -> dict:
        """Recommend maintenance window."""
        buffer = int(total_minutes * 0.5)  # 50% buffer
        window_hours = math.ceil((total_minutes + buffer) / 60)
        
        if total_minutes <= 60:
            day = "Saturday 02:00 - 04:00 UTC"
        elif total_minutes <= 180:
            day = "Saturday 01:00 - 05:00 UTC"
        else:
            day = "Saturday 00:00 - 08:00 UTC"
        
        return {
            "suggested_window": day,
            "minimum_hours": round(total_minutes / 60, 1),
            "recommended_hours": window_hours,
            "includes_buffer": f"{buffer} minutes ({buffer/total_minutes*100:.0f}%)",
        }
    
    def _assign_owner(self, phase_name) -> str:
        """Assign responsible team to each phase."""
        owners = {
            "Pre-Checks": "Migration Lead",
            "Quiesce Applications": "App Team",
            "Final Data Sync": "Infra Team",
            "Database Cutover": "DBA Team",
            "DNS/LB Switch": "Network Team",
            "Smoke Tests": "QA Team",
            "Monitoring Validation": "SRE Team",
            "Go/No-Go Decision": "Migration Lead",
        }
        return owners.get(phase_name, "Migration Lead")
