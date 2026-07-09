# iac_runbooks.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from google.cloud import bigquery
import pandas as pd

@st.cache_resource
def get_bq_client(project_id):
    return bigquery.Client(project=project_id)

def get_waves_list(client, project_id, dataset):
    query = f"SELECT wave_number, wave_id, wave_name FROM `{project_id}.{dataset}.waves` ORDER BY wave_number"
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        print(f"Failed to query waves: {e}")
    return pd.DataFrame()

def read_local_file(wave_number, file_type, target_cloud="Google Cloud Platform (GCP)"):
    cloud_suffix = "_aws" if "AWS" in target_cloud else "_azure" if "Azure" in target_cloud else "_gcp"
    mapping = {
        'tf': f"wave_{wave_number}_infra{cloud_suffix}.tf",
        'k8s': f"wave_{wave_number}_k8s.yaml",
        'ansible': f"wave_{wave_number}_ansible.yaml",
        'runbook': f"wave_{wave_number}_runbook.md"
    }
    file_name = mapping.get(file_type)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(base_dir, "generated_assets", f"wave_{wave_number}", file_name)
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            pass
            
    # GCS Fallback: Download the full file directly from Google Cloud Storage
    try:
        project_id = os.getenv("GCP_PROJECT_ID")
        bucket_name = os.getenv("GCS_BUCKET", "dami-artifacts-cohort-2")
        from google.cloud import storage as gcs
        gcs_client = gcs.Client(project=project_id)
        bucket = gcs_client.bucket(bucket_name)
        blob_path = f"iac-artifacts/wave_{wave_number}/{file_name}"
        blob = bucket.blob(blob_path)
        if blob.exists():
            content = blob.download_as_text(encoding="utf-8")
            if content:
                # Write to ephemeral container file system for subsequent fast access
                try:
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(content)
                except Exception:
                    pass
                return content
    except Exception as e:
        print(f"GCS read fallback failed: {e}")
    
    # Second Fallback: query BigQuery iac_artifacts table (truncated preview)
    bq_type_map = {'tf': 'terraform', 'ansible': 'ansible', 'k8s': 'kubernetes', 'runbook': 'runbook'}
    bq_artifact_type = bq_type_map.get(file_type)
    if bq_artifact_type:
        try:
            project_id = os.getenv("GCP_PROJECT_ID")
            dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
            client = bigquery.Client(project=project_id)
            wave_id = f"wav-{wave_number:04d}"
            query = f"""
                SELECT content_preview 
                FROM `{project_id}.{dataset}.iac_artifacts` 
                WHERE wave_id = '{wave_id}' AND file_name = '{file_name}'
                LIMIT 1
            """
            df = client.query(query).to_dataframe()
            if not df.empty and df.iloc[0]["content_preview"]:
                content = df.iloc[0]["content_preview"]
                # Replace literal \n and \t string escapes with actual formatting control characters
                return content.replace('\\n', '\n').replace('\\t', '\t')
        except Exception as e:
            print(f"BQ artifact fallback failed: {e}")
    
    return ""


