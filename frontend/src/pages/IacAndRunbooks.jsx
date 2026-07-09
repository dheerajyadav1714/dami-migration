import React, { useState } from 'react';
import api from '../lib/api';
import axios from 'axios';
import { 
  FileCode2, BookOpen, PlayCircle, Loader2, Copy, Check, Shield, Cpu
} from 'lucide-react';

const CLOUD_PROVIDERS = ['Google Cloud Platform', 'Multi-Cloud'];
const WAVE_GROUPS = ['Wave 1 — Rehost', 'Wave 2 — Managed Services', 'Wave 3 — Refactor'];

const ARTIFACT_TABS = [
  { key: 'runbook', label: '📖 Runbook', icon: BookOpen },
  { key: 'foundation', label: '🏗️ Foundation/LZ', icon: Shield },
  { key: 'workload', label: '🚀 Workload IaC', icon: FileCode2 },
  { key: 'dockerfile', label: '🐳 Dockerfile', icon: FileCode2 },
  { key: 'kubernetes', label: '☸️ Kubernetes YAML', icon: FileCode2 },
  { key: 'ansible', label: '🤖 Ansible Playbook', icon: FileCode2 },
  { key: 'cicd', label: '🔄 CI/CD Pipeline', icon: FileCode2 },
  { key: 'monitoring', label: '📊 Monitoring', icon: FileCode2 },
];

