# bigquery_schemas.py
# Define all table creation statements for the D.A.M.I. migration intelligence platform.

DATASET_NAME = "dami_data"

TABLES_SQL = {
    # DOMAIN 1: INVENTORY
    "servers": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.servers` (
          server_id STRING NOT NULL,
          name STRING,
          vcpu INT64,
          ram_gb FLOAT64,
          disk_gb FLOAT64,
          os STRING,
          os_version STRING,
          ip_address STRING,
          cluster STRING,
          datacenter STRING,
          power_state STRING,
          cpu_utilization_avg FLOAT64,
          ram_utilization_avg FLOAT64,
          disk_iops_avg FLOAT64,
          network_throughput_mbps FLOAT64,
          workload_type STRING,
          app_owner STRING,
          environment STRING,
          source_platform STRING,
          last_access_days INT64,
          eol_date DATE,
          compliance_flags ARRAY<STRING>,
          tags JSON,
          project_id STRING,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        );
    """,
    "applications": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.applications` (
          app_id STRING NOT NULL,
          name STRING,
          tier STRING,
          tech_stack ARRAY<STRING>,
          framework STRING,
          language STRING,
          owner STRING,
          business_unit STRING,
          business_criticality INT64,
          sla_requirement STRING,
          compliance_flags ARRAY<STRING>,
          data_classification STRING,
          server_ids ARRAY<STRING>,
          annual_revenue_impact FLOAT64,
          user_count INT64,
          project_id STRING
        );
    """,
    "databases": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.databases` (
          db_id STRING NOT NULL,
          name STRING,
          db_engine STRING,
          version STRING,
          edition STRING,
          size_gb FLOAT64,
          table_count INT64,
          connection_count INT64,
          has_stored_procedures BOOL,
          has_custom_extensions BOOL,
          has_linked_servers BOOL,
          replication_type STRING,
          backup_frequency STRING,
          rpo_hours FLOAT64,
          rto_hours FLOAT64,
          licensing_model STRING,
          server_id STRING,
          project_id STRING
        );
    """,

    # DOMAIN 2: DEPENDENCIES
    "app_dependencies": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.app_dependencies` (
          dep_id STRING NOT NULL,
          source_app_id STRING,
          target_app_id STRING,
          protocol STRING,
          port INT64,
          traffic_volume STRING,
          latency_sensitivity STRING,
          dependency_type STRING,
          data_flow_direction STRING,
          project_id STRING
        );
    """,
    "app_db_dependencies": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.app_db_dependencies` (
          app_id STRING,
          db_id STRING,
          connection_type STRING,
          query_pattern STRING,
          project_id STRING
        );
    """,
    "shared_services": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.shared_services` (
          service_id STRING NOT NULL,
          service_name STRING,
          service_type STRING,
          ip_address STRING,
          port INT64,
          used_by_count INT64,
          migration_strategy STRING,
          gcp_equivalent STRING,
          project_id STRING
        );
    """,

    # DOMAIN 3: ASSESSMENT & PLANNING
    "risk_scores": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.risk_scores` (
          assessment_id STRING NOT NULL,
          server_id STRING,
          app_id STRING,
          complexity_score FLOAT64,
          business_criticality FLOAT64,
          technical_risk FLOAT64,
          dependency_risk FLOAT64,
          data_sensitivity_risk FLOAT64,
          compliance_risk FLOAT64,
          overall_risk_score FLOAT64,
          risk_level STRING,
          recommended_strategy STRING,
          strategy_rationale STRING,
          alternative_strategy STRING,
          estimated_effort_days INT64,
          estimated_downtime_hours FLOAT64,
          requires_code_change BOOL,
          requires_data_migration BOOL,
          requires_network_change BOOL,
          project_id STRING,
          assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        );
    """,
    "waves": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.waves` (
          wave_id STRING NOT NULL,
          wave_number INT64,
          wave_name STRING,
          wave_type STRING,
          estimated_start_date DATE,
          estimated_end_date DATE,
          estimated_duration_days INT64,
          rationale STRING,
          risk_level STRING,
          workload_count INT64,
          total_servers INT64,
          total_databases INT64,
          prerequisites STRING,
          success_criteria STRING,
          rollback_strategy STRING,
          project_id STRING
        );
    """,
    "wave_workloads": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.wave_workloads` (
          wave_id STRING,
          server_id STRING,
          app_id STRING,
          sequence_in_wave INT64,
          migration_approach STRING,
          target_gcp_service STRING,
          target_machine_type STRING,
          target_region STRING,
          prerequisites ARRAY<STRING>,
          estimated_hours FLOAT64,
          project_id STRING
        );
    """,
    "target_architecture": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.target_architecture` (
          mapping_id STRING NOT NULL,
          source_component_id STRING,
          source_component_type STRING,
          source_technology STRING,
          target_gcp_service STRING,
          target_resource_name STRING,
          target_machine_type STRING,
          target_region STRING,
          target_configuration JSON,
          rightsizing_recommendation STRING,
          cost_estimate_monthly FLOAT64,
          project_id STRING
        );
    """,

    # DOMAIN 4: GENERATED ARTIFACTS
    "iac_artifacts": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.iac_artifacts` (
          artifact_id STRING NOT NULL,
          wave_id STRING,
          artifact_type STRING,
          file_name STRING,
          gcs_path STRING,
          content_preview STRING,
          resource_count INT64,
          validated BOOL,
          project_id STRING,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        );
    """,
    "runbooks": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.runbooks` (
          runbook_id STRING NOT NULL,
          server_id STRING,
          wave_id STRING,
          title STRING,
          gcs_path STRING,
          sections JSON,
          estimated_duration_hours FLOAT64,
          rollback_included BOOL,
          validation_steps_count INT64,
          project_id STRING,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        );
    """,
    "diagrams": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.diagrams` (
          diagram_id STRING NOT NULL,
          diagram_type STRING,
          format STRING,
          gcs_path STRING,
          project_id STRING,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        );
    """,

    # DOMAIN 5: PROJECTS & FEEDBACK
    "projects": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.projects` (
          project_id STRING NOT NULL,
          name STRING,
          client_name STRING,
          description STRING,
          status STRING,
          migration_type STRING,
          source_platform STRING,
          target_cloud STRING,
          total_servers INT64,
          total_applications INT64,
          total_databases INT64,
          total_waves INT64,
          current_phase STRING,
          estimated_savings_pct FLOAT64,
          estimated_savings_annual FLOAT64,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        );
    """,
    "feedback": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.feedback` (
          feedback_id STRING NOT NULL,
          feedback_text STRING,
          feedback_type STRING,
          source STRING,
          status STRING,
          affected_component STRING,
          affected_agent STRING,
          validation_result STRING,
          changes_applied STRING,
          conflict_details STRING,
          project_id STRING,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
        );
    """,

    # DOMAIN 6: AGENT OBSERVABILITY
    "agent_execution_logs": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.agent_execution_logs` (
          trace_id STRING NOT NULL,
          run_id STRING NOT NULL,
          agent_name STRING,
          agent_type STRING,
          phase STRING,
          status STRING,
          started_at TIMESTAMP,
          completed_at TIMESTAMP,
          duration_ms INT64,
          input_summary STRING,
          output_summary STRING,
          tools_called ARRAY<STRING>,
          records_processed INT64,
          error_message STRING,
          project_id STRING
        );
    """,

    # DOMAIN 7: SELF-LEARNING MEMORY
    "agent_memories": """
        CREATE TABLE IF NOT EXISTS `{project_id}.{dataset}.agent_memories` (
          memory_id STRING NOT NULL,
          agent_name STRING,
          learning_type STRING,
          context_json STRING,
          original_output STRING,
          corrected_output STRING,
          confidence_delta FLOAT64,
          tags ARRAY<STRING>,
          created_at STRING,
          applied_count INT64 DEFAULT 0,
          effectiveness_score FLOAT64 DEFAULT 0.0
        );
    """
}