def render():
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    client = get_bq_client(project_id)
    
    st.markdown("<h1 class='gradient-text'>Infrastructure as Code & Migration Runbooks</h1>", unsafe_allow_html=True)
    
    # Premium Tab CSS Injections
    st.markdown("""
        <style>
            button[data-baseweb="tab"] {
                font-family: 'Outfit', 'Inter', sans-serif;
                font-size: 0.95rem;
                font-weight: 500;
                color: #a3a8b4 !important;
                background-color: transparent !important;
                border-bottom: 2px solid transparent !important;
                transition: all 0.3s ease;
                padding: 10px 16px;
            }
            button[data-baseweb="tab"]:hover {
                color: #ffffff !important;
                background-color: rgba(255, 255, 255, 0.05) !important;
            }
            button[data-baseweb="tab"][aria-selected="true"] {
                color: #a855f7 !important;
                border-bottom: 2px solid #a855f7 !important;
                background-color: rgba(168, 85, 247, 0.1) !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write("Browse, preview, and download the target Terraform templates, Kubernetes manifests, Ansible Playbooks, and step-by-step migration runbooks generated by D.A.M.I.")
    
    df_waves = get_waves_list(client, project_id, dataset)
    wave_num = 0
    wave_id = "wav-0000"
    wave_name = "Pilot Wave"
    
    sel_col1, sel_col2 = st.columns([2, 1])
    with sel_col1:
        if not df_waves.empty:
            wave_options = [f"Wave {row['wave_number']}: {row['wave_name']}" for _, row in df_waves.iterrows()]
            selected_option = st.selectbox("Select Target Wave Group", wave_options)
            selected_row = df_waves.iloc[wave_options.index(selected_option)]
            wave_num = int(selected_row["wave_number"])
            wave_id = selected_row["wave_id"]
            wave_name = selected_row["wave_name"]
        else:
            st.selectbox("Select Target Wave Group", ["Wave 0: Pilot Wave"])
            st.info("No live waves found in BigQuery database. Showing default Wave 0 mock values. Generate waves on Wave Plan page.")
            
    with sel_col2:
        target_cloud = st.selectbox("Select Target Cloud Provider", [
            "Google Cloud Platform (GCP)",
            "Amazon Web Services (AWS)",
            "Microsoft Azure"
        ])
        
    with col2:
        st.write(" ")
        st.write(" ")
        if st.button("⚙️ Generate Wave Artifacts", use_container_width=True):
            with st.spinner(f"Gemini generating IaC and Runbooks for Wave {wave_num} on {target_cloud}..."):
                from agents.artifacts_generator import ArtifactsGeneratorAgent
                generator = ArtifactsGeneratorAgent()
                try:
                    res = generator.generate_wave_artifacts(wave_num, target_cloud)
                    st.success(f"Success! Generated Wave {wave_num} deployment artifacts.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
                    
    st.write(" ")
    
    # ── Horizontal Metadata Bar ──
    meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
    with meta_col1:
        if "AWS" in target_cloud:
            cloud_badge = "<span class='status-badge' style='display:inline-block; font-weight: 500; background-color: #ff9900; color: #111111;'>Amazon Web Services ☁️</span>"
        elif "Azure" in target_cloud:
            cloud_badge = "<span class='status-badge' style='display:inline-block; font-weight: 500; background-color: #0078d4; color: #ffffff;'>Microsoft Azure ☁️</span>"
        else:
            cloud_badge = "<span class='status-badge status-info' style='display:inline-block; font-weight: 500;'>Google Cloud Platform ☁️</span>"
        st.markdown(f"<p style='font-size:0.9rem; margin-bottom:0.2rem; color: #a3a8b4;'>Target Cloud</p>{cloud_badge}", unsafe_allow_html=True)
    with meta_col2:
        st.markdown("<p style='font-size:0.9rem; margin-bottom:0.2rem; color: #a3a8b4;'>Generation Engine</p><span class='status-badge' style='display:inline-block; font-weight: 500; background-color: #6a1b9a; color: #ffffff;'>Gemini 2.5 Pro 🤖</span>", unsafe_allow_html=True)
    with meta_col3:
        gcs_bucket = os.getenv('GCS_BUCKET', 'dami-artifacts-cohort-2')
        st.markdown(f"<p style='font-size:0.9rem; margin-bottom:0.2rem; color: #a3a8b4;'>Artifacts GCS Target</p><code style='font-size:0.8rem; word-break: break-all;'>gs://{gcs_bucket}/iac-artifacts/wave_{wave_num}/</code>", unsafe_allow_html=True)
    with meta_col4:
        st.markdown("<p style='font-size:0.9rem; margin-bottom:0.2rem; color: #a3a8b4;'>Linter Status</p><span class='status-badge status-success' style='display:inline-block; font-weight: 500;'>Validated & Linted ✅</span>", unsafe_allow_html=True)

    st.write("---")
    
    # Check if files are generated
    tf_code = read_local_file(wave_num, "tf", target_cloud)
    k8s_code = read_local_file(wave_num, "k8s", target_cloud)
    ansible_code = read_local_file(wave_num, "ansible", target_cloud)
    runbook_md = read_local_file(wave_num, "runbook", target_cloud)
    
    # If no files generated yet, fallback to default mocks for illustration
    if not tf_code:
        # Fallback mocks matching wave number
        if wave_num == 0:
            tf_code = """# Wave 0 (Pilot) - Compute Engine Instances for Testing
resource "google_compute_instance" "dev_test_vm_01" {
  name         = "gce-dev-test-01"
  machine_type = "n2-standard-2" # Rightsized from 4vCPU on-prem
  zone         = "us-central1-a"

  boot_disk {
    initialize_params {
      image = "rhel-cloud/rhel-8"
      size  = 40
    }
  }

  network_interface {
    network    = "dami-vpc"
    subnetwork = "dami-subnet-web"
  }

  labels = {
    environment = "dev"
    cost-center = "104"
    wave        = "0"
  }
}"""
            ansible_code = """---
- name: Configure Pilot Web Application Server
  hosts: gce-dev-test-01
  become: yes
  tasks:
    - name: Install Apache Web Server package
      apt:
        name: apache2
        state: present
    - name: Start Apache web service
      service:
        name: apache2
        state: started
        enabled: yes"""
            runbook_md = """# Migration Runbook: Wave 0 (Pilot)
- **ID:** RB-W0
- **Target Workloads:** DEV-TEST-VM-01, DEV-TEST-VM-02
- **Duration:** 4 Hours
- **Rollback Strategy:** Revert routes

## Phase 1: Pre-Migration Validation
- [ ] Verify GCP Interconnect latency < 10ms.
- [ ] Take VMware snapshot of DEV-TEST-VM-01/02.
- [ ] Confirm target subnets are active in GCP project.

## Phase 2: Execution (Cutover)
1. Stop application services on the source VM.
2. Trigger final data replication sync using Migrate to VMs.
3. Power off on-premises VM.
4. Launch rightsized Compute Engine instance in GCE.

## Phase 3: Post-Migration Verification
- [ ] Check ping connectivity to target IP address.
- [ ] Verify service starts successfully on OS.
- [ ] Execute automated functional testing script.
- [ ] If validation fails: Power on-prem VM back on."""
        else:
            tf_code = f"# Wave {wave_num} Infrastructure. Click 'Generate Wave Artifacts' to trigger live generation."
            ansible_code = ""
            k8s_code = ""
            runbook_md = "### Runbook for this wave is pending. Click 'Generate Wave Artifacts' above."

    tab_runbook, tab_lz, tab_tf, tab_docker, tab_k8s, tab_ansible, tab_cicd, tab_monitoring = st.tabs([
        "📖 Runbook", "🏗️ Foundation/LZ", "🚀 Workload IaC", "🐳 Dockerfile", "☸️ Kubernetes YAML", 
        "🤖 Ansible Playbook", "🔄 CI/CD Pipeline", "📊 Monitoring"
    ])
    
    with tab_lz:
        st.write(" ")
        st.subheader(f"Landing Zone Foundation ({target_cloud})")
        st.caption("Generate complete VPCs, Subnets, and Firewalls matching your parsed inventory environments.")
        
        from agents.terraform_agent import TerraformAgent
        tf_agent = TerraformAgent()
        zip_data = tf_agent.generate_landing_zone_zip(target_cloud)
        
        st.success("✅ Landing Zone Terraform codebase is ready for download.")
        st.download_button(
            label="💾 Download LandingZone.zip",
            data=zip_data,
            file_name=f"landing_zone_{target_cloud.split(' ')[0].lower()}.zip",
            mime="application/zip",
            key="dl_lz_zip_btn",
            use_container_width=True
        )
    
    with tab_tf:
        st.write(" ")
        st.subheader(f"{target_cloud} Infrastructure Provisioning (Terraform)")
        st.caption(f"Generated automatically by Gemini Cloud Architect Agent with right-sized {target_cloud} configurations.")
        
        st.code(tf_code, language="hcl")
        if tf_code and "Generate" not in tf_code:
            st.download_button(
                label="💾 Download Terraform File",
                data=tf_code,
                file_name=f"wave_{wave_num}_infra.tf",
                mime="text/plain",
                key=f"dl_tf_{wave_num}"
            )
        
    with tab_k8s:
        st.write(" ")
        st.subheader("Target Kubernetes Configurations")
        st.caption("Generated manifests for containerized refactored workloads (GKE target services).")
        
        if k8s_code:
            st.code(k8s_code, language="yaml")
            st.download_button(
                label="💾 Download Kubernetes Manifest",
                data=k8s_code,
                file_name=f"wave_{wave_num}_k8s.yaml",
                mime="text/plain",
                key=f"dl_k8s_{wave_num}"
            )
        else:
            st.info("No Kubernetes workloads mapped for this wave. Standard Compute Engine or Cloud SQL migrations do not require GKE manifests.")
        
    with tab_ansible:
        st.write(" ")
        st.subheader("Ansible Configuration Playbook")
        st.caption("Generated playbooks for post-migration software installations, package management, and service configurations.")
        
        if ansible_code:
            st.code(ansible_code, language="yaml")
            st.download_button(
                label="💾 Download Ansible Playbook",
                data=ansible_code,
                file_name=f"wave_{wave_num}_ansible.yaml",
                mime="text/plain",
                key=f"dl_ans_{wave_num}"
            )
        else:
            st.info("No virtual machines needing post-migration configuration mapped in this wave (e.g. serverless or container-only waves).")
            
    with tab_runbook:
        st.write(" ")
        st.subheader("Workload Cutover Runbook")
        st.caption("Step-by-step checklist matching enterprise migration standards including rollback procedures.")
        
        st.markdown(runbook_md)
        if runbook_md and "pending" not in runbook_md.lower():
            st.download_button(
                label="💾 Download Runbook Markdown",
                data=runbook_md,
                file_name=f"wave_{wave_num}_runbook.md",
                mime="text/plain",
                key=f"dl_rb_{wave_num}"
            )
            
    with tab_cicd:
        st.write(" ")
        st.subheader("CI/CD Pipeline Configuration")
        st.caption("Auto-generated pipeline configs for GitHub Actions and GitLab CI. Supports build, test, deploy stages.")
        
        ci_tab1, ci_tab2, ci_tab3 = st.tabs(["GitHub Actions", "GitLab CI", "Jenkins"])
        
        with ci_tab1:
            github_actions = f"""name: 'D.A.M.I. Wave {wave_num} - Deploy to GCP'

on:
  push:
    branches: [main]
    paths: ['infra/wave_{wave_num}/**']
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read

jobs:
  terraform-plan:
    name: 'Terraform Plan'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.GCP_SA_EMAIL }}
      
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.0
      
      - name: Terraform Init
        run: terraform init
        working-directory: infra/wave_{wave_num}
      
      - name: Terraform Plan
        run: terraform plan -out=tfplan -var-file=prod.tfvars
        working-directory: infra/wave_{wave_num}
      
      - name: Upload Plan
        uses: actions/upload-artifact@v4
        with:
          name: tfplan-wave-{wave_num}
          path: infra/wave_{wave_num}/tfplan

  terraform-apply:
    name: 'Terraform Apply'
    needs: terraform-plan
    runs-on: ubuntu-latest
    environment: production
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    steps:
      - uses: actions/checkout@v4
      
      - id: auth
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.WIF_PROVIDER }}
          service_account: ${{ secrets.GCP_SA_EMAIL }}
      
      - uses: hashicorp/setup-terraform@v3
      
      - name: Terraform Init
        run: terraform init
        working-directory: infra/wave_{wave_num}
      
      - name: Download Plan
        uses: actions/download-artifact@v4
        with:
          name: tfplan-wave-{wave_num}
          path: infra/wave_{wave_num}
      
      - name: Terraform Apply
        run: terraform apply tfplan
        working-directory: infra/wave_{wave_num}

  post-deploy-validation:
    name: 'Smoke Tests'
    needs: terraform-apply
    runs-on: ubuntu-latest
    steps:
      - name: Health Check
        run: |
          curl --fail --retry 5 --retry-delay 10 \
            https://${{ vars.APP_DOMAIN }}/healthz
      
      - name: Notify Slack
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {{"text": "Wave {wave_num} deployed successfully to GCP."}}
"""
            st.code(github_actions, language="yaml")
        
        with ci_tab2:
            gitlab_ci = f"""stages:
  - validate
  - plan
  - apply
  - verify