const ARTIFACT_CONTENT = {
  runbook: `# Migration Runbook — Wave 1: Rehost
## Pre-Migration Checklist
- [ ] Confirm VM snapshots taken on source
- [ ] Validate network connectivity to GCP VPC
- [ ] Ensure DNS TTL lowered to 60s (24h before cutover)
- [ ] Verify firewall rules allow required ports
- [ ] Confirm rollback plan documented and tested

## Migration Steps
1. **Stop source VMs** (maintenance window)
2. **Export VMDK** from vSphere
3. **Upload to Cloud Storage** using \`gsutil\`
4. **Import as GCE image** using \`gcloud compute images import\`
5. **Launch GCE instances** from Terraform plan
6. **Validate connectivity** — ping, curl, health checks
7. **Update DNS** to point to new GCE IPs
8. **Monitor for 48 hours** before decommission

## Rollback Plan
- Re-enable source VMs
- Revert DNS to original IPs
- TTL restoration to standard values`,

  foundation: `# Landing Zone — Foundation Terraform
resource "google_project" "migration_project" {
  name       = "dami-migration-prod"
  project_id = "dami-migration-prod"
  org_id     = var.org_id
  billing_account = var.billing_account
}

resource "google_compute_network" "migration_vpc" {
  name                    = "migration-vpc"
  project                 = google_project.migration_project.project_id
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "prod_subnet" {
  name          = "prod-subnet-us-central1"
  ip_cidr_range = "10.150.0.0/20"
  region        = "us-central1"
  network       = google_compute_network.migration_vpc.id
  
  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.4.0.0/14"
  }
}

resource "google_compute_firewall" "allow_internal" {
  name    = "allow-internal"
  network = google_compute_network.migration_vpc.id
  allow { protocol = "tcp" }
  allow { protocol = "udp" }
  allow { protocol = "icmp" }
  source_ranges = ["10.150.0.0/20"]
}`,

  workload: `# Workload IaC — Wave 1 Compute Instances
resource "google_compute_instance" "webapp_prod_01" {
  name         = "webapp-prod-01"
  machine_type = "e2-standard-4"
  zone         = "us-central1-a"
  
  boot_disk {
    initialize_params {
      image = "rhel-8-v20240515"
      size  = 80
    }
  }
  
  network_interface {
    network    = google_compute_network.migration_vpc.id
    subnetwork = google_compute_subnetwork.prod_subnet.id
  }
  
  tags = ["webapp", "prod", "wave-1"]
}

resource "google_compute_instance" "lb_nginx_01" {
  name         = "lb-nginx-01"
  machine_type = "e2-medium"
  zone         = "us-central1-a"
  
  boot_disk {
    initialize_params { image = "rhel-8-v20240515"; size = 40 }
  }
  
  network_interface {
    network    = google_compute_network.migration_vpc.id
    subnetwork = google_compute_subnetwork.prod_subnet.id
  }
  
  tags = ["loadbalancer", "prod", "wave-1"]
}`,

  dockerfile: `# Auto-generated Dockerfile for Payment App
FROM gcr.io/distroless/java17-debian12:nonroot

WORKDIR /app
COPY target/payment-engine.jar /app/app.jar
COPY config/ /app/config/

ENV JAVA_OPTS="-Xmx2g -Xms512m"
ENV SPRING_PROFILES_ACTIVE=gcp

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s \\
  CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["java", "-jar", "/app/app.jar"]`,

  kubernetes: `# Kubernetes Deployment — Payment App on GKE
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-engine
  namespace: prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-engine
  template:
    metadata:
      labels:
        app: payment-engine
    spec:
      containers:
      - name: payment-engine
        image: gcr.io/dami-migration/payment-engine:latest
        ports:
        - containerPort: 8080
        resources:
          requests: { cpu: "500m", memory: "1Gi" }
          limits: { cpu: "2", memory: "4Gi" }
        readinessProbe:
          httpGet: { path: /health, port: 8080 }
          initialDelaySeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: payment-engine-svc
  namespace: prod
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: payment-engine`,

  ansible: `# Ansible Playbook — Pre-Migration Server Prep
---
- name: Pre-Migration Server Preparation
  hosts: migration_targets
  become: yes
  
  tasks:
    - name: Update all packages
      yum:
        name: '*'
        state: latest
      when: ansible_os_family == "RedHat"
    
    - name: Install migration agent
      yum:
        name: google-cloud-ops-agent
        state: present
    
    - name: Configure ops-agent
      template:
        src: templates/ops-agent-config.yaml.j2
        dest: /etc/google-cloud-ops-agent/config.yaml
    
    - name: Start ops-agent
      systemd:
        name: google-cloud-ops-agent
        state: started
        enabled: yes
    
    - name: Create pre-migration snapshot
      command: >
        gcloud compute disks snapshot {{ inventory_hostname }}-disk
        --zone={{ zone }}
        --snapshot-names={{ inventory_hostname }}-pre-migration`,

  cicd: `# CI/CD Pipeline — Cloud Build
steps:
  # Build & Test
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/payment-engine:$SHORT_SHA', '.']
  
  # Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/payment-engine:$SHORT_SHA']
  
  # Deploy to GKE Staging
  - name: 'gcr.io/cloud-builders/gke-deploy'
    args:
    - run
    - --filename=k8s/
    - --image=gcr.io/$PROJECT_ID/payment-engine:$SHORT_SHA
    - --location=us-central1
    - --cluster=migration-cluster-staging
  
  # Run Integration Tests
  - name: 'gcr.io/cloud-builders/curl'
    args: ['-f', 'http://staging.internal/health']
    
  # Promote to Production (manual approval via Cloud Deploy)
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['deploy', 'releases', 'create', 'release-$SHORT_SHA',
           '--delivery-pipeline=payment-pipeline',
           '--region=us-central1']`,

  monitoring: `# Monitoring — Cloud Monitoring Alerting Policy
resource "google_monitoring_alert_policy" "high_cpu" {
  display_name = "High CPU - Migration Workloads"
  combiner     = "OR"
  
  conditions {
    display_name = "CPU > 80% for 5 min"
    condition_threshold {
      filter = "metric.type=\\"compute.googleapis.com/instance/cpu/utilization\\" AND resource.label.instance_id = starts_with(\\"webapp\\")"
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.email.name]
}

resource "google_monitoring_dashboard" "migration_dash" {
  dashboard_json = jsonencode({
    displayName = "D.A.M.I. Migration Health"
    gridLayout = { columns = 2, widgets = [] }
  })
}`,
};

const ROLLBACK_PLAN = `# Rollback Procedure — Emergency Recovery

## Trigger Conditions
- Health check failures > 3 consecutive
- Error rate > 5% for 10 minutes
- Latency P99 > 2000ms for 5 minutes
- Data integrity check failures

## Immediate Actions (0-5 min)
1. ⚠️ **Alert Stakeholders** — PagerDuty + Slack #migration-ops
2. 🔄 **DNS Failback** — Switch to on-prem IPs (TTL: 60s)
3. 🟢 **Re-enable Source VMs** — Power on original VMs
4. 🔒 **Freeze Changes** — No further deployments

## Validation (5-15 min)
- Confirm traffic routing back to on-prem
- Verify data consistency (last write timestamp)
- Check application health endpoints
- Monitor error rates

## Post-Mortem (Within 24h)
- Root cause analysis
- Update migration runbook
- Schedule re-attempt with fixes`;

