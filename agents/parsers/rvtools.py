# agents/parsers/rvtools.py
from .base_parser import BaseParser
import pandas as pd

class RVToolsParser(BaseParser):
    """Parser for VMware RVTools exports (vInfo tab)."""
    
    def parse(self, df: pd.DataFrame) -> list:
        normalized = []
        for idx, row in df.iterrows():
            vm_name = str(row.get("VM", f"vm-{idx:04d}"))
            
            # Map standard RVTools columns
            cpus = int(row.get("CPUs", 2))
            ram_mb = float(row.get("Memory", 4096.0))
            ram_gb = ram_mb if "Memory" not in df.columns or df["Memory"].mean() < 1000 else ram_mb / 1024.0
            
            disk_mb = float(row.get("Provisioned MiB", 50000.0))
            disk_gb = disk_mb / 1024.0
            
            # Extract standard info
            normalized.append({
                "server_id": f"srv-rv-{idx:05d}",
                "name": vm_name,
                "vcpu": cpus,
                "ram_gb": round(ram_gb, 2),
                "disk_gb": round(disk_gb, 2),
                "os": str(row.get("OS according to the configuration file", "unknown")),
                "os_version": "unknown",
                "ip_address": str(row.get("IP Address", "")),
                "cluster": str(row.get("Cluster", "Unknown-Cluster")),
                "datacenter": str(row.get("Datacenter", "On-Premises")),
                "power_state": str(row.get("Powerstate", "poweredOn")),
                "cpu_utilization_avg": float(row.get("CPU_Avg", 10.0)),
                "ram_utilization_avg": float(row.get("RAM_Avg", 40.0)),
                "workload_type": self._determine_workload(vm_name),
                "app_owner": "vmware-admin@company.com",
                "environment": self._determine_environment(vm_name),
                "source_platform": "vmware",
                "project_id": self.project_id
            })
            
        return normalized