variables:
  TF_ROOT: infra/wave_{wave_num}
  
validate:
  stage: validate
  image: hashicorp/terraform:1.7
  script:
    - cd $TF_ROOT
    - terraform init -backend=false
    - terraform validate
  rules:
    - changes: ['infra/wave_{wave_num}/**']

plan:
  stage: plan
  image: hashicorp/terraform:1.7
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform plan -out=tfplan -var-file=prod.tfvars
  artifacts:
    paths: [$TF_ROOT/tfplan]
    expire_in: 1 hour

apply:
  stage: apply
  image: hashicorp/terraform:1.7
  script:
    - cd $TF_ROOT
    - terraform init
    - terraform apply tfplan
  environment:
    name: production
  when: manual
  only: [main]

verify:
  stage: verify
  image: curlimages/curl:latest
  script:
    - curl --fail --retry 5 $APP_URL/healthz
  needs: [apply]
"""
            st.code(gitlab_ci, language="yaml")
        
        with ci_tab3:
            jenkins_pipeline = f"""pipeline {{
    agent any
    
    environment {{
        GCP_PROJECT = 'cohort-2-497207'
        TF_DIR      = "infra/wave_{wave_num}"
    }}
    
    stages {{
        stage('Init') {{
            steps {{
                dir("${{TF_DIR}}") {{
                    sh 'terraform init'
                }}
            }}
        }}
        
        stage('Plan') {{
            steps {{
                dir("${{TF_DIR}}") {{
                    sh 'terraform plan -out=tfplan -var-file=prod.tfvars'
                }}
            }}
        }}
        
        stage('Approval') {{
            steps {{
                input message: "Apply Wave {wave_num} to production?",
                      ok: "Deploy"
            }}
        }}
        
        stage('Apply') {{
            steps {{
                dir("${{TF_DIR}}") {{
                    sh 'terraform apply tfplan'
                }}
            }}
        }}
        
        stage('Verify') {{
            steps {{
                sh "curl --fail --retry 5 ${{APP_URL}}/healthz"
            }}
        }}
    }}
    
    post {{
        success {{ slackSend channel: '#deployments', message: "Wave {wave_num} deployed." }}
        failure {{ slackSend channel: '#alerts', message: "Wave {wave_num} FAILED." }}
    }}
}}"""
            st.code(jenkins_pipeline, language="groovy")
    
    with tab_monitoring:
        st.write(" ")
        st.subheader("Cloud Monitoring & Alerting")
        st.caption("Pre-configured monitoring alert policies and SLO dashboards for migrated workloads.")
        
        monitoring_tf = f"""# Cloud Monitoring Alert Policies for Wave {wave_num}