export default function IacAndRunbooks() {
  const [activeTab, setActiveTab] = useState('runbook');
  const [selectedWave, setSelectedWave] = useState('Wave 1 — Rehost');
  const [selectedProvider, setSelectedProvider] = useState('Google Cloud Platform');
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [copied, setCopied] = useState(false);
  const [showRollback, setShowRollback] = useState(false);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.post('/api/run-agent', {
        project_id: 'proj-migration-001', phase: 'artifacts',
        wave_number: parseInt(selectedWave.charAt(5)) || 1
      });
      setGenerated(true);
    } catch {
      alert('Failed to trigger generation. Ensure the backend is running.');
    } finally {
      setGenerating(false);
    }
  };

  const copyCode = () => {
    navigator.clipboard.writeText(ARTIFACT_CONTENT[activeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getFileName = () => {
    const waveNum = selectedWave.charAt(5) || '1';
    const exts = { runbook: `.md`, foundation: `.tf`, workload: `.tf`, dockerfile: ``, kubernetes: `.yaml`, ansible: `.yaml`, cicd: `.yaml`, monitoring: `.tf` };
    return `wave_${waveNum}_${activeTab}${exts[activeTab]}`;
  };

  return (
    <main className="flex-1 bg-[#0b0f19] text-white flex flex-col h-full overflow-y-auto p-10 pb-20 custom-scrollbar relative z-10">
      <header className="mb-8">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-purple-400 tracking-tight mb-2">IaC & Runbooks</h1>
            <p className="text-slate-400 font-medium">Auto-generated Terraform, Kubernetes, Ansible, CI/CD, and monitoring configs for each wave.</p>
          </div>
          <button onClick={handleGenerate} disabled={generating} className="flex items-center gap-2 px-5 py-2.5 text-sm font-bold text-white bg-indigo-600 border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.3)] rounded-xl hover:bg-indigo-500 transition-all disabled:opacity-50">
            {generating ? <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</> : <><PlayCircle className="w-4 h-4" /> Generate Artifacts</>}
          </button>
        </div>
      </header>
      <div className="h-px bg-white/10 w-full mb-8" />

      {/* Selectors */}
      <div className="flex gap-4 mb-8">
        <select value={selectedWave} onChange={e => setSelectedWave(e.target.value)} className="bg-[#131826] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white">
          {WAVE_GROUPS.map(w => <option key={w}>{w}</option>)}
        </select>
        <select value={selectedProvider} onChange={e => setSelectedProvider(e.target.value)} className="bg-[#131826] border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white">
          {CLOUD_PROVIDERS.map(p => <option key={p}>{p}</option>)}
        </select>
      </div>

      {/* Artifact Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {ARTIFACT_TABS.map(t => (
          <button key={t.key} onClick={() => setActiveTab(t.key)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${activeTab === t.key ? 'bg-indigo-600/20 border border-indigo-500/30 text-indigo-300' : 'bg-[#131826] border border-white/5 text-slate-400 hover:text-white'}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Code Viewer */}
      <div className="bg-[#131826] rounded-xl border border-white/[0.05] shadow-lg overflow-hidden mb-8">
        <div className="flex items-center justify-between px-5 py-3 bg-slate-900/50 border-b border-white/5">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            {getFileName()}
          </div>
          <button onClick={copyCode} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors px-2 py-1 rounded-lg bg-slate-800 border border-white/10">
            {copied ? <><Check className="w-3.5 h-3.5 text-emerald-400" /> Copied!</> : <><Copy className="w-3.5 h-3.5" /> Copy</>}
          </button>
        </div>
        <pre className="p-5 text-xs font-mono text-slate-300 overflow-x-auto leading-relaxed max-h-[500px] custom-scrollbar">{ARTIFACT_CONTENT[activeTab]}</pre>
      </div>

      {/* Rollback Plan Generator */}
      <div className="bg-[#131826] rounded-xl p-6 border border-white/[0.05] shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white">🔄 Rollback Plan Generator</h3>
          <button onClick={() => setShowRollback(!showRollback)} className="bg-red-600/20 border border-red-500/30 text-red-400 px-4 py-2 rounded-lg text-sm font-bold hover:bg-red-600/30 transition-colors">
            {showRollback ? 'Hide' : 'Show'} Rollback Procedure
          </button>
        </div>
        {showRollback && (
          <pre className="bg-slate-900/50 rounded-xl p-5 text-xs font-mono text-slate-300 overflow-x-auto border border-white/5 max-h-[400px] custom-scrollbar whitespace-pre-wrap">{ROLLBACK_PLAN}</pre>
        )}
      </div>
    </main>
  );
}
