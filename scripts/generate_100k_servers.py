"""
Generate 100K-row synthetic server inventory CSV for GPU benchmark testing.

Matches the column format of data/seed/sample_rvtools.csv:
VM, CPUs, Memory, Provisioned MiB, OS according to the configuration file,
IP Address, Cluster, Powerstate, CPU_Avg, RAM_Avg

Usage:
    python scripts/generate_100k_servers.py
"""
import csv
import random
import os

# Configuration
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                           "data", "seed", "sample_servers_100k.csv")
ROW_COUNT = 100_000

# Realistic distributions
VM_PREFIXES = [
    "WEBAPP", "APP", "DB", "LB", "CACHE", "QUEUE", "BATCH", "API",
    "AUTH", "MONITOR", "LOG", "PROXY", "SEARCH", "ML", "ETL", "CRM",
    "ERP", "HR", "FINANCE", "REPORT", "STORAGE", "BACKUP", "DNS",
    "MAIL", "INFRA", "CI", "TEST", "STAGE", "DEV", "MGMT"
]

ENVIRONMENTS = ["PROD", "STAGE", "DEV", "QA", "UAT", "DR", "PERF"]
ENV_WEIGHTS = [35, 15, 20, 10, 8, 7, 5]

OS_LIST = [
    "Red Hat Enterprise Linux 8 (64-bit)",
    "Red Hat Enterprise Linux 9 (64-bit)",
    "Ubuntu Linux 22.04 (64-bit)",
    "Ubuntu Linux 20.04 (64-bit)",
    "Windows Server 2019 (64-bit)",
    "Windows Server 2022 (64-bit)",
    "CentOS Linux 7 (64-bit)",
    "SUSE Linux Enterprise 15 (64-bit)",
    "Oracle Linux 8 (64-bit)",
    "Debian GNU/Linux 11 (64-bit)",
]
OS_WEIGHTS = [20, 15, 18, 10, 12, 8, 5, 4, 5, 3]

CLUSTERS = [
    "Cluster-Production-US", "Cluster-Production-EU", "Cluster-Production-APAC",
    "Cluster-Staging-US", "Cluster-Dev-US", "Cluster-QA-US",
    "Cluster-DR-US", "Cluster-Performance-US", "Cluster-UAT-EU"
]

CPU_CONFIGS = [1, 2, 4, 8, 16, 32, 48, 64]
CPU_WEIGHTS = [3, 10, 25, 30, 20, 8, 3, 1]

MEMORY_CONFIGS = [2, 4, 8, 16, 32, 64, 128, 256, 512]
MEMORY_WEIGHTS = [2, 8, 20, 30, 20, 12, 5, 2, 1]


def generate_ip(idx):
    """Generate realistic private IP in 10.x.x.x range."""
    octet2 = 150 + (idx // 65536) % 6
    octet3 = (idx // 256) % 256
    octet4 = idx % 256
    return f"10.{octet2}.{octet3}.{octet4}"


def generate_row(idx):
    """Generate a single server row."""
    prefix = random.choice(VM_PREFIXES)
    env = random.choices(ENVIRONMENTS, weights=ENV_WEIGHTS, k=1)[0]
    seq = str(idx + 1).zfill(2 if idx < 100 else (3 if idx < 1000 else 5))
    vm_name = f"{prefix}-{env}-{seq}"
    
    cpus = random.choices(CPU_CONFIGS, weights=CPU_WEIGHTS, k=1)[0]
    memory = random.choices(MEMORY_CONFIGS, weights=MEMORY_WEIGHTS, k=1)[0]
    
    # Provisioned storage in MiB (correlated with server size)
    base_storage = memory * 1024 * random.uniform(2, 8)
    provisioned = int(base_storage + random.uniform(10000, 200000))
    
    os_name = random.choices(OS_LIST, weights=OS_WEIGHTS, k=1)[0]
    ip = generate_ip(idx)
    
    # Cluster correlated with environment
    if "PROD" in env or "DR" in env:
        cluster = random.choice([c for c in CLUSTERS if "Production" in c or "DR" in c])
    elif "STAGE" in env or "UAT" in env:
        cluster = random.choice([c for c in CLUSTERS if "Staging" in c or "UAT" in c])
    else:
        cluster = random.choice([c for c in CLUSTERS if "Dev" in c or "QA" in c or "Performance" in c])
    
    powerstate = random.choices(["poweredOn", "poweredOff"], weights=[92, 8], k=1)[0]
    
    # Utilization correlated with environment
    if "PROD" in env:
        cpu_avg = round(random.gauss(45, 20), 2)
        ram_avg = round(random.gauss(65, 15), 2)
    elif "DEV" in env or "QA" in env:
        cpu_avg = round(random.gauss(15, 10), 2)
        ram_avg = round(random.gauss(30, 15), 2)
    else:
        cpu_avg = round(random.gauss(30, 15), 2)
        ram_avg = round(random.gauss(50, 15), 2)
    
    cpu_avg = max(0.1, min(99.9, cpu_avg))
    ram_avg = max(0.5, min(99.9, ram_avg))
    
    return [vm_name, cpus, memory, provisioned, os_name, ip, cluster, powerstate, cpu_avg, ram_avg]


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    print(f"Generating {ROW_COUNT:,} synthetic server records...")
    
    headers = [
        "VM", "CPUs", "Memory", "Provisioned MiB",
        "OS according to the configuration file", "IP Address",
        "Cluster", "Powerstate", "CPU_Avg", "RAM_Avg"
    ]
    
    random.seed(42)  # Reproducible output
    
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for i in range(ROW_COUNT):
            writer.writerow(generate_row(i))
            
            if (i + 1) % 25000 == 0:
                print(f"  Generated {i + 1:,} / {ROW_COUNT:,} rows...")
    
    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"\n[DONE] Generated {ROW_COUNT:,} rows")
    print(f"  File: {OUTPUT_FILE}")
    print(f"  Size: {file_size / (1024*1024):.1f} MB")


if __name__ == "__main__":
    main()