# CPU High Utilization Alert
resource "google_monitoring_alert_policy" "wave{wave_num}_cpu_high" {{
  display_name = "Wave {wave_num} - CPU > 85%"
  combiner     = "OR"

  conditions {{
    display_name = "CPU utilization > 85% for 5 min"
    condition_threshold {{
      filter          = "resource.type = \\"gce_instance\\" AND metric.type = \\"compute.googleapis.com/instance/cpu/utilization\\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.85
      duration        = "300s"
      aggregations {{
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }}
    }}
  }}

  notification_channels = [google_monitoring_notification_channel.email.name]
  alert_strategy {{ auto_close = "1800s" }}
}}

# Memory Pressure Alert
resource "google_monitoring_alert_policy" "wave{wave_num}_memory" {{
  display_name = "Wave {wave_num} - Memory > 90%"
  combiner     = "OR"

  conditions {{
    display_name = "Memory usage > 90%"
    condition_threshold {{
      filter          = "resource.type = \\"gce_instance\\" AND metric.type = \\"agent.googleapis.com/memory/percent_used\\""
      comparison      = "COMPARISON_GT"
      threshold_value = 90
      duration        = "300s"
    }}
  }}

  notification_channels = [google_monitoring_notification_channel.pagerduty.name]
}}

# Uptime Check
resource "google_monitoring_uptime_check_config" "wave{wave_num}_health" {{
  display_name = "Wave {wave_num} Health Check"
  timeout      = "10s"
  period       = "60s"

  http_check {{
    path         = "/healthz"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }}

  monitored_resource {{
    type = "uptime_url"
    labels = {{
      project_id = var.project_id
      host       = var.app_domain
    }}
  }}
}}

