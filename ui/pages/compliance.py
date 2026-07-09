# ui/pages/compliance.py
"""
Compliance & Security Posture Dashboard
Maps workloads to compliance frameworks (HIPAA, PCI-DSS, SOC2, ISO27001)
and shows security control readiness for each migration wave.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@st.cache_resource
def get_bq_client(project_id):
    return bigquery.Client(project=project_id)

def fetch_compliance_data(client, project_id, dataset):
    """Fetch server data with compliance flags and risk info."""
    query = f"""
        SELECT s.server_id, s.name, s.workload_type, s.environment, s.os,
               s.compliance_flags, s.tags,
               r.risk_level, r.recommended_strategy, r.overall_risk_score
        FROM `{project_id}.{dataset}.servers` s
        LEFT JOIN `{project_id}.{dataset}.risk_scores` r ON s.server_id = r.server_id
    """
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return df
    except Exception as e:
        print(f"Failed to query compliance data: {e}")
    return None

# Compliance framework control mappings
COMPLIANCE_FRAMEWORKS = {
    "HIPAA": {
        "icon": "🏥",
        "color": "#ef4444",
        "controls": [
            {"id": "164.312(a)(1)", "name": "Access Control", "gcp_service": "Cloud IAM + Context-Aware Access", "status": "auto"},
            {"id": "164.312(a)(2)(iv)", "name": "Encryption at Rest", "gcp_service": "CMEK (Cloud KMS)", "status": "auto"},
            {"id": "164.312(e)(1)", "name": "Transmission Security", "gcp_service": "VPC Service Controls + TLS 1.3", "status": "auto"},
            {"id": "164.308(a)(1)", "name": "Security Management", "gcp_service": "Security Command Center Premium", "status": "review"},
            {"id": "164.312(b)", "name": "Audit Controls", "gcp_service": "Cloud Audit Logs + Chronicle SIEM", "status": "auto"},
            {"id": "164.310(d)(1)", "name": "Device & Media Controls", "gcp_service": "Confidential VMs + Shielded VMs", "status": "review"},
        ]
    },
    "PCI-DSS": {
        "icon": "💳",
        "color": "#f59e0b",
        "controls": [
            {"id": "Req 1", "name": "Network Segmentation", "gcp_service": "VPC Firewall Rules + Hierarchical Policies", "status": "auto"},
            {"id": "Req 3", "name": "Protect Stored Data", "gcp_service": "CMEK + DLP API", "status": "auto"},
            {"id": "Req 6", "name": "Secure Development", "gcp_service": "Binary Authorization + Artifact Registry", "status": "review"},
            {"id": "Req 7", "name": "Access Restriction", "gcp_service": "IAM Conditions + VPC-SC Perimeters", "status": "auto"},
            {"id": "Req 8", "name": "Authentication", "gcp_service": "Cloud Identity + MFA Enforcement", "status": "auto"},
            {"id": "Req 10", "name": "Logging & Monitoring", "gcp_service": "Cloud Logging + Cloud Monitoring", "status": "auto"},
        ]
    },
    "SOC2": {
        "icon": "🔒",
        "color": "#6366f1",
        "controls": [
            {"id": "CC6.1", "name": "Logical Access", "gcp_service": "Cloud IAM + Organization Policies", "status": "auto"},
            {"id": "CC6.6", "name": "System Boundary Protection", "gcp_service": "Cloud Armor WAF + DDoS Protection", "status": "auto"},
            {"id": "CC7.2", "name": "Monitoring Activities", "gcp_service": "Security Command Center + Event Threat Detection", "status": "auto"},
            {"id": "CC8.1", "name": "Change Management", "gcp_service": "Cloud Build + Terraform State Locking", "status": "review"},
            {"id": "A1.2", "name": "Recovery Mechanisms", "gcp_service": "Cloud SQL HA + Cross-Region Snapshots", "status": "auto"},
        ]
    },
    "ISO27001": {
        "icon": "🌐",
        "color": "#22d3ee",
        "controls": [
            {"id": "A.9", "name": "Access Control Policy", "gcp_service": "IAM + BeyondCorp Enterprise", "status": "auto"},
            {"id": "A.10", "name": "Cryptography", "gcp_service": "Cloud KMS + Certificate Manager", "status": "auto"},
            {"id": "A.12", "name": "Operations Security", "gcp_service": "OS Config Management + Patch Management", "status": "review"},
            {"id": "A.13", "name": "Communications Security", "gcp_service": "Private Google Access + Cloud Interconnect", "status": "auto"},
            {"id": "A.18", "name": "Compliance Verification", "gcp_service": "Assured Workloads + Compliance Reports", "status": "auto"},
        ]
    }
}

def render():
    st.markdown("<h1 class='gradient-text'>Compliance & Security Posture</h1>", unsafe_allow_html=True)
    st.write("Map each workload's compliance requirements to Google Cloud security controls. Ensure regulatory readiness before migration execution.")
    st.write("---")

    project_id = os.getenv("GCP_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "dami_v3")
    client = get_bq_client(project_id)

    df = fetch_compliance_data(client, project_id, dataset)

    # Compliance posture summary
    st.subheader("🛡️ Compliance Framework Coverage")

    framework_cols = st.columns(4)
    for idx, (fw_name, fw_data) in enumerate(COMPLIANCE_FRAMEWORKS.items()):
        with framework_cols[idx]:
            total = len(fw_data["controls"])
            auto_count = sum(1 for c in fw_data["controls"] if c["status"] == "auto")
            pct = int((auto_count / total) * 100)
            review_count = total - auto_count

            st.markdown(f"""
            <div style="
                background: rgba(30, 30, 47, 0.6);
                border: 1px solid {fw_data['color']}44;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                transition: all 0.3s ease;
            ">
                <div style="font-size: 2rem;">{fw_data['icon']}</div>
                <div style="font-weight: 700; color: {fw_data['color']}; font-size: 1.1rem; margin: 4px 0;">{fw_name}</div>
                <div style="font-size: 2rem; font-weight: 800; color: #e2e8f0;">{pct}%</div>
                <div style="font-size: 0.75rem; color: #94a3b8;">Auto-mapped controls</div>
                <div style="margin-top: 8px;">
                    <span style="background: #10b98133; color: #10b981; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: 600;">
                        ✅ {auto_count} Automated
                    </span>
                    &nbsp;
                    <span style="background: #f59e0b33; color: #f59e0b; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: 600;">
                        👁️ {review_count} Review
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    st.write("---")

    # Detailed control mapping per framework
    st.subheader("📋 Security Control Mapping Detail")

    selected_fw = st.selectbox(
        "Select Compliance Framework",
        list(COMPLIANCE_FRAMEWORKS.keys()),
        format_func=lambda x: f"{COMPLIANCE_FRAMEWORKS[x]['icon']} {x}"
    )

    fw = COMPLIANCE_FRAMEWORKS[selected_fw]

    for ctrl in fw["controls"]:
        status_color = "#10b981" if ctrl["status"] == "auto" else "#f59e0b"
        status_label = "✅ Auto-Mapped" if ctrl["status"] == "auto" else "👁️ Manual Review Required"
        status_bg = "#10b98118" if ctrl["status"] == "auto" else "#f59e0b18"

        st.markdown(f"""
        <div style="
            background: {status_bg};
            border-left: 3px solid {status_color};
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div>
                <span style="font-weight: 600; color: #e2e8f0;">{ctrl['id']}</span>
                <span style="color: #94a3b8; margin-left: 8px;">—</span>
                <span style="color: #cbd5e1; margin-left: 8px;">{ctrl['name']}</span>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.75rem; color: {fw['color']}; font-weight: 500;">{ctrl['gcp_service']}</div>
                <div style="font-size: 0.7rem; color: {status_color}; font-weight: 600; margin-top: 2px;">{status_label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("---")

    # Workload Compliance Heatmap
    st.subheader("🗺️ Workload Compliance Risk Heatmap")

    if df is not None and not df.empty:
        # Parse compliance flags and determine framework applicability
        workload_compliance = []
        for _, row in df.iterrows():
            flags = row.get("compliance_flags", [])
            if flags is None:
                flags = []
            env = row.get("environment", "dev")
            wtype = row.get("workload_type", "APP")
            risk = row.get("risk_level", "medium")

            # Determine applicable frameworks based on workload characteristics
            applicable = []
            if "HIPAA" in flags or (wtype == "DB" and env == "prod"):
                applicable.append("HIPAA")
            if "PCI" in flags or (wtype in ["WEB", "APP"] and env == "prod"):
                applicable.append("PCI-DSS")
            if env == "prod":
                applicable.append("SOC2")
            applicable.append("ISO27001")  # Always applicable

            workload_compliance.append({
                "server_id": row["server_id"],
                "name": row["name"],
                "environment": env,
                "workload_type": wtype,
                "risk_level": risk,
                "frameworks": ", ".join(applicable),
                "framework_count": len(applicable),
            })

        comp_df = pd.DataFrame(workload_compliance)

        # Show summary table
        col_chart, col_table = st.columns([1, 1])

        with col_chart:
            # Framework coverage by workload type
            fw_counts = []
            for _, row in comp_df.iterrows():
                for fw in row["frameworks"].split(", "):
                    if fw:
                        fw_counts.append({"framework": fw, "workload_type": row["workload_type"]})
            if fw_counts:
                fw_df = pd.DataFrame(fw_counts)
                fig = px.histogram(
                    fw_df, x="framework", color="workload_type",
                    barmode="group",
                    color_discrete_sequence=["#6366f1", "#8b5cf6", "#22d3ee", "#10b981", "#f59e0b", "#ef4444", "#ec4899", "#14b8a6", "#0ea5e9"]
                )
                fig.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="#e2e8f0",
                    title=dict(text="Framework Coverage by Workload Type", font=dict(size=13)),
                    xaxis_title="",
                    yaxis_title="Workload Count",
                    margin=dict(l=40, r=10, t=40, b=80),
                    height=450,
                    legend=dict(
                        orientation="h",
                        yanchor="top", y=-0.15,
                        xanchor="center", x=0.5,
                        font=dict(size=9),
                        bgcolor="rgba(0,0,0,0)",
                        traceorder="normal"
                    )
                )
                st.plotly_chart(fig, use_container_width=True)

        with col_table:
            # Risk level breakdown by compliance burden
            risk_fw = comp_df.groupby(["risk_level", "framework_count"]).size().reset_index(name="count")
            fig2 = px.scatter(
                risk_fw, x="framework_count", y="risk_level",
                size="count", color="risk_level",
                color_discrete_map={"low": "#10b981", "medium": "#f59e0b", "high": "#ef4444", "critical": "#dc2626"},
                size_max=25
            )
            fig2.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#e2e8f0",
                title=dict(text="Risk Level vs Compliance Burden", font=dict(size=13)),
                xaxis_title="# Frameworks Applicable",
                yaxis_title="",
                margin=dict(l=10, r=10, t=40, b=60),
                height=450,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="top", y=-0.12,
                    xanchor="center", x=0.5,
                    font=dict(size=9),
                    bgcolor="rgba(0,0,0,0)"
                )
            )
            fig2.update_xaxes(dtick=1)
            st.plotly_chart(fig2, use_container_width=True)

        # Show compliance details table
        st.dataframe(
            comp_df[["name", "environment", "workload_type", "risk_level", "frameworks"]].head(20),
            use_container_width=True,
            hide_index=True,
            column_config={
                "name": "Server Name",
                "environment": "Environment",
                "workload_type": "Workload Type",
                "risk_level": "Risk Level",
                "frameworks": "Applicable Frameworks"
            }
        )
    else:
        st.info("No workload data available. Seed the database from the Upload Center to see compliance mapping.")

    # Generated Terraform security controls
    st.subheader("🔐 Generated Security Infrastructure-as-Code")
    st.caption("D.A.M.I. auto-generates the following security Terraform configurations for your target landing zone.")

    sec_row1_col1, sec_row1_col2 = st.columns(2)

    with sec_row1_col1:
        with st.expander("🛡️ VPC Service Controls Perimeter", expanded=False):
            st.code('''# VPC Service Controls Perimeter
resource "google_access_context_manager_service_perimeter" "migration_perimeter" {
  parent = "accessPolicies/${var.access_policy_id}"
  name   = "accessPolicies/${var.access_policy_id}/servicePerimeters/migration_zone"
  title  = "D.A.M.I. Migration Security Perimeter"

  status {
    resources = ["projects/${var.project_number}"]
    restricted_services = [
      "bigquery.googleapis.com",
      "storage.googleapis.com",
      "compute.googleapis.com",
      "sqladmin.googleapis.com"
    ]
    access_levels = [
      google_access_context_manager_access_level.corp_network.name
    ]
  }
}''', language="hcl")

    with sec_row1_col2:
        with st.expander("🔑 Cloud KMS CMEK Encryption", expanded=False):
            st.code('''# Customer-Managed Encryption Keys (CMEK)
resource "google_kms_key_ring" "migration_keyring" {
  name     = "dami-migration-keyring"
  location = var.region
}

resource "google_kms_crypto_key" "db_encryption_key" {
  name            = "db-encryption-key"
  key_ring        = google_kms_key_ring.migration_keyring.id
  rotation_period = "7776000s"  # 90 days
  purpose         = "ENCRYPT_DECRYPT"

  version_template {
    algorithm        = "GOOGLE_SYMMETRIC_ENCRYPTION"
    protection_level = "HSM"
  }
  lifecycle { prevent_destroy = true }
}''', language="hcl")

    sec_row2_col1, sec_row2_col2 = st.columns(2)

    with sec_row2_col1:
        with st.expander("🌐 Cloud Armor WAF Policy", expanded=False):
            st.code('''# Cloud Armor Web Application Firewall
resource "google_compute_security_policy" "migration_waf" {
  name = "dami-migration-waf-policy"

  # OWASP Top 10 protection
  rule {
    action   = "deny(403)"
    priority = "1000"
    match {
      expr { expression = "evaluatePreconfiguredExpr('xss-v33-stable')" }
    }
    description = "Block XSS attacks"
  }

  rule {
    action   = "deny(403)"
    priority = "1001"
    match {
      expr { expression = "evaluatePreconfiguredExpr('sqli-v33-stable')" }
    }
    description = "Block SQL injection"
  }

  rule {
    action   = "throttle"
    priority = "2000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config { src_ip_ranges = ["*"] }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
    }
    description = "Rate limiting - 100 req/min per IP"
  }

  # Default allow
  rule {
    action   = "allow"
    priority = "2147483647"
    match { versioned_expr = "SRC_IPS_V1"
      config { src_ip_ranges = ["*"] }
    }
  }
}''', language="hcl")

    with sec_row2_col2:
        with st.expander("🔒 IAM Workload Identity Federation", expanded=False):
            st.code('''# Workload Identity Federation (keyless auth)
resource "google_iam_workload_identity_pool" "migration_pool" {
  workload_identity_pool_id = "dami-migration-pool"
  display_name              = "D.A.M.I. Migration Workload Pool"
}

resource "google_iam_workload_identity_pool_provider" "github_provider" {
  workload_identity_pool_id          = google_iam_workload_identity_pool.migration_pool.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-actions"
  display_name                       = "GitHub Actions CI/CD"

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.actor"      = "assertion.actor"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account_iam_binding" "workload_binding" {
  service_account_id = google_service_account.migration_sa.name
  role               = "roles/iam.workloadIdentityUser"
  members = [
    "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.migration_pool.name}/attribute.repository/${var.github_repo}"
  ]
}''', language="hcl")

    sec_row3_col1, sec_row3_col2 = st.columns(2)

    with sec_row3_col1:
        with st.expander("✅ Binary Authorization for GKE", expanded=False):
            st.code('''# Binary Authorization - only deploy signed images
resource "google_binary_authorization_policy" "migration_policy" {
  project = var.project_id

  admission_whitelist_patterns {
    name_pattern = "gcr.io/${var.project_id}/*"
  }

  default_admission_rule {
    evaluation_mode  = "REQUIRE_ATTESTATION"
    enforcement_mode = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    require_attestations_by = [
      google_binary_authorization_attestor.build_attestor.id
    ]
  }

  cluster_admission_rules {
    cluster                 = "${var.region}.${var.gke_cluster_name}"
    evaluation_mode         = "REQUIRE_ATTESTATION"
    enforcement_mode        = "ENFORCED_BLOCK_AND_AUDIT_LOG"
    require_attestations_by = [
      google_binary_authorization_attestor.build_attestor.id
    ]
  }
}

resource "google_binary_authorization_attestor" "build_attestor" {
  name = "dami-build-attestor"
  attestation_authority_note {
    note_reference = google_container_analysis_note.build_note.name
  }
}''', language="hcl")

    with sec_row3_col2:
        with st.expander("📋 Organization Policy Constraints", expanded=False):
            st.code('''# Org Policy - Restrict resource locations
resource "google_org_policy_policy" "restrict_locations" {
  name   = "projects/${var.project_id}/policies/gcp.resourceLocations"
  parent = "projects/${var.project_id}"

  spec {
    rules {
      values {
        allowed_values = [
          "in:us-locations",
          "in:eu-locations"
        ]
      }
    }
  }
}

# Org Policy - Disable external IP on VMs
resource "google_org_policy_policy" "disable_external_ip" {
  name   = "projects/${var.project_id}/policies/compute.vmExternalIpAccess"
  parent = "projects/${var.project_id}"

  spec {
    rules { enforce = "TRUE" }
  }
}

# Org Policy - Require OS Login
resource "google_org_policy_policy" "require_os_login" {
  name   = "projects/${var.project_id}/policies/compute.requireOsLogin"
  parent = "projects/${var.project_id}"

  spec {
    rules { enforce = "TRUE" }
  }
}

# Cloud Audit Logs - Full data access logging
resource "google_project_iam_audit_config" "full_audit" {
  project = var.project_id
  service = "allServices"

  audit_log_config { log_type = "ADMIN_READ" }
  audit_log_config { log_type = "DATA_READ" }
  audit_log_config { log_type = "DATA_WRITE" }
}''', language="hcl")
    
    # ── Compliance Gap Analysis ──
    st.write("---")
    st.subheader("🔍 Compliance Gap Analysis & Auto-Remediation")
    st.write("Identifies compliance gaps across all frameworks and generates prioritized remediation actions.")
    
    # Build gap analysis from framework controls
    gaps = []
    for framework, fw_data in COMPLIANCE_FRAMEWORKS.items():
        for ctrl in fw_data["controls"]:
            if ctrl["status"] == "review":
                gaps.append({
                    "Framework": f"{fw_data['icon']} {framework}",
                    "Control ID": ctrl["id"],
                    "Control Name": ctrl["name"],
                    "GCP Service": ctrl["gcp_service"],
                    "Status": "⚠️ Needs Review",
                    "Priority": "High" if framework in ["HIPAA", "PCI-DSS"] else "Medium",
                    "Est. Effort": "2-4 hours"
                })
            elif ctrl["status"] == "manual":
                gaps.append({
                    "Framework": f"{fw_data['icon']} {framework}",
                    "Control ID": ctrl["id"],
                    "Control Name": ctrl["name"],
                    "GCP Service": ctrl["gcp_service"],
                    "Status": "🔴 Manual Required",
                    "Priority": "Critical",
                    "Est. Effort": "4-8 hours"
                })
    
    total_controls = sum(len(fw["controls"]) for fw in COMPLIANCE_FRAMEWORKS.values())
    auto_controls = total_controls - len(gaps)
    compliance_pct = round(auto_controls / total_controls * 100) if total_controls > 0 else 0
    
    gap_col1, gap_col2, gap_col3, gap_col4 = st.columns(4)
    with gap_col1:
        color = "#10b981" if compliance_pct >= 85 else "#f59e0b" if compliance_pct >= 70 else "#ef4444"
        st.markdown(f"""
        <div style="text-align:center; padding:12px; background:rgba(15,15,26,0.6); border-radius:10px; border:1px solid {color}33;">
            <div style="font-size:2rem; font-weight:800; color:{color};">{compliance_pct}%</div>
            <div style="font-size:0.75rem; color:#94a3b8;">Auto-Compliant</div>
        </div>""", unsafe_allow_html=True)
    with gap_col2:
        st.metric("Total Controls", f"{total_controls}", delta=f"{len(COMPLIANCE_FRAMEWORKS)} frameworks")
    with gap_col3:
        st.metric("Auto-Mapped", f"{auto_controls}", delta="GCP-native controls")
    with gap_col4:
        st.metric("Gaps Found", f"{len(gaps)}", delta="Action required", delta_color="inverse")
    
    st.write("")
    
    if gaps:
        gap_left, gap_right = st.columns([1, 1])
        
        with gap_left:
            st.markdown("##### ⚠️ Outstanding Compliance Gaps")
            gap_df = pd.DataFrame(gaps)
            st.dataframe(gap_df, use_container_width=True, hide_index=True)
        
        with gap_right:
            st.markdown("##### 🛠️ Auto-Remediation Commands")
            st.caption("Copy and apply these Terraform/gcloud commands to close compliance gaps:")
            
            remediation_cmds = []
            for gap in gaps:
                if "Encryption" in gap["Control Name"]:
                    remediation_cmds.append(f"# {gap['Control ID']}: {gap['Control Name']}\ngcloud kms keyrings create migration-keyring --location=global\ngcloud kms keys create cmek-key --keyring=migration-keyring --location=global --purpose=encryption")
                elif "Access" in gap["Control Name"] or "Identity" in gap["Control Name"]:
                    remediation_cmds.append(f"# {gap['Control ID']}: {gap['Control Name']}\ngcloud projects add-iam-policy-binding $PROJECT_ID \\\n  --member='group:security-admins@domain.com' \\\n  --role='roles/iam.securityReviewer'")
                elif "Audit" in gap["Control Name"] or "Log" in gap["Control Name"]:
                    remediation_cmds.append(f"# {gap['Control ID']}: {gap['Control Name']}\ngcloud logging sinks create compliance-sink \\\n  storage.googleapis.com/compliance-logs-bucket \\\n  --log-filter='resource.type=\"gce_instance\"'")
                elif "Network" in gap["Control Name"] or "Firewall" in gap["Control Name"]:
                    remediation_cmds.append(f"# {gap['Control ID']}: {gap['Control Name']}\ngcloud compute firewall-rules update default-allow-internal \\\n  --disabled")
                else:
                    remediation_cmds.append(f"# {gap['Control ID']}: {gap['Control Name']}\n# Review required: {gap['GCP Service']}\n# Assign to security team for manual assessment")
            
            st.code("\n\n".join(remediation_cmds), language="bash")
    else:
        st.success("✅ All compliance controls are auto-mapped! No gaps detected.")

    st.write("---")
    st.subheader("🛡️ AI Zero-Trust Security Policy Generator")
    st.write("Automatically generate strict Network Policies and Firewall Rules based on observed application dependency traffic.")
    
    if st.button("🔒 Generate Zero-Trust Policies", type="primary"):
        with st.spinner("Gemini is analyzing dependencies to generate Zero-Trust rules..."):
            import json
            from google.genai import Client
            from google.genai import types
            
            try:
                deps_df = client.query(f"SELECT source_server_id, target_server_id, port, protocol FROM `{project_id}.{dataset}.dependencies` LIMIT 50").to_dataframe()
                deps_json = json.dumps(deps_df.to_dict('records'))
                
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    genai_client = Client(api_key=api_key)
                    model_name = "gemini-2.5-pro"
                else:
                    genai_client = Client(enterprise=True)
                    model_name = f"projects/{os.getenv('VERTEX_PROJECT_ID', 'gcp-experiments-490315')}/locations/{os.getenv('VERTEX_AI_LOCATION', 'us-central1')}/publishers/google/models/gemini-2.5-pro"
                
                prompt = f"""
                You are a DevSecOps Engineer. Based on the following application dependency map, generate strict Zero-Trust security rules.
                
                1. Output a Kubernetes `NetworkPolicy` YAML for GKE workloads that ONLY allows the exact observed ports.
                2. Output Terraform `google_compute_firewall` blocks for GCP VMs restricting traffic.
                
                Dependencies observed:
                {deps_json}
                """
                
                response = genai_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.2)
                )
                
                st.session_state["zero_trust_code"] = response.text
                st.success("Zero-Trust Security Policies generated successfully!")
            except Exception as e:
                st.error(f"Failed to generate Zero-Trust policies: {e}")
                
    if "zero_trust_code" in st.session_state:
        st.markdown(st.session_state["zero_trust_code"])


if __name__ == "__main__":
    render()
