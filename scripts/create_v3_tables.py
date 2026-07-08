"""
Create dami_data_v3 dataset and tables for refinement-v3 enhancements.

This dataset is ISOLATED from the submitted service's dami_data dataset.
All new feature writes go here; existing dami_data is READ-ONLY.

Usage:
    python scripts/create_v3_tables.py
"""
import os
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "cohort-2-497207")
DATASET_V3 = os.getenv("BIGQUERY_DATASET_V3", "dami_data_v3")
LOCATION = "US"


def create_dataset(client: bigquery.Client):
    """Create dami_data_v3 dataset if it doesn't exist."""
    dataset_ref = f"{PROJECT_ID}.{DATASET_V3}"
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = LOCATION
    dataset.description = (
        "D.A.M.I. refinement-v3 enhancement data. "
        "Isolated from submitted dami_data dataset."
    )
    try:
        client.create_dataset(dataset, exists_ok=True)
        print(f"[OK] Dataset '{dataset_ref}' ready")
    except Exception as e:
        print(f"[ERROR] Failed to create dataset: {e}")
        raise


def create_gpu_benchmarks_table(client: bigquery.Client):
    """Create gpu_benchmarks table for real Dataproc + Colab GPU results."""
    table_id = f"{PROJECT_ID}.{DATASET_V3}.gpu_benchmarks"
    schema = [
        bigquery.SchemaField("benchmark_id", "STRING", mode="REQUIRED",
                             description="Unique benchmark run identifier"),
        bigquery.SchemaField("method", "STRING", mode="REQUIRED",
                             description="Processing method: spark_rapids, cudf_pandas, pandas_cpu"),
        bigquery.SchemaField("rows_processed", "INTEGER", mode="REQUIRED",
                             description="Number of rows processed in benchmark"),
        bigquery.SchemaField("processing_seconds", "FLOAT", mode="REQUIRED",
                             description="Wall-clock processing time in seconds"),
        bigquery.SchemaField("speedup_factor", "FLOAT", mode="NULLABLE",
                             description="Speedup vs CPU baseline (e.g., 25.3x)"),
        bigquery.SchemaField("gpu_device", "STRING", mode="NULLABLE",
                             description="GPU device name (e.g., NVIDIA T4)"),
        bigquery.SchemaField("platform", "STRING", mode="NULLABLE",
                             description="Execution platform: dataproc_serverless, colab, local"),
        bigquery.SchemaField("job_id", "STRING", mode="NULLABLE",
                             description="Dataproc batch job ID for traceability"),
        bigquery.SchemaField("details_json", "STRING", mode="NULLABLE",
                             description="Additional benchmark details as JSON"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED",
                             description="When the benchmark was recorded"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Real GPU benchmark results from Dataproc Serverless + Colab"
    try:
        client.create_table(table, exists_ok=True)
        print(f"[OK] Table '{table_id}' ready")
    except Exception as e:
        print(f"[ERROR] Failed to create gpu_benchmarks table: {e}")
        raise


def create_agent_memories_v3_table(client: bigquery.Client):
    """Create enhanced agent_memories table for self-learning tracking."""
    table_id = f"{PROJECT_ID}.{DATASET_V3}.agent_memories_v3"
    schema = [
        bigquery.SchemaField("memory_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("learning_type", "STRING", mode="REQUIRED",
                             description="correction, pattern, optimization, insight"),
        bigquery.SchemaField("context_json", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("original_output", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("corrected_output", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("confidence_delta", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("tags", "STRING", mode="REPEATED"),
        bigquery.SchemaField("applied_count", "INTEGER", mode="NULLABLE",
                             description="How many times this memory was applied"),
        bigquery.SchemaField("effectiveness_score", "FLOAT", mode="NULLABLE",
                             description="Cumulative effectiveness score"),
        bigquery.SchemaField("last_applied_at", "TIMESTAMP", mode="NULLABLE",
                             description="When this memory was last applied to an agent"),
        bigquery.SchemaField("applied_by_agents", "STRING", mode="REPEATED",
                             description="List of agent names that used this memory"),
        bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Enhanced self-learning memories with application tracking"
    try:
        client.create_table(table, exists_ok=True)
        print(f"[OK] Table '{table_id}' ready")
    except Exception as e:
        print(f"[ERROR] Failed to create agent_memories_v3 table: {e}")
        raise


def main():
    print(f"[SETUP] Setting up dami_data_v3 in project '{PROJECT_ID}'...\n")
    client = bigquery.Client(project=PROJECT_ID)

    create_dataset(client)
    create_gpu_benchmarks_table(client)
    create_agent_memories_v3_table(client)

    print(f"\n[DONE] All dami_data_v3 tables ready. Isolation setup complete.")
    print(f"   Read from: dami_data (existing, read-only)")
    print(f"   Write to:  dami_data_v3 (new, isolated)")


if __name__ == "__main__":
    main()
