# agents/trace_logger.py
"""
Agent Execution Trace Logger
Records every agent invocation into BigQuery `agent_execution_logs` table
for the Agent Transparency Dashboard.
"""
import os
import uuid
import time
import datetime
from contextlib import contextmanager
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

# Global run_id shared across a single orchestration pass
_current_run_id = None

def new_run_id():
    global _current_run_id
    _current_run_id = f"run-{uuid.uuid4().hex[:12]}"
    return _current_run_id

def get_run_id():
    global _current_run_id
    if _current_run_id is None:
        new_run_id()
    return _current_run_id

class TraceLogger:
    """Records agent execution traces to BigQuery."""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
        self.table_id = f"{self.project_id}.{self.dataset}.agent_execution_logs"
        try:
            self.client = bigquery.Client(project=self.project_id)
        except Exception:
            self.client = None

    def log(self, trace_id: str, run_id: str, agent_name: str,
            agent_type: str, phase: str, status: str,
            started_at: datetime.datetime, completed_at: datetime.datetime,
            duration_ms: int, input_summary: str = "",
            output_summary: str = "", tools_called: list = None,
            records_processed: int = 0, error_message: str = ""):
        """Write a single trace entry to BigQuery."""
        row = {
            "trace_id": trace_id,
            "run_id": run_id,
            "agent_name": agent_name,
            "agent_type": agent_type,
            "phase": phase,
            "status": status,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "duration_ms": duration_ms,
            "input_summary": input_summary[:500] if input_summary else "",
            "output_summary": output_summary[:500] if output_summary else "",
            "tools_called": tools_called or [],
            "records_processed": records_processed,
            "error_message": error_message[:500] if error_message else "",
            "project_id": self.project_id
        }
        if self.client:
            try:
                import io
                import json as _json
                # Use load_table (batch) instead of streaming insert (free tier compatible)
                job_config = bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND
                )
                json_str = _json.dumps(row) + "\n"
                data_file = io.BytesIO(json_str.encode())
                job = self.client.load_table_from_file(
                    data_file, self.table_id, job_config=job_config
                )
                job.result()  # Wait for completion
            except Exception as e:
                print(f"TraceLogger BQ write note: {e}")
        # Always print for console visibility (ASCII-safe for Windows)
        status_icon = "[OK]" if status == "success" else "[ERR]" if status == "error" else "[...]"
        safe_summary = output_summary[:80].encode('ascii', 'replace').decode('ascii') if output_summary else ""
        print(f"  {status_icon} [{agent_name}] {phase} - {duration_ms}ms - {safe_summary}")

# Singleton logger
_logger = None

def get_logger() -> TraceLogger:
    global _logger
    if _logger is None:
        _logger = TraceLogger()
    return _logger

@contextmanager
def trace_agent(agent_name: str, agent_type: str, phase: str,
                input_summary: str = "", tools: list = None):
    """
    Context manager to automatically trace agent execution.
    
    Usage:
        with trace_agent("DiscoveryAgent", "specialist", "assess", "Processing 100 VMs") as trace:
            result = agent.run()
            trace["output_summary"] = f"Loaded {result['count']} servers"
            trace["records_processed"] = result['count']
    """
    logger = get_logger()
    run_id = get_run_id()
    trace_id = f"trc-{uuid.uuid4().hex[:12]}"
    started_at = datetime.datetime.now(datetime.timezone.utc)

    trace_data = {
        "output_summary": "",
        "records_processed": 0,
        "error_message": "",
        "status": "success"
    }

    try:
        yield trace_data
    except Exception as e:
        trace_data["status"] = "error"
        trace_data["error_message"] = str(e)
        raise
    finally:
        completed_at = datetime.datetime.now(datetime.timezone.utc)
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)

        logger.log(
            trace_id=trace_id,
            run_id=run_id,
            agent_name=agent_name,
            agent_type=agent_type,
            phase=phase,
            status=trace_data["status"],
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            input_summary=input_summary,
            output_summary=trace_data["output_summary"],
            tools_called=tools or [],
            records_processed=trace_data["records_processed"],
            error_message=trace_data["error_message"]
        )
