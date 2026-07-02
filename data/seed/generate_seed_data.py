# generate_seed_data.py
import csv
import json
import os
import random

SEED_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_rvtools_csv():
    file_path = os.path.join(SEED_DIR, "sample_rvtools.csv")
    print(f"Generating mock RVTools dataset at '{file_path}'...")
    
    # Headers matching typical RVTools vInfo sheet export
    headers = [
        "VM", "CPUs", "Memory", "Provisioned MiB", 
        "OS according to the configuration file", "IP Address", 
        "Cluster", "Powerstate", "CPU_Avg", "RAM_Avg"
    ]
    
    vms = []
    
    # Define some core application service definitions
    services = [
        {"prefix": "LB-NGINX", "cpus": 2, "mem_gb": 4, "disk_mb": 40960, "os": "Red Hat Enterprise Linux 8 (64-bit)", "state": "poweredOn", "cpu": 12.5, "ram": 45.0, "type": "LB"},
        {"prefix": "LB-HAProxy", "cpus": 2, "mem_gb": 4, "disk_mb": 40960, "os": "Ubuntu Linux 20.04 (64-bit)", "state": "poweredOn", "cpu": 8.0, "ram": 35.0, "type": "LB"},
        {"prefix": "WEBAPP-PROD", "cpus": 4, "mem_gb": 8, "disk_mb": 81920, "os": "Red Hat Enterprise Linux 8 (64-bit)", "state": "poweredOn", "cpu": 45.0, "ram": 72.0, "type": "WEB"},
        {"prefix": "WEBAPP-STAGE", "cpus": 2, "mem_gb": 4, "disk_mb": 61440, "os": "Red Hat Enterprise Linux 8 (64-bit)", "state": "poweredOn", "cpu": 15.0, "ram": 55.0, "type": "WEB"},
        {"prefix": "APP-PAYMENT-PROD", "cpus": 8, "mem_gb": 16, "disk_mb": 102400, "os": "Ubuntu Linux 22.04 (64-bit)", "state": "poweredOn", "cpu": 55.0, "ram": 78.0, "type": "APP"},
        {"prefix": "APP-ORDER-PROD", "cpus": 4, "mem_gb": 8, "disk_mb": 81920, "os": "Ubuntu Linux 22.04 (64-bit)", "state": "poweredOn", "cpu": 35.0, "ram": 65.0, "type": "APP"},
        {"prefix": "APP-INVENTORY-PROD", "cpus": 4, "mem_gb": 8, "disk_mb": 81920, "os": "Ubuntu Linux 20.04 (64-bit)", "state": "poweredOn", "cpu": 25.0, "ram": 58.0, "type": "APP"},
        {"prefix": "DB-ORACLE-PROD", "cpus": 16, "mem_gb": 64, "disk_mb": 512000, "os": "Red Hat Enterprise Linux 7 (64-bit)", "state": "poweredOn", "cpu": 65.0, "ram": 85.0, "type": "DB"},
        {"prefix": "DB-MYSQL-STAGE", "cpus": 4, "mem_gb": 16, "disk_mb": 102400, "os": "Ubuntu Linux 20.04 (64-bit)", "state": "poweredOn", "cpu": 18.0, "ram": 48.0, "type": "DB"},
        {"prefix": "CACHE-REDIS-PROD", "cpus": 4, "mem_gb": 16, "disk_mb": 40960, "os": "Ubuntu Linux 20.04 (64-bit)", "state": "poweredOn", "cpu": 22.0, "ram": 80.0, "type": "CACHE"},
        {"prefix": "QUEUE-RABBIT-PROD", "cpus": 4, "mem_gb": 8, "disk_mb": 61440, "os": "Ubuntu Linux 20.04 (64-bit)", "state": "poweredOn", "cpu": 15.0, "ram": 42.0, "type": "QUEUE"},
        {"prefix": "INFRA-LDAP", "cpus": 2, "mem_gb": 4, "disk_mb": 40960, "os": "Windows Server 2016 (64-bit)", "state": "poweredOn", "cpu": 10.0, "ram": 60.0, "type": "INFRA"},
        {"prefix": "INFRA-DNS", "cpus": 2, "mem_gb": 4, "disk_mb": 40960, "os": "Red Hat Enterprise Linux 8 (64-bit)", "state": "poweredOn", "cpu": 5.0, "ram": 30.0, "type": "INFRA"},
        {"prefix": "INFRA-NTP", "cpus": 1, "mem_gb": 2, "disk_mb": 20480, "os": "Ubuntu Linux 18.04 (64-bit)", "state": "poweredOn", "cpu": 2.0, "ram": 15.0, "type": "INFRA"},
        {"prefix": "MONITORING-NAGIOS", "cpus": 4, "mem_gb": 8, "disk_mb": 81920, "os": "Ubuntu Linux 20.04 (64-bit)", "state": "poweredOn", "cpu": 28.0, "ram": 62.0, "type": "INFRA"},
        {"prefix": "LEGACY-ARCHIVE", "cpus": 2, "mem_gb": 4, "disk_mb": 204800, "os": "Windows Server 2008 R2 (64-bit)", "state": "poweredOff", "cpu": 0.0, "ram": 0.0, "type": "LEGACY"}, # EOL OS, powered off (candidate for Retire)
        {"prefix": "DEV-TEST-VM", "cpus": 2, "mem_gb": 4, "disk_mb": 40960, "os": "CentOS 7 (64-bit)", "state": "poweredOn", "cpu": 5.0, "ram": 25.0, "type": "DEV"}
    ]
    
    # Generate 100 VMs by instantiating services and adding numeric suffixes
    random.seed(42)
    
    ip_counter = 10
    
    for i in range(1, 101):
        svc = random.choice(services)
        # Suffix
        suffix = f"{i:02d}"
        vm_name = f"{svc['prefix']}-{suffix}"
        
        # Calculate provisioned MiB
        prov_mb = svc['disk_mb'] + random.randint(-5120, 10240)
        
        # Generate IP
        ip_addr = f"10.150.23.{ip_counter}"
        ip_counter += 1
        if ip_counter > 250:
            ip_counter = 10
            
        # Add variability
        vms.append([
            vm_name,
            svc['cpus'],
            svc['mem_gb'],
            prov_mb,
            svc['os'],
            ip_addr,
            "Cluster-Production-US" if "-PROD" in vm_name else "Cluster-Staging-US" if "-STAGE" in vm_name else "Cluster-Infra-US",
            svc['state'],
            round(svc['cpu'] + random.uniform(-5.0, 5.0), 2) if svc['state'] == "poweredOn" else 0.0,
            round(svc['ram'] + random.uniform(-10.0, 5.0), 2) if svc['state'] == "poweredOn" else 0.0,
        ])
        
    with open(file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(vms)
        
    print(f"Generated {len(vms)} VMs in CSV successfully.")

def generate_dependencies_json():
    file_path = os.path.join(SEED_DIR, "dependencies.json")
    print(f"Generating mock dependencies JSON at '{file_path}'...")
    
    # We will generate mock network flows that match our generated VMs
    # We read the generated CSV to get IP addresses
    csv_path = os.path.join(SEED_DIR, "sample_rvtools.csv")
    if not os.path.exists(csv_path):
        # Generate CSV first if it doesn't exist
        generate_rvtools_csv()
        
    vms = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vms.append(row)
            
    # Group VMs by type
    lbs = [vm for vm in vms if "LB-" in vm['VM']]
    webs = [vm for vm in vms if "WEBAPP-" in vm['VM']]
    apps = [vm for vm in vms if "APP-" in vm['VM']]
    dbs = [vm for vm in vms if "DB-" in vm['VM']]
    caches = [vm for vm in vms if "CACHE-" in vm['VM']]
    queues = [vm for vm in vms if "QUEUE-" in vm['VM']]
    infras = [vm for vm in vms if "INFRA-" in vm['VM']]
    
    flows = []
    
    # Load Balancers to Web servers (HTTP:80, HTTPS:443)
    for lb in lbs:
        for web in webs[:5]:  # Link to first few web servers
            flows.append({
                "source_ip": lb['IP Address'],
                "dest_ip": web['IP Address'],
                "protocol": "HTTPS",
                "dest_port": 443,
                "bytes_transferred": random.randint(1000000, 50000000),
                "dependency_type": "sync"
            })
            
    # Web servers to App servers (HTTP:8080)
    for web in webs:
        # Each web server calls a couple of app servers
        targets = random.sample(apps, min(len(apps), 2))
        for app in targets:
            flows.append({
                "source_ip": web['IP Address'],
                "dest_ip": app['IP Address'],
                "protocol": "HTTP",
                "dest_port": 8080,
                "bytes_transferred": random.randint(500000, 20000000),
                "dependency_type": "sync"
            })
            
    # App servers to Databases (SQL ports)
    for app in apps:
        # App payment calls Oracle DB, others call MySQL/etc.
        if "PAYMENT" in app['VM']:
            target_dbs = [db for db in dbs if "ORACLE" in db['VM']]
            port = 1521
            proto = "Oracle Net"
        else:
            target_dbs = [db for db in dbs if "MYSQL" in db['VM'] or "ORACLE" in db['VM']]
            port = 3306 if "MYSQL" in target_dbs[0]['VM'] else 1521
            proto = "MySQL Protocol" if port == 3306 else "Oracle Net"
            
        if target_dbs:
            db = random.choice(target_dbs)
            flows.append({
                "source_ip": app['IP Address'],
                "dest_ip": db['IP Address'],
                "protocol": proto,
                "dest_port": port,
                "bytes_transferred": random.randint(200000, 10000000),
                "dependency_type": "sync"
            })
            
    # App servers to Cache (Redis)
    for app in apps:
        if caches:
            cache = random.choice(caches)
            flows.append({
                "source_ip": app['IP Address'],
                "dest_ip": cache['IP Address'],
                "protocol": "TCP",
                "dest_port": 6379,
                "bytes_transferred": random.randint(100000, 5000000),
                "dependency_type": "sync"
            })
            
    # App servers to Message Queue (RabbitMQ)
    for app in apps:
        if queues:
            queue = random.choice(queues)
            flows.append({
                "source_ip": app['IP Address'],
                "dest_ip": queue['IP Address'],
                "protocol": "AMQP",
                "dest_port": 5672,
                "bytes_transferred": random.randint(50000, 2000000),
                "dependency_type": "async"
            })
            
    # Outward dependencies on shared infra (LDAP, DNS, NTP)
    ldap_servers = [vm for vm in infras if "LDAP" in vm['VM']]
    dns_servers = [vm for vm in infras if "DNS" in vm['VM']]
    ntp_servers = [vm for vm in infras if "NTP" in vm['VM']]
    
    for vm in vms:
        # Every VM uses DNS
        for dns in dns_servers:
            flows.append({
                "source_ip": vm['IP Address'],
                "dest_ip": dns['IP Address'],
                "protocol": "UDP",
                "dest_port": 53,
                "bytes_transferred": random.randint(1000, 50000),
                "dependency_type": "infra"
            })
        # Every VM uses NTP
        for ntp in ntp_servers:
            flows.append({
                "source_ip": vm['IP Address'],
                "dest_ip": ntp['IP Address'],
                "protocol": "UDP",
                "dest_port": 123,
                "bytes_transferred": random.randint(100, 5000),
                "dependency_type": "infra"
            })
        # Active servers use LDAP for authentication
        if vm['Powerstate'] == "poweredOn" and ldap_servers:
            ldap = random.choice(ldap_servers)
            flows.append({
                "source_ip": vm['IP Address'],
                "dest_ip": ldap['IP Address'],
                "protocol": "LDAP",
                "dest_port": 389,
                "bytes_transferred": random.randint(5000, 200000),
                "dependency_type": "infra"
            })
            
    with open(file_path, 'w') as f:
        json.dump(flows, f, indent=2)
        
    print(f"Generated {len(flows)} network dependency flows in JSON successfully.")

if __name__ == "__main__":
    os.makedirs(SEED_DIR, exist_ok=True)
    generate_rvtools_csv()
    generate_dependencies_json()
    print("All seed data generated successfully!")