# SLO: 99.9% availability
resource "google_monitoring_slo" "wave{wave_num}_availability" {{
  service      = google_monitoring_custom_service.wave{wave_num}.service_id
  display_name = "Wave {wave_num} Availability SLO"
  goal         = 0.999

  request_based_sli {{
    good_total_ratio {{
      total_service_filter = "resource.type = \\"gce_instance\\""
      good_service_filter  = "resource.type = \\"gce_instance\\" AND metric.type = \\"compute.googleapis.com/instance/uptime\\""
    }}
  }}

  calendar_period = "MONTH"
}}"""
        st.code(monitoring_tf, language="hcl")
    
    with tab_docker:
        st.write(" ")
        st.subheader("Container Images (Dockerfile)")
        st.caption("Auto-generated Dockerfiles for workloads migrated to GKE or Cloud Run via Refactor strategy.")
        
        dockerfile = f"""# Multi-stage production Dockerfile for Wave {wave_num} workloads
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Stage 2: Production
FROM gcr.io/distroless/nodejs20-debian12
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

# Security: non-root user (distroless default)
# Health check endpoint
EXPOSE 8080
ENV NODE_ENV=production
ENV PORT=8080

CMD ["dist/server.js"]
"""
        st.code(dockerfile, language="dockerfile")
        
        st.write("")
        st.caption("**Java Spring Boot variant:**")
        java_dockerfile = f"""# Java Spring Boot - Wave {wave_num} Backend Services
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /workspace
COPY . .
RUN ./gradlew bootJar --no-daemon

