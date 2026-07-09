# agents/parsers/device42.py
from .base_parser import BaseParser
import pandas as pd

class Device42Parser(BaseParser):
    """Parser for Device42 JSON/CSV exports."""
    
    def parse(self, df: pd.DataFrame) -> list:
        normalized = []
        for idx, row in df.iterrows():
            d42_id = str(row.get("device_id", row.get("id", f"d42-{idx:05d}")))
            name = str(row.get("name", row.get("device", f"server-{idx:04d}")))
            
            # Hardware
            vcpu = int(row.get("cpucore", row.get("cpu_core_count", 2)))
            
            # RAM in MB usually
            ram_mb = float(row.get("ram", 4096.0))
            ram_gb = ram_mb / 1024.0 if ram_mb > 512 else ram_mb
            
            normalized.append({
                "server_id": d42_id,
                "name": name,
                "vcpu": vcpu,
                "ram_gb": round(ram_gb, 2),
                "disk_gb": float(row.get("hdd_size", row.get("hddcount", 100.0))),
                "os": str(row.get("os", row.get("os_name", "Linux"))),
                "os_version": str(row.get("osver", row.get("os_version", "unknown"))),
                "ip_address": str(row.get("ip_addresses", "")),
                "cluster": str(row.get("building", row.get("site", "D42-Datacenter"))),
                "datacenter": str(row.get("room", "On-Premises")),
                "power_state": "poweredOn",  # D42 doesn't always export power state easily
                "cpu_utilization_avg": 25.0, # Placeholder
                "ram_utilization_avg": 40.0, # Placeholder
                "workload_type": self._determine_workload(name),
                "app_owner": "d42-admin@company.com",
                "environment": self._determine_environment(name),
                "source_platform": "device42",
                "project_id": self.project_id
            })
            
        return normalized
