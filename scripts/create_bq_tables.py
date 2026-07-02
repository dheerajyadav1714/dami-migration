# create_bq_tables.py
import os
import sys
from google.cloud import bigquery
from dotenv import load_dotenv

# Ensure schemas directory is in import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas.bigquery_schemas import DATASET_NAME, TABLES_SQL

def main():
    # Load environment variables
    load_dotenv()
    project_id = os.getenv("GCP_PROJECT_ID")
    region = os.getenv("GCP_REGION", "us-central1")

    if not project_id:
        print("Error: GCP_PROJECT_ID environment variable not set in .env")
        sys.exit(1)

    print(f"Initializing BigQuery dataset and tables in project '{project_id}'...")

    # Construct BigQuery client
    client = bigquery.Client(project=project_id)

    # Define dataset ID and reference
    dataset_id = f"{project_id}.{DATASET_NAME}"
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = region

    # Create dataset if not exists
    try:
        dataset = client.create_dataset(dataset, timeout=30, exists_ok=True)
        print(f"Dataset '{dataset_id}' in location '{region}' is ready.")
    except Exception as e:
        print(f"Failed to create dataset: {e}")
        sys.exit(1)

    # Create tables
    success_count = 0
    fail_count = 0

    for table_name, sql_template in TABLES_SQL.items():
        # Format the SQL statement with current project_id and dataset
        sql = sql_template.format(project_id=project_id, dataset=DATASET_NAME)
        
        try:
            print(f"Creating table '{table_name}'...")
            query_job = client.query(sql)
            query_job.result()  # Wait for query to complete
            print(f"Table '{table_name}' created or already exists.")
            success_count += 1
        except Exception as e:
            print(f"Failed to create table '{table_name}': {e}")
            fail_count += 1

    print("\nInitialization Summary:")
    print(f"Successful table operations: {success_count}/{len(TABLES_SQL)}")
    if fail_count > 0:
        print(f"Failed table operations: {fail_count}")
        sys.exit(1)
    else:
        print("All BigQuery tables created successfully!")

if __name__ == "__main__":
    main()