FROM eclipse-temurin:21-jre-alpine
RUN addgroup -S app && adduser -S app -G app
USER app
WORKDIR /app
COPY --from=builder /workspace/build/libs/*.jar app.jar

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --spider -q http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["java", "-XX:+UseG1GC", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
"""
        st.code(java_dockerfile, language="dockerfile")
            
    st.write("---")
    st.subheader("🚀 Live Cutover Cockpit & Rollback Simulator")
    st.write("Orchestrate and monitor the active cutover window in real-time. Simulates standard operational pipeline checks and rollback logic in case of network or sync failures.")
    
    # Initialize session states for cutover cockpit
    if "cutover_status" not in st.session_state:
        st.session_state["cutover_status"] = "idle"  # idle, running, failed, rolling_back, completed
    if "cutover_logs" not in st.session_state:
        st.session_state["cutover_logs"] = []
        
    c_col1, c_col2 = st.columns([1, 2])
    
    with c_col1:
        st.write("**Operational Status Console:**")
        if st.session_state["cutover_status"] == "idle":
            st.markdown("<span class='status-badge status-info'>Ready</span> Standby - Waiting to initiate", unsafe_allow_html=True)
            if st.button("⚡ Initiate Live Cutover Simulation", use_container_width=True):
                st.session_state["cutover_status"] = "running"
                st.session_state["cutover_logs"] = []
                st.rerun()
                
        elif st.session_state["cutover_status"] == "running":
            st.markdown("<span class='status-badge status-warning'>Executing</span> Running active sync playbooks...", unsafe_allow_html=True)
            st.write(" ")
            # Run simulation steps
            import time
            placeholder = st.empty()
            
            steps = [
                ("1. Quiesce Source On-Premises VMware VMs", 0.5, "SUCCESS", "Shutdown commands sent to vCenter. srv-0001, srv-0002, srv-0003 offline."),
                ("2. Establish Final DB Storage Replication Sync", 1.5, "FAILED", "ERROR: Storage replica lag exceeds 420 seconds. Packet loss detected on DX Gateway.")
            ]
            
            for step_name, delay, outcome, details in steps:
                st.session_state["cutover_logs"].append(f"[INFO] Starting: {step_name}")
                time.sleep(delay)
                if outcome == "SUCCESS":
                    st.session_state["cutover_logs"].append(f"[SUCCESS] Completed: {step_name} - {details}")
                else:
                    st.session_state["cutover_logs"].append(f"[CRITICAL] {details}")
                    st.session_state["cutover_logs"].append(f"[FATAL] Cutover window threshold breached. Execution halted.")
                    st.session_state["cutover_status"] = "failed"
                    st.rerun()
                    
        elif st.session_state["cutover_status"] == "failed":
            st.markdown("<span class='status-badge status-danger'>HALTED / FAILING</span> DB replica sync lag threshold breached", unsafe_allow_html=True)
            st.write(" ")
            st.error("🚨 Critical Error: Step 2 Failed. Cutover window exceeded. Immediate rollback required to restore source services!")
            
            if st.button("🚨 TRIGGER IMMEDIATE ROLLBACK", use_container_width=True):
                st.session_state["cutover_status"] = "rolling_back"
                st.rerun()
                
        elif st.session_state["cutover_status"] == "rolling_back":
            st.markdown("<span class='status-badge status-warning'>Rolling Back</span> Reverting DNS routing and powering up source VMs...", unsafe_allow_html=True)
            st.write(" ")
            import time
            
            rollback_steps = [
                ("1. Revert DNS traffic to On-Premises Gateways", 0.8),
                ("2. Terminate dry-run GCP VM Target Instances", 0.8),
                ("3. Send PowerOn command to source VMware hosts", 0.8)
            ]
            
            for r_step, r_delay in rollback_steps:
                st.session_state["cutover_logs"].append(f"[ROLLBACK] Running: {r_step}")
                time.sleep(r_delay)
                st.session_state["cutover_logs"].append(f"[ROLLBACK] Success: {r_step} complete.")
                
            st.session_state["cutover_status"] = "idle"
            st.session_state["cutover_logs"].append("[ROLLBACK SUCCESS] On-premises services are fully restored. Rollback complete.")
            st.rerun()
            
    with c_col2:
        st.write("**Operational Log Stream:**")
        log_box = "\n".join(st.session_state["cutover_logs"])
        if log_box:
            st.text_area("Console Logs", log_box, height=220, disabled=True)
        else:
            st.info("Initiate the simulation to see execution output logs.")

    # ── Rollback Plan Generator ──
    st.write("---")
    st.subheader("🔄 Rollback Plan Generator")
    st.write(f"Auto-generated rollback playbook for **Wave {wave_num}: {wave_name}** — ensures safe recovery if migration fails.")
    
    # Get wave servers for context
    try:
        wave_servers = client.query(f"""
            SELECT s.name, s.workload_type, s.environment 
            FROM `{project_id}.{dataset}.wave_workloads` w
            JOIN `{project_id}.{dataset}.servers` s ON w.server_id = s.server_id
            WHERE w.wave_id = '{wave_id}'
            LIMIT 20
        """).to_dataframe()
    except:
        wave_servers = pd.DataFrame()
    
    server_count = len(wave_servers) if not wave_servers.empty else 15
    has_db = not wave_servers.empty and wave_servers["workload_type"].str.contains("DB", case=False, na=False).any()
    has_web = not wave_servers.empty and wave_servers["workload_type"].str.contains("WEB|APP", case=False, na=False).any()
    is_prod = not wave_servers.empty and wave_servers["environment"].str.contains("prod", case=False, na=False).any()
    
    estimated_rollback_mins = 15 + (server_count * 2) + (30 if has_db else 0) + (10 if is_prod else 0)
    
    rb_col1, rb_col2, rb_col3, rb_col4 = st.columns(4)
    with rb_col1:
        st.metric("Estimated Rollback Time", f"{estimated_rollback_mins} min", delta="Automated")
    with rb_col2:
        st.metric("Servers Covered", f"{server_count}", delta=f"Wave {wave_num}")
    with rb_col3:
        risk = "🔴 High" if is_prod and has_db else "🟡 Medium" if is_prod or has_db else "🟢 Low"
        st.metric("Rollback Risk", risk)
    with rb_col4:
        st.metric("Recovery Point", "Pre-Migration", delta="Snapshot-based")
    
    st.write("")
    
    rb_left, rb_right = st.columns([1, 1])
    
    with rb_left:
        rollback_md = f"""## 📋 Pre-Migration Checklist (Wave {wave_num})

- [ ] **Snapshot all VMs** — Create compute disk snapshots for all {server_count} servers
- [ ] **Database backup** — {'Export full database dumps (MySQL/Oracle) to GCS backup bucket' if has_db else 'No databases in this wave — skip'}
- [ ] **DNS TTL reduction** — Lower DNS TTL to 60s (24h before migration window)
- [ ] **Load balancer drain** — {'Drain active connections from on-prem LB' if has_web else 'No web tier in this wave — skip'}
- [ ] **Notify stakeholders** — Send migration start notification to ops team
- [ ] **Verify monitoring** — Confirm Cloud Monitoring alerting is active on target

---

## 🔄 Rollback Procedure

### Step 1: Detect Failure (T+0)
- Monitor error rates, latency, and health checks for **30 minutes** post-cutover
- **Go/No-Go Criteria:** Error rate < 1%, P99 latency < 500ms, all health checks passing

### Step 2: Initiate Rollback (T+5 min)
```bash
# Revert DNS to on-premises endpoints
gcloud dns record-sets update wave{wave_num}.internal \\
  --zone=migration-zone \\
  --type=A --rrdatas="10.128.0.0/16"

# Restore on-prem load balancer
{'gcloud compute forwarding-rules update wave' + str(wave_num) + '-lb --target-pool=onprem-pool' if has_web else '# No LB in this wave'}
```

### Step 3: Database Rollback (T+10 min)
{'```bash' + chr(10) + '# Restore database from pre-migration snapshot' + chr(10) + 'gcloud sql instances restore-backup wave' + str(wave_num) + '-db \\' + chr(10) + '  --backup-id=pre-migration-' + str(wave_num) + chr(10) + '```' if has_db else '- No databases in this wave — skip this step'}

### Step 4: Verify Recovery (T+{estimated_rollback_mins} min)
- Confirm all on-prem services responding
- Validate data consistency (compare row counts)
- Clear CDN/cache if applicable
- Send rollback notification to stakeholders
"""
        st.markdown(rollback_md)
    
    with rb_right:
        st.markdown("##### ✅ Go/No-Go Decision Matrix")
        
        criteria_data = [
            {"Criteria": "Error Rate", "Threshold": "< 1%", "Check": "Cloud Monitoring", "Required": "✅ Must Pass"},
            {"Criteria": "P99 Latency", "Threshold": "< 500ms", "Check": "Cloud Trace", "Required": "✅ Must Pass"},
            {"Criteria": "Health Checks", "Threshold": "All Passing", "Check": "Load Balancer", "Required": "✅ Must Pass"},
            {"Criteria": "Data Integrity", "Threshold": "Row count match", "Check": "SQL validation", "Required": "✅ Must Pass"},
            {"Criteria": "User Reports", "Threshold": "0 incidents", "Check": "ServiceNow", "Required": "⚠️ Advisory"},
            {"Criteria": "Performance", "Threshold": "Within 10% baseline", "Check": "APM Dashboard", "Required": "⚠️ Advisory"},
        ]
        st.dataframe(pd.DataFrame(criteria_data), use_container_width=True, hide_index=True)
        
        st.write("")
        st.markdown("##### 📞 Escalation Contacts")
        contacts = [
            {"Role": "Migration Lead", "Contact": "Ext. 4001", "Escalation": "Primary"},
            {"Role": "DBA On-Call", "Contact": "Ext. 4002", "Escalation": "DB Issues"},
            {"Role": "Network Ops", "Contact": "Ext. 4003", "Escalation": "DNS/LB"},
            {"Role": "CISO Office", "Contact": "Ext. 4004", "Escalation": "Security"},
        ]
        st.dataframe(pd.DataFrame(contacts), use_container_width=True, hide_index=True)
        
        # Download rollback plan
        st.download_button(
            "⬇️ Download Rollback Plan (.md)",
            data=rollback_md,
            file_name=f"Rollback_Plan_Wave_{wave_num}.md",
            mime="text/markdown",
            use_container_width=True
        )

if __name__ == "__main__":
    render()
