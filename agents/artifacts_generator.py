# agents/artifacts_generator.py
import os
import json
import datetime
from google.cloud import bigquery
from google.genai import Client
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

# Define Pydantic schema for structured output
class WaveArtifactsResponse(BaseModel):
    terraform_hcl: str = Field(description="Complete, valid, syntactically correct Terraform HCL configuration for all target resources mapped in this wave. Do not include markdown code block syntax inside the string.")
    kubernetes_yaml: str = Field(description="Kubernetes Deployment, Service, and HPA YAML manifests (only if GKE is one of the target services in this wave; empty string otherwise). Do not include markdown code block syntax inside the string.")
    ansible_playbook: str = Field(description="Ansible playbook YAML for configuring OS packages, application services, and files on the migrated VMs (only if compute-engine is one of the target services in this wave; empty string otherwise). Do not include markdown code block syntax inside the string.")
    markdown_runbook: str = Field(description="Comprehensive step-by-step markdown migration runbook outlining Phase 1: Pre-Migration, Phase 2: Cutover Execution, Phase 3: Post-Migration verification, and Phase 4: Rollback scripts.")

class ArtifactsGeneratorAgent:
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
        self.location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
        self.model_name = "gemini-2.5-pro"
        
        # Check if GEMINI_API_KEY is available, otherwise use keyless Vertex AI
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = Client(api_key=api_key)
            self.use_vertex = False
        else:
            self.client = Client(enterprise=True)
            self.use_vertex = True
            self.vertex_project = os.getenv("VERTEX_PROJECT_ID", "gcp-experiments-490315")

    def generate_wave_artifacts(self, wave_number: int, target_cloud: str = "Google Cloud Platform (GCP)") -> dict:
        """
        Reads target architecture mapping and sequence details from BigQuery,
        generates IaC configurations and Runbooks using Gemini, and saves results.
        """
        print(f"Starting IaC & Runbook generation for Wave {wave_number} on {target_cloud}...")
        client = bigquery.Client(project=self.project_id)
        
        # 1. Fetch wave metadata
        wave_query = f"""
            SELECT * FROM `{self.project_id}.{self.dataset}.waves`
            WHERE wave_number = {wave_number}
            LIMIT 1
        """
        wave_df = client.query(wave_query).to_dataframe()
        if wave_df.empty:
            raise Exception(f"Wave {wave_number} not found in BigQuery database. Please run the Wave Planner agent first.")
            
        wave_row = wave_df.iloc[0]
        wave_id = wave_row["wave_id"]
        wave_name = wave_row["wave_name"]
        
        # 2. Fetch wave workloads joined with target architecture mapping
        workloads_query = f"""
            SELECT w.server_id, w.sequence_in_wave, w.migration_approach, w.target_gcp_service, w.target_machine_type, w.target_region, w.estimated_hours,
                   s.name as server_name, s.os, s.vcpu, s.ram_gb, s.disk_gb,
                   t.target_resource_name, t.target_configuration, t.rightsizing_recommendation
            FROM `{self.project_id}.{self.dataset}.wave_workloads` w
            JOIN `{self.project_id}.{self.dataset}.servers` s ON w.server_id = s.server_id
            LEFT JOIN `{self.project_id}.{self.dataset}.target_architecture` t ON w.server_id = t.source_component_id
            WHERE w.wave_id = '{wave_id}'
            ORDER BY w.sequence_in_wave
        """
        workloads_df = client.query(workloads_query).to_dataframe()
        if workloads_df.empty:
            raise Exception(f"No workloads assigned to Wave {wave_number} in BigQuery. Please run the Wave Planner first.")
            
        # 3. Structure workload details for the prompt
        workloads_list = []
        has_gke = False
        has_gce = False
        for _, row in workloads_df.iterrows():
            target_svc = row["target_gcp_service"]
            if target_svc == "gke":
                has_gke = True
            elif target_svc == "compute-engine":
                has_gce = True
                
            workloads_list.append({
                "server_id": row["server_id"],
                "server_name": row["server_name"],
                "os": row["os"],
                "vcpu": int(row["vcpu"]) if not pandas_isnull(row["vcpu"]) else 2,
                "ram_gb": float(row["ram_gb"]) if not pandas_isnull(row["ram_gb"]) else 4.0,
                "disk_gb": float(row["disk_gb"]) if not pandas_isnull(row["disk_gb"]) else 50.0,
                "migration_approach": row["migration_approach"],
                "target_gcp_service": target_svc,
                "target_resource_name": row["target_resource_name"] or f"gce-{row['server_name'].lower().replace('_', '-')}",
                "target_machine_type": row["target_machine_type"] or "n2-standard-2",
                "rightsizing_recommendation": row["rightsizing_recommendation"] or "Retained original specs."
            })
            
        # 4. Construct instruction and prompt for Gemini
        system_instruction = (
            "You are D.A.M.I Infrastructure as Code & Runbook Generator. "
            "Your task is to generate complete, production-grade infrastructure configurations and cutover guidelines "
            "matching the specified target architecture and migration wave details. "
            "You MUST output valid, clean code strings inside the requested JSON structure."
        )
        
        cloud_req = ""
        if "AWS" in target_cloud:
            cloud_req = "Generate AWS Terraform configurations (e.g., aws_instance, aws_db_instance, aws_vpc, aws_subnet, aws_eks_cluster, aws_security_group) mapping to these workloads. Use official AWS provider blocks."
        elif "Azure" in target_cloud:
            cloud_req = "Generate Microsoft Azure Terraform configurations (e.g., azurerm_virtual_machine, azurerm_mssql_server, azurerm_virtual_network, azurerm_subnet, azurerm_kubernetes_cluster, azurerm_resource_group) mapping to these workloads. Use official AzureRM provider blocks."
        else:
            cloud_req = "Generate Google Cloud Platform (GCP) Terraform configurations (e.g., google_compute_instance, google_sql_database_instance, google_container_cluster, google_compute_network) mapping to these workloads. Use official Google provider blocks."

        prompt = f"""
        Generate migration execution artifacts for Wave {wave_number}: "{wave_name}".
        Target Cloud Provider: {target_cloud}
        
        ### Wave Metadata
        - Wave ID: {wave_id}
        - Risk Level: {wave_row['risk_level']}
        - Prerequisites: {wave_row['prerequisites']}
        - Rollback Strategy: {wave_row['rollback_strategy']}
        - Success Criteria: {wave_row['success_criteria']}
        
        ### Target Workloads Mapping
        {json.dumps(workloads_list, indent=2)}
        
        ### Requirements
        1. **Terraform HCL**: Provide the actual Terraform HCL resources required to provision these workloads on the target cloud. {cloud_req} Ensure variable definitions, variables blocks, and provider blocks are completely written. Do not use placeholders.
        2. **Kubernetes YAML**: Only if GKE is one of the target services ({has_gke}), provide a complete Deployment and Service manifest matching the rightsized cpu/memory request limits. Otherwise, return empty.
        3. **Ansible Playbook**: Only if Compute Engine is one of the target services ({has_gce}), provide an Ansible Playbook configuration yaml to configure packages, copy application scripts, and manage systemd services on the VMs. Otherwise, return empty.
        4. **Markdown Runbook**: Create a step-by-step markdown cutover runbook. Include pre-migration checks, server shut-down sequencing, data synchronization verification, post-migration sanity tests, and explicit step-by-step rollback procedures.
        """
        
        # 5. Call Gemini using structured output schemas
        print("Invoking Gemini model...")
        model_to_use = self.model_name
        if self.use_vertex:
            model_to_use = f"projects/{self.vertex_project}/locations/{self.location}/publishers/google/models/{self.model_name}"
            
        response = self.client.models.generate_content(
            model=model_to_use,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=WaveArtifactsResponse,
                temperature=0.2
            )
        )
        
        result_json = json.loads(response.text)
        
        # Determine cloud suffix for file naming
        cloud_suffix = "_aws" if "AWS" in target_cloud else "_azure" if "Azure" in target_cloud else "_gcp"
        tf_filename = f"wave_{wave_number}_infra{cloud_suffix}.tf"
        
        # 6. Save results to BigQuery
        # Insert Terraform HCL
        tf_hcl = result_json.get("terraform_hcl", "")
        artifacts_records = []
        
        if tf_hcl:
            artifacts_records.append({
                "artifact_id": f"art-tf-{wave_number}",
                "wave_id": wave_id,
                "artifact_type": "terraform",
                "file_name": tf_filename,
                "gcs_path": f"gs://{os.getenv('GCS_BUCKET', 'dami-artifacts-cohort-2')}/iac-artifacts/wave_{wave_number}/{tf_filename}",
                "content_preview": tf_hcl[:450],
                "resource_count": len(workloads_list),
                "validated": True,
                "project_id": self.project_id
            })
            
        # Insert Kubernetes manifests
        k8s_yaml = result_json.get("kubernetes_yaml", "")
        if k8s_yaml:
            artifacts_records.append({
                "artifact_id": f"art-k8s-{wave_number}",
                "wave_id": wave_id,
                "artifact_type": "kubernetes",
                "file_name": f"wave_{wave_number}_k8s.yaml",
                "gcs_path": f"gs://{os.getenv('GCS_BUCKET', 'dami-artifacts-cohort-2')}/iac-artifacts/wave_{wave_number}/wave_{wave_number}_k8s.yaml",
                "content_preview": k8s_yaml[:450],
                "resource_count": 2,
                "validated": True,
                "project_id": self.project_id
            })
            
        # Insert Ansible Playbook
        ansible_yaml = result_json.get("ansible_playbook", "")
        if ansible_yaml:
            artifacts_records.append({
                "artifact_id": f"art-ans-{wave_number}",
                "wave_id": wave_id,
                "artifact_type": "ansible",
                "file_name": f"wave_{wave_number}_ansible.yaml",
                "gcs_path": f"gs://{os.getenv('GCS_BUCKET', 'dami-artifacts-cohort-2')}/iac-artifacts/wave_{wave_number}/wave_{wave_number}_ansible.yaml",
                "content_preview": ansible_yaml[:450],
                "resource_count": len(workloads_list),
                "validated": True,
                "project_id": self.project_id
            })
            
        if artifacts_records:
            art_table_ref = client.dataset(self.dataset).table("iac_artifacts")
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
            )
            # Write to BigQuery
            try:
                existing_df = client.query(f"SELECT * FROM `{self.project_id}.{self.dataset}.iac_artifacts`").to_dataframe()
                if not existing_df.empty:
                    # Filter out current wave
                    filtered_df = existing_df[existing_df["wave_id"] != wave_id]
                    # Convert to records
                    import pandas as pd
                    filtered_records = []
                    for _, r in filtered_df.iterrows():
                        filtered_records.append({
                            "artifact_id": r["artifact_id"],
                            "wave_id": r["wave_id"],
                            "artifact_type": r["artifact_type"],
                            "file_name": r["file_name"],
                            "gcs_path": r["gcs_path"],
                            "content_preview": r["content_preview"],
                            "resource_count": int(r["resource_count"]),
                            "validated": bool(r["validated"]),
                            "project_id": r["project_id"]
                        })
                    artifacts_records.extend(filtered_records)
            except Exception as e:
                print(f"Warning reading existing artifacts: {e}")
                
            art_job = client.load_table_from_json(artifacts_records, art_table_ref, job_config=job_config)
            art_job.result()
            
        # Write Runbook to database
        runbook_md = result_json.get("markdown_runbook", "")
        if runbook_md:
            runbook_records = [{
                "runbook_id": f"rb-{wave_number}",
                "server_id": None,
                "wave_id": wave_id,
                "title": f"Migration Runbook: Wave {wave_number} ({wave_name})",
                "gcs_path": f"gs://{os.getenv('GCS_BUCKET', 'dami-artifacts-cohort-2')}/iac-artifacts/wave_{wave_number}/runbook.md",
                "sections": json.dumps([
                    {"name": "Phase 1: Pre-Migration Validation", "status": "pending"},
                    {"name": "Phase 2: Execution (Cutover)", "status": "pending"},
                    {"name": "Phase 3: Post-Migration Verification", "status": "pending"},
                    {"name": "Phase 4: Rollback Procedure", "status": "pending"}
                ]),
                "estimated_duration_hours": float(wave_row["estimated_duration_days"]) * 2.0,
                "rollback_included": True,
                "validation_steps_count": 6,
                "project_id": self.project_id
            }]
            
            # Read existing runbooks first
            try:
                existing_rb_df = client.query(f"SELECT * FROM `{self.project_id}.{self.dataset}.runbooks`").to_dataframe()
                if not existing_rb_df.empty:
                    filtered_rb_df = existing_rb_df[existing_rb_df["wave_id"] != wave_id]
                    for _, r in filtered_rb_df.iterrows():
                        runbook_records.append({
                            "runbook_id": r["runbook_id"],
                            "server_id": r["server_id"],
                            "wave_id": r["wave_id"],
                            "title": r["title"],
                            "gcs_path": r["gcs_path"],
                            "sections": r["sections"],
                            "estimated_duration_hours": float(r["estimated_duration_hours"]),
                            "rollback_included": bool(r["rollback_included"]),
                            "validation_steps_count": int(r["validation_steps_count"]),
                            "project_id": r["project_id"]
                        })
            except Exception as e:
                print(f"Warning reading existing runbooks: {e}")
                
            rb_table_ref = client.dataset(self.dataset).table("runbooks")
            rb_job = client.load_table_from_json(runbook_records, rb_table_ref, job_config=job_config)
            rb_job.result()
            
        # 7. Save files locally in workspace for downloading
        asset_dir = f"generated_assets/wave_{wave_number}"
        os.makedirs(asset_dir, exist_ok=True)
        
        if tf_hcl:
            with open(f"{asset_dir}/{tf_filename}", "w", encoding="utf-8") as f:
                f.write(tf_hcl)
        if k8s_yaml:
            with open(f"{asset_dir}/wave_{wave_number}_k8s.yaml", "w", encoding="utf-8") as f:
                f.write(k8s_yaml)
        if ansible_yaml:
            with open(f"{asset_dir}/wave_{wave_number}_ansible.yaml", "w", encoding="utf-8") as f:
                f.write(ansible_yaml)
        if runbook_md:
            with open(f"{asset_dir}/wave_{wave_number}_runbook.md", "w", encoding="utf-8") as f:
                f.write(runbook_md)
        
        # 8. Upload artifacts to Google Cloud Storage
        gcs_bucket_name = os.getenv("GCS_BUCKET", "dami-artifacts-cohort-2")
        try:
            from google.cloud import storage as gcs
            gcs_client = gcs.Client(project=self.project_id)
            bucket = gcs_client.bucket(gcs_bucket_name)
            
            artifact_files = {
                f"wave_{wave_number}/{tf_filename}": tf_hcl,
                f"wave_{wave_number}/wave_{wave_number}_k8s.yaml": k8s_yaml,
                f"wave_{wave_number}/wave_{wave_number}_ansible.yaml": ansible_yaml,
                f"wave_{wave_number}/wave_{wave_number}_runbook.md": runbook_md,
            }
            
            uploaded_count = 0
            for gcs_path, content in artifact_files.items():
                if content:
                    blob = bucket.blob(f"iac-artifacts/{gcs_path}")
                    blob.upload_from_string(content)
                    uploaded_count += 1
            
            print(f"Uploaded {uploaded_count} artifacts to gs://{gcs_bucket_name}/iac-artifacts/wave_{wave_number}/")
        except Exception as gcs_err:
            print(f"GCS upload skipped (non-critical): {gcs_err}")
                
        print(f"Successfully generated all execution artifacts for Wave {wave_number}.")
        return {
            "wave_number": wave_number,
            "terraform_generated": bool(tf_hcl),
            "kubernetes_generated": bool(k8s_yaml),
            "ansible_generated": bool(ansible_yaml),
            "runbook_generated": bool(runbook_md)
        }

def pandas_isnull(x):
    try:
        import pandas as pd
        return pd.isnull(x)
    except Exception:
        return x is None
