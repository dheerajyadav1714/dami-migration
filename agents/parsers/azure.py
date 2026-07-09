# agents/parsers/azure.py
from .base_parser import BaseParser
import pandas as pd
import re

class AzureParser(BaseParser):
    """Parser for Azure Resource Graph / VM exports."""
    
    def parse(self, df: pd.DataFrame) -> list:
        normalized = []
        for idx, row in df.iterrows():
            vm_id = str(row.get("Id", row.get("resourceId", f"az-vm-{idx:08d}")))
            vm_name = str(row.get("Name", row.get("name", f"az-vm-{idx:04d}")))
            
            # Azure usually provides hardwareProfile.vmSize e.g., "Standard_D4s_v3"
            # We simulate extraction if raw vCPU/RAM not present
            vm_size = str(row.get("HardwareProfile", row.get("vmSize", "Standard_D2s_v3")))
            
            vcpu = int(row.get("vCPU", 2))
            # Try to infer from name (e.g. D4s has 4 vCPUs)
            if "vCPU" not in df.columns:
                match = re.search(r'_([A-Z]*\d+)[a-z]*_', vm_size)
                if match:
                    num_str = "".join(filter(str.isdigit, match.group(1)))
                    if num_str:
                        vcpu = int(num_str)
            
            ram_gb = float(row.get("MemoryGB", vcpu * 4.0)) # Rough heuristic
            
            # State
            status = str(row.get("PowerState", row.get("status", "running"))).lower()
            power_state = "poweredOn" if "running" in status else "poweredOff"
            
            normalized.append({
                "server_id": vm_id.split("/")[-1] if "/" in vm_id else vm_id,
                "name": vm_name,
                "vcpu": vcpu,
                "ram_gb": round(ram_gb, 2),
                "disk_gb": float(row.get("OsDiskSizeGB", 128.0)),
                "os": str(row.get("OsType", "Windows")),
                "os_version": str(row.get("OsVersion", "unknown")),
                "ip_address": str(row.get("PrivateIpAddress", "")),
                "cluster": str(row.get("ResourceGroup", row.get("resourceGroup", "Azure-RG"))),
                "datacenter": str(row.get("Location", row.get("location", "eastus"))),
                "power_state": power_state,
                "cpu_utilization_avg": float(row.get("CPUPercent", 30.0)),
                "ram_utilization_avg": float(row.get("RAMPercent", 50.0)),
                "workload_type": self._determine_workload(vm_name),
                "app_owner": "azure-admin@company.com",
                "environment": self._determine_environment(vm_name),
                "source_platform": "azure",
                "project_id": self.project_id
            })
            
        return normalized
