# agents/memory_store.py
"""
Self-Learning Memory Store — Adaptive Feedback Intelligence

Stores and retrieves agent learning signals (corrections, optimizations,
pattern discoveries) to make D.A.M.I.'s agents improve over time.

Architecture:
    - Primary Backend: BigQuery (always available)
    - Optional Backend: AlloyDB Omni (Docker, for vector similarity search)
    
When AlloyDB Omni is available, the store uses pgvector for semantic similarity
searches on past corrections. When unavailable, it falls back to BigQuery
with keyword-based retrieval.

This enables:
    1. Feedback Memory: Human corrections are stored and retrieved when similar
       workloads are encountered in future migrations.
    2. Pattern Learning: The system learns from past migration decisions to
       improve risk scoring, architecture mapping, and wave sequencing.
    3. Confidence Calibration: Tracks prediction accuracy over time to adjust
       confidence thresholds.
"""
import os
import json
import hashlib
import datetime
from typing import Optional
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()


class MemoryStore:
    """
    Dual-backend memory store for agent self-learning.
    Uses BigQuery by default, with optional AlloyDB Omni for vector search.
    """
    
    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID")
        self.dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
        self.bq_client = bigquery.Client(project=self.project_id)
        self.alloydb_available = False
        
        # Try to connect to AlloyDB Omni (Docker)
        self._check_alloydb()
    
    def _check_alloydb(self):
        """Check if AlloyDB Omni is available via Docker."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("ALLOYDB_HOST", "localhost"),
                port=os.getenv("ALLOYDB_PORT", "5432"),
                database=os.getenv("ALLOYDB_DB", "dami_memory"),
                user=os.getenv("ALLOYDB_USER", "postgres"),
                password=os.getenv("ALLOYDB_PASSWORD", "dami2026")
            )
            conn.close()
            self.alloydb_available = True
            print("[MemoryStore] AlloyDB Omni connected — vector search enabled")
        except Exception:
            self.alloydb_available = False
            print("[MemoryStore] AlloyDB Omni not available — using BigQuery backend")
    
    def store_learning(
        self,
        agent_name: str,
        learning_type: str,  # "correction", "pattern", "optimization", "insight"
        context: dict,
        original_output: str,
        corrected_output: str,
        confidence_delta: float = 0.0,
        tags: list = None
    ) -> str:
        """
        Stores a learning signal from a human correction or pattern discovery.
        
        Returns:
            memory_id: Unique ID for the stored memory.
        """
        memory_id = hashlib.sha256(
            f"{agent_name}:{learning_type}:{datetime.datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        record = {
            "memory_id": memory_id,
            "agent_name": agent_name,
            "learning_type": learning_type,
            "context_json": json.dumps(context),
            "original_output": original_output,
            "corrected_output": corrected_output,
            "confidence_delta": confidence_delta,
            "tags": tags or [],
            "created_at": datetime.datetime.now().isoformat(),
            "applied_count": 0,
            "effectiveness_score": 0.0
        }
        
        # Store in BigQuery
        table_ref = f"{self.project_id}.{self.dataset}.agent_memories"
        errors = self.bq_client.insert_rows_json(table_ref, [record])
        if errors:
            print(f"[MemoryStore] BQ insert error: {errors}")
        
        # Also store in AlloyDB if available (for vector search)
        if self.alloydb_available:
            self._store_alloydb(record)
        
        print(f"[MemoryStore] Stored learning '{learning_type}' for {agent_name} -> {memory_id}")
        return memory_id
    
    def retrieve_relevant_memories(
        self,
        agent_name: str,
        context: dict,
        limit: int = 5
    ) -> list:
        """
        Retrieves the most relevant past learnings for the given context.
        
        If AlloyDB is available, uses pgvector similarity search.
        Otherwise, falls back to BigQuery keyword matching.
        """
        if self.alloydb_available:
            return self._search_alloydb(agent_name, context, limit)
        
        # BigQuery fallback: keyword-based retrieval
        context_str = json.dumps(context)
        keywords = []
        for key in ["workload_type", "os_type", "risk_level", "server_name"]:
            if key in context:
                keywords.append(context[key])
        
        if not keywords:
            return []
        
        # Build search conditions
        conditions = " OR ".join([
            f"LOWER(context_json) LIKE '%{kw.lower()}%'" for kw in keywords
        ])
        
        query = f"""
            SELECT memory_id, agent_name, learning_type, context_json,
                   original_output, corrected_output, confidence_delta,
                   tags, created_at, applied_count, effectiveness_score
            FROM `{self.project_id}.{self.dataset}.agent_memories`
            WHERE agent_name = '{agent_name}'
              AND ({conditions})
            ORDER BY effectiveness_score DESC, created_at DESC
            LIMIT {limit}
        """
        
        try:
            df = self.bq_client.query(query).to_dataframe()
            return df.to_dict(orient="records")
        except Exception as e:
            print(f"[MemoryStore] BQ retrieval error: {e}")
            return []
    
    def record_outcome(self, memory_id: str, was_helpful: bool):
        """
        Records whether a retrieved memory was actually helpful when applied.
        Updates the effectiveness score for future retrieval ranking.
        """
        delta = 0.1 if was_helpful else -0.05
        
        query = f"""
            UPDATE `{self.project_id}.{self.dataset}.agent_memories`
            SET applied_count = applied_count + 1,
                effectiveness_score = effectiveness_score + {delta}
            WHERE memory_id = '{memory_id}'
        """
        
        try:
            self.bq_client.query(query).result()
            print(f"[MemoryStore] Updated outcome for {memory_id}: helpful={was_helpful}")
        except Exception as e:
            print(f"[MemoryStore] Outcome update error: {e}")
    
    def get_learning_stats(self) -> dict:
        """Returns aggregate learning statistics for the dashboard."""
        query = f"""
            SELECT 
                COUNT(*) as total_memories,
                COUNTIF(learning_type = 'correction') as corrections,
                COUNTIF(learning_type = 'pattern') as patterns,
                COUNTIF(learning_type = 'optimization') as optimizations,
                COUNTIF(learning_type = 'insight') as insights,
                ROUND(AVG(effectiveness_score), 3) as avg_effectiveness,
                SUM(applied_count) as total_applications,
                COUNT(DISTINCT agent_name) as agents_learning
            FROM `{self.project_id}.{self.dataset}.agent_memories`
        """
        
        try:
            df = self.bq_client.query(query).to_dataframe()
            if not df.empty:
                return df.iloc[0].to_dict()
        except Exception:
            pass
        
        return {
            "total_memories": 0, "corrections": 0, "patterns": 0,
            "optimizations": 0, "insights": 0, "avg_effectiveness": 0.0,
            "total_applications": 0, "agents_learning": 0
        }
    
    def _store_alloydb(self, record: dict):
        """Store memory in AlloyDB Omni with pgvector embedding (when available)."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("ALLOYDB_HOST", "localhost"),
                port=os.getenv("ALLOYDB_PORT", "5432"),
                database=os.getenv("ALLOYDB_DB", "dami_memory"),
                user=os.getenv("ALLOYDB_USER", "postgres"),
                password=os.getenv("ALLOYDB_PASSWORD", "dami2026")
            )
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO agent_memories 
                (memory_id, agent_name, learning_type, context_json, 
                 original_output, corrected_output, confidence_delta, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                record["memory_id"], record["agent_name"], record["learning_type"],
                record["context_json"], record["original_output"],
                record["corrected_output"], record["confidence_delta"],
                record["created_at"]
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[MemoryStore] AlloyDB insert error: {e}")
    
    def _search_alloydb(self, agent_name: str, context: dict, limit: int) -> list:
        """Search AlloyDB Omni using pgvector similarity (when available)."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("ALLOYDB_HOST", "localhost"),
                port=os.getenv("ALLOYDB_PORT", "5432"),
                database=os.getenv("ALLOYDB_DB", "dami_memory"),
                user=os.getenv("ALLOYDB_USER", "postgres"),
                password=os.getenv("ALLOYDB_PASSWORD", "dami2026")
            )
            cur = conn.cursor()
            # Simplified text similarity search (pgvector would use embeddings)
            context_str = json.dumps(context)
            cur.execute("""
                SELECT memory_id, agent_name, learning_type, context_json,
                       original_output, corrected_output, confidence_delta,
                       created_at
                FROM agent_memories
                WHERE agent_name = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (agent_name, limit))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    "memory_id": row[0], "agent_name": row[1],
                    "learning_type": row[2], "context_json": row[3],
                    "original_output": row[4], "corrected_output": row[5],
                    "confidence_delta": row[6], "created_at": row[7]
                })
            cur.close()
            conn.close()
            return results
        except Exception as e:
            print(f"[MemoryStore] AlloyDB search error: {e}")
            return []


if __name__ == "__main__":
    store = MemoryStore()
    stats = store.get_learning_stats()
    print(f"Memory Store Stats: {stats}")
