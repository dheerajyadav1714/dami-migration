# agents/parsers/aws.py
from .base_parser import BaseParser
import pandas as pd
import re

class AWSParser(BaseParser):
    """Parser for AWS EC2 describe-instances or Migration Hub exports."""
    
    def parse(self, df: pd.DataFrame) -> list:
        normalized = []
        for idx, row in df.iterrows():
            # AWS column mapping logic
            inst_id = str(row.get("InstanceId", f"i-aws-{idx:08d}"))
            inst_name = str(row.get("Name", row.get("Tags.Name", inst_id)))
            
            # Parse memory e.g., "8 GiB" -> 8
            mem_raw = str(row.get("Memory", row.get("MemoryInfo.SizeInMiB", "4096")))
            mem_numbers = re.findall(r"[\d\.]+", mem_raw)
            mem_val = float(mem_numbers[0]) if mem_numbers else 4.0
            
            # If in MiB, convert to GB
            if "mib" in mem_raw.lower() or mem_val > 512:
                mem_gb = mem_val / 1024.0
            else:
                mem_gb = mem_val
                
            vcpu = int(row.get("vCPU", row.get("CpuOptions.CoreCount", 2)))
            
            # State mapping
            state = str(row.get("State", row.get("State.Name", "running"))).lower()
            power_state = "poweredOn" if state in ["running", "pending"] else "poweredOff"
            
            normalized.append({
                "server_id": inst_id,
                "name": inst_name,
                "vcpu": vcpu,
                "ram_gb": round(mem_gb, 2),
                "disk_gb": float(row.get("DiskGB", row.get("VolumeSize", 50.0))),
                "os": str(row.get("PlatformDetails", row.get("OS", "Linux/UNIX"))),
                "os_version": "unknown",
                "ip_address": str(row.get("PrivateIpAddress", row.get("PrivateIP", ""))),
                "cluster": str(row.get("VpcId", "AWS-VPC")),
                "datacenter": str(row.get("Placement.AvailabilityZone", row.get("AvailabilityZone", "us-east-1a"))),
                "power_state": power_state,
                "cpu_utilization_avg": float(row.get("CPUPercent", 25.0)),
                "ram_utilization_avg": float(row.get("RAMPercent", 45.0)),
                "workload_type": self._determine_workload(inst_name),
                "app_owner": "aws-admin@company.com",
                "environment": self._determine_environment(inst_name),
                "source_platform": "aws",
                "project_id": self.project_id
            })
            
        return normalized
