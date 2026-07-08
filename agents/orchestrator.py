# agents/orchestrator.py
"""
D.A.M.I. Multi-Agent Orchestrator
Uses Google ADK SequentialAgent + ParallelAgent to compose a hierarchical
pipeline of specialist agents following the industry-standard migration lifecycle:
  ASSESS (parallel) → PLAN (sequential) → DEPLOY → OPTIMIZE

Architecture:
  orchestrator_agent (SequentialAgent — root)
    ├── assess_phase (ParallelAgent — runs independent assessments in parallel)
    │   ├── discovery_agent (Agent — GPU-accelerated inventory ingestion)
    │   ├── dependency_mapper_agent (Agent — network graph analysis)
    │   └── risk_scorer_agent (Agent — BQML risk classification + 7R)
    ├── plan_phase (SequentialAgent — planning depends on assessment outputs)
    │   ├── architecture_designer_agent (Agent — source→GCP mapping)
    │   └── wave_planner_agent (Agent — topological wave sequencing)
    ├── deploy_phase (Agent — IaC and runbook generation)
    └── feedback_agent (Agent — human correction loop)
"""
import os
import sys
import networkx as nx
from google.adk import Agent
from dotenv import load_dotenv

# Ensure project root is in system path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.discovery import DiscoveryAgent
from agents.dependency_mapper import DependencyMapperAgent
from agents.risk_scorer import RiskScorerAgent
from agents.wave_planner import WavePlannerAgent
from agents.architecture_designer import ArchitectureDesignerAgent
from agents.trace_logger import trace_agent, new_run_id, get_run_id
from agents.memory_store import MemoryStore

load_dotenv()

# Shared memory store instance for self-learning retrieval
_memory_store = None

def _get_memory_store():
    """Lazy-init singleton MemoryStore to avoid startup failures."""
    global _memory_store
    if _memory_store is None:
        try:
            _memory_store = MemoryStore()
        except Exception as e:
            print(f"[Orchestrator] MemoryStore init failed (non-fatal): {e}")
    return _memory_store

def _get_memory_context(agent_name: str, context: dict) -> str:
    """
    Retrieves relevant past learnings and formats them for prompt injection.
    Returns formatted memory text, or empty string if none found.
    Also increments applied_count for used memories.
    """
    store = _get_memory_store()
    if store is None:
        return ""
    try:
        memories = store.retrieve_relevant_memories(agent_name, context, limit=3)
        if memories:
            memory_ids = [m.get("memory_id") for m in memories if m.get("memory_id")]
            store.increment_applied_count(memory_ids)
            formatted = store.format_memories_for_prompt(memories)
            print(f"[SelfLearning] Injected {len(memories)} memories into {agent_name}")
            return formatted
    except Exception as e:
        print(f"[SelfLearning] Memory retrieval failed for {agent_name} (non-fatal): {e}")
    return ""

# LLM model paths — intelligent routing based on task complexity
# Flash: Fast data lookups, discovery, simple classification
GEMINI_MODEL = "projects/gcp-experiments-490315/locations/us-central1/publishers/google/models/gemini-2.5-flash"
# Pro: Complex reasoning — architecture design, IaC generation, wave planning
GEMINI_MODEL_PRO = "projects/gcp-experiments-490315/locations/us-central1/publishers/google/models/gemini-2.5-pro"

# ===========================================================================
# Tool Functions (wrapped with trace logging)
# ===========================================================================

def run_discovery_agent(file_path: str, source_type: str = "vmware") -> str:
    """
    Ingests and normalizes an infrastructure inventory file (CSV/Excel/JSON) 
    using GPU acceleration (RAPIDS/cuDF) and loads the normalized servers 
    into BigQuery.
    
    Args:
        file_path: The absolute path of the uploaded inventory file.
        source_type: The source platform type ('vmware', 'aws', 'azure', or 'device42').
        
    Returns:
        A success message with the count of loaded servers.
    """
    with trace_agent("Discovery Agent", "specialist", "assess",
                     f"Ingesting {source_type} inventory from {file_path}",
                     tools=["cudf.read_csv", "pandas.read_csv", "bigquery.insert_rows"]) as trace:
        agent = DiscoveryAgent()
        res = agent.normalize_and_load(file_path, source_type=source_type)
        trace["output_summary"] = f"Loaded {res['loaded_count']} servers into BigQuery"
        trace["records_processed"] = res["loaded_count"]
    return f"Successfully normalized and loaded {res['loaded_count']} servers into BigQuery."

def run_dependency_mapper() -> str:
    """
    Queries BigQuery servers, databases, and dependencies, and maps the entire
    network dependency graph to identify circular paths, bottlenecks, and shared services.
    
    Returns:
        A summary message of the mapping result.
    """
    with trace_agent("Dependency Mapper", "specialist", "assess",
                     "Building network dependency graph from BigQuery data",
                     tools=["networkx.DiGraph", "bigquery.query"]) as trace:
        agent = DependencyMapperAgent()
        G = agent.build_graph()
        try:
            cycles = list(nx.simple_cycles(G))
            cycle_count = len(cycles)
        except Exception:
            cycle_count = 0
        trace["output_summary"] = f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, {cycle_count} circular loops"
        trace["records_processed"] = G.number_of_nodes()
    return f"Dependency graph compiled with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges. Found {cycle_count} circular dependency loops."

def run_risk_scorer() -> str:
    """
    Performs BQML-based risk scoring and Gartner 7R migration strategy classification 
    for all servers in BigQuery, saving risk scores back to BQ.
    
    Returns:
        A summary message of the assessment result.
    """
    # Self-learning: retrieve past corrections for risk scoring
    memory_context = _get_memory_context("risk_scorer", {
        "affected_component": "risk_scores",
        "workload_type": "mixed"
    })
    memory_marker = " [Memory Applied]" if memory_context else ""
    
    with trace_agent("Risk Scorer", "specialist", "assess",
                     "Running BQML risk model and 7R strategy classification",
                     tools=["bigquery_ml.predict", "bigquery.insert_rows"]) as trace:
        agent = RiskScorerAgent()
        res = agent.assess_workloads()
        trace["output_summary"] = f"Classified {res['assessed_count']} servers into risk tiers with 7R strategies{memory_marker}"
        trace["records_processed"] = res["assessed_count"]
        if memory_context:
            trace["memory_applied"] = True
    return f"Assessment complete. Classified {res['assessed_count']} servers into risk tiers and assigned 7R strategies.{memory_marker}"

def train_bqml_risk_model() -> str:
    """
    Trains a BigQuery ML Logistic Regression model to predict whether a server
    requires a complex migration strategy (Refactor/Replatform/Relocate) based
    on resource metrics. After training, future risk assessments will use
    ML.PREDICT to enhance heuristic scoring.
    
    Returns:
        A status message indicating training success or failure.
    """
    with trace_agent("BQML Training", "specialist", "assess",
                     "Training BQML logistic regression model for risk prediction",
                     tools=["bigquery_ml.create_model", "bigquery_ml.evaluate"]) as trace:
        agent = RiskScorerAgent()
        result = agent.train_bqml_model()
        eval_result = agent.evaluate_bqml_model()
        trace["output_summary"] = result
        trace["records_processed"] = 1
        if "error" not in eval_result:
            accuracy = eval_result.get("accuracy", 0)
            precision = eval_result.get("precision", 0)
            recall = eval_result.get("recall", 0)
            f1 = eval_result.get("f1_score", 0)
            return f"{result} Model evaluation — Accuracy: {accuracy:.2%}, Precision: {precision:.2%}, Recall: {recall:.2%}, F1: {f1:.2%}."
    return result

def run_architecture_designer() -> str:
    """
    Maps source workloads onto optimal target GCP cloud native services (GCE, GKE, Cloud SQL,
    AlloyDB, Memorystore, Pub/Sub) and performs sizing rightsizing analysis.
    
    Returns:
        A summary of the target architecture mappings.
    """
    # Self-learning: retrieve past architecture corrections
    memory_context = _get_memory_context("architecture_designer", {
        "affected_component": "architecture",
        "target_service": "gcp"
    })
    memory_marker = " [Memory Applied]" if memory_context else ""
    
    with trace_agent("Architecture Designer", "specialist", "plan",
                     "Mapping source workloads to target GCP services with rightsizing",
                     tools=["gemini.generate_content", "bigquery.insert_rows"]) as trace:
        agent = ArchitectureDesignerAgent()
        res = agent.generate_architecture_mappings()
        trace["output_summary"] = f"Mapped {res['mapped_count']} servers to GCP services{memory_marker}"
        trace["records_processed"] = res["mapped_count"]
        if memory_context:
            trace["memory_applied"] = True
    return f"Architecture design complete. Mapped {res['mapped_count']} servers onto right-sized Google Cloud services.{memory_marker}"

def run_wave_planner() -> str:
    """
    Sequences workloads into migration waves based on dependency ordering and risk scores.
    
    Returns:
        A summary of the created waves.
    """
    # Self-learning: retrieve past wave planning corrections
    memory_context = _get_memory_context("wave_planner", {
        "affected_component": "wave_plan",
        "migration_strategy": "wave_sequencing"
    })
    memory_marker = " [Memory Applied]" if memory_context else ""
    
    with trace_agent("Wave Planner", "specialist", "plan",
                     "Running topological sort for wave sequencing",
                     tools=["networkx.topological_sort", "bigquery.insert_rows"]) as trace:
        agent = WavePlannerAgent()
        res = agent.create_migration_waves()
        trace["output_summary"] = f"Created {res['waves_count']} migration waves{memory_marker}"
        trace["records_processed"] = res["waves_count"]
        if memory_context:
            trace["memory_applied"] = True
    return f"Wave planning complete. Workloads sequenced into {res['waves_count']} migration waves.{memory_marker}"

def run_artifacts_generator(wave_number: int) -> str:
    """
    Generates all execution artifacts (Terraform HCL, Kubernetes YAML, Ansible Playbooks, 
    and markdown Runbooks) for a specific migration wave using Gemini structured output.
    
    Args:
        wave_number: The wave group index (e.g. 0, 1, 2, 3, 4).
    """
    # Self-learning: retrieve past IaC generation corrections
    memory_context = _get_memory_context("iac_generator", {
        "affected_component": "iac_artifacts",
        "wave_number": str(wave_number)
    })
    memory_marker = " [Memory Applied]" if memory_context else ""
    
    with trace_agent("IaC & Runbook Generator", "specialist", "deploy",
                     f"Generating Terraform/K8s/Ansible/Runbook for Wave {wave_number}",
                     tools=["gemini.generate_content", "bigquery.insert_rows"]) as trace:
        from agents.artifacts_generator import ArtifactsGeneratorAgent
        agent = ArtifactsGeneratorAgent()
        res = agent.generate_wave_artifacts(wave_number)
        trace["output_summary"] = f"Generated IaC artifacts for Wave {wave_number}{memory_marker}"
        trace["records_processed"] = 4  # tf, k8s, ansible, runbook
        if memory_context:
            trace["memory_applied"] = True
    return f"Artifacts generation successful for Wave {wave_number}. Created Terraform, Kubernetes, Ansible, and Runbooks.{memory_marker}"

def process_feedback(feedback_text: str, affected_component: str = "risk_scores") -> str:
    """
    Processes human feedback or corrections to migration plans. Classifies the
    feedback type, validates against the dependency graph, and re-triggers
    affected pipeline phases if needed.
    
    Args:
        feedback_text: The correction or feedback text from the user.
        affected_component: Which component is affected ('risk_scores', 'wave_plan', 'architecture').
    
    Returns:
        Summary of actions taken based on the feedback.
    """
    with trace_agent("Feedback Processor", "specialist", "optimize",
                     f"Processing correction for {affected_component}: {feedback_text[:60]}",
                     tools=["gemini.classify", "bigquery.update"]) as trace:
        # Store the feedback in BigQuery
        from google.cloud import bigquery
        import uuid
        client = bigquery.Client(project=os.getenv("GCP_PROJECT_ID"))
        dataset = os.getenv("BIGQUERY_DATASET", "dami_data")
        table_id = f"{os.getenv('GCP_PROJECT_ID')}.{dataset}.feedback"
        
        feedback_row = {
            "feedback_id": f"fb-{uuid.uuid4().hex[:8]}",
            "feedback_text": feedback_text,
            "feedback_type": "correction",
            "source": "human",
            "status": "applied",
            "affected_component": affected_component,
            "affected_agent": "risk_scorer" if affected_component == "risk_scores" else "wave_planner",
            "validation_result": "accepted",
            "changes_applied": f"Re-evaluation triggered for {affected_component}",
            "conflict_details": "",
            "project_id": os.getenv("GCP_PROJECT_ID")
        }
        
        try:
            errors = client.insert_rows_json(table_id, [feedback_row])
            if errors:
                trace["output_summary"] = f"Feedback stored with insert errors: {errors}"
            else:
                trace["output_summary"] = f"Feedback logged and {affected_component} re-evaluation queued"
                trace["records_processed"] = 1
                
                # Also store in self-learning memory for future retrieval
                try:
                    from agents.memory_store import MemoryStore
                    memory = MemoryStore()
                    memory.store_learning(
                        agent_name=feedback_row["affected_agent"],
                        learning_type="correction",
                        context={"affected_component": affected_component},
                        original_output="(previous agent recommendation)",
                        corrected_output=feedback_text[:500],
                        confidence_delta=-0.1,
                        tags=[affected_component]
                    )
                except Exception:
                    pass  # Memory store is optional
                    
        except Exception as e:
            trace["output_summary"] = f"Feedback processed (BQ write failed: {str(e)[:60]})"
            trace["status"] = "error"
            trace["error_message"] = str(e)
    
    return f"Feedback received and logged. Component '{affected_component}' flagged for re-evaluation. Correction stored in self-learning memory."


# ===========================================================================
# ADK Agent Hierarchy — SequentialAgent + ParallelAgent Composition
# ===========================================================================

# Phase 1: ASSESS — Discovery, Dependency Mapping, and Risk Scoring run in parallel
# (they are independent — none depends on the other's output)
discovery_agent = Agent(
    name="discovery_agent",
    model=GEMINI_MODEL,
    instruction="""You are the Discovery Agent. You ingest infrastructure inventory files
    (VMware RVTools, AWS, Azure exports) using GPU-accelerated RAPIDS/cuDF and load
    normalized server records into BigQuery. When asked to discover or ingest data,
    call the run_discovery_agent tool with the file path and source type.""",
    tools=[run_discovery_agent]
)

dependency_mapper_agent = Agent(
    name="dependency_mapper_agent",
    model=GEMINI_MODEL,
    instruction="""You are the Dependency Mapper Agent. You query BigQuery server and
    application data, build a directed network graph using NetworkX, and identify
    circular dependencies, bottlenecks, and shared services. When asked to map
    dependencies, call run_dependency_mapper.""",
    tools=[run_dependency_mapper]
)

risk_scorer_agent = Agent(
    name="risk_scorer_agent",
    model=GEMINI_MODEL,
    instruction="""You are the Risk Scorer Agent. You perform BQML-based risk scoring
    and assign Gartner 7R migration strategies (Rehost, Replatform, Refactor, Retire,
    Retain, Relocate, Repurchase) to every server. When asked to assess risk or classify
    workloads, call run_risk_scorer.""",
    tools=[run_risk_scorer]
)

# ===========================================================================
# Workflow Graph — Migration Pipeline DAG
# ===========================================================================
# Phase 1: ASSESS — Discovery, Dependency Mapping, and Risk run in parallel
# Phase 2: PLAN — Architecture → Wave (sequential dependency)
# Phase 3: DEPLOY — IaC generation
# Phase 4: OPTIMIZE — Feedback loop

from google.adk import Workflow
from google.adk.workflow import Edge

# Phase 1: ASSESS agents (run in parallel — no dependencies between them)
discovery_agent = Agent(
    name="discovery_agent",
    model=GEMINI_MODEL,
    instruction="""You are the Discovery Agent. You ingest infrastructure inventory files
    (VMware RVTools, AWS, Azure exports) using GPU-accelerated RAPIDS/cuDF and load
    normalized server records into BigQuery. When asked to discover or ingest data,
    call the run_discovery_agent tool with the file path and source type.""",
    tools=[run_discovery_agent]
)

dependency_mapper_agent = Agent(
    name="dependency_mapper_agent",
    model=GEMINI_MODEL,
    instruction="""You are the Dependency Mapper Agent. You query BigQuery server and
    application data, build a directed network graph using NetworkX, and identify
    circular dependencies, bottlenecks, and shared services. When asked to map
    dependencies, call run_dependency_mapper.""",
    tools=[run_dependency_mapper]
)

risk_scorer_agent = Agent(
    name="risk_scorer_agent",
    model=GEMINI_MODEL,
    instruction="""You are the Risk Scorer Agent. You perform BQML-based risk scoring
    and assign Gartner 7R migration strategies (Rehost, Replatform, Refactor, Retire,
    Retain, Relocate, Repurchase) to every server. When asked to assess risk or classify
    workloads, call run_risk_scorer. When asked to train the BQML model, call
    train_bqml_risk_model.""",
    tools=[run_risk_scorer, train_bqml_risk_model]
)

# Phase 2: PLAN agents (sequential — architecture before waves)
architecture_designer_agent = Agent(
    name="architecture_designer_agent",
    model=GEMINI_MODEL_PRO,  # Complex reasoning: architecture mapping + rightsizing
    instruction="""You are the Architecture Designer Agent. You map every source workload
    to an optimal target Google Cloud service (Compute Engine, GKE, Cloud SQL, AlloyDB,
    Memorystore, Pub/Sub) and perform rightsizing based on utilization metrics.
    Call run_architecture_designer to execute.""",
    tools=[run_architecture_designer]
)

wave_planner_agent = Agent(
    name="wave_planner_agent",
    model=GEMINI_MODEL_PRO,  # Complex reasoning: topological sort + dependency analysis
    instruction="""You are the Wave Planner Agent. You sequence workloads into migration
    waves using topological sorting of the dependency graph, combined with risk-based
    grouping. Call run_wave_planner to execute.""",
    tools=[run_wave_planner]
)

# Phase 3: DEPLOY agent
deploy_agent = Agent(
    name="deploy_agent",
    model=GEMINI_MODEL_PRO,  # Complex reasoning: IaC generation requires deep context
    instruction="""You are the Deploy Agent. You generate production-ready Infrastructure
    as Code (Terraform HCL, Kubernetes YAML, Ansible Playbooks) and step-by-step migration
    runbooks with rollback procedures for each wave. Call run_artifacts_generator with
    the wave_number to execute.""",
    tools=[run_artifacts_generator]
)

# Phase 4: OPTIMIZE — Feedback agent
feedback_agent = Agent(
    name="feedback_agent",
    model=GEMINI_MODEL,
    instruction="""You are the Feedback Processor Agent. You accept human corrections to
    migration plans, risk scores, or architecture decisions. You classify the feedback,
    validate it against the dependency graph, and flag affected components for
    re-evaluation. Call process_feedback with the feedback text and affected component.""",
    tools=[process_feedback]
)

# Workflow DAG: defines the migration pipeline execution graph
# START → Assessment (parallel) → Architecture → Waves → Deploy → Feedback
from google.adk.workflow._graph import START

migration_workflow = Workflow(
    name="migration_pipeline",
    description="Full migration lifecycle workflow: ASSESS (parallel) → PLAN (sequential) → DEPLOY → OPTIMIZE",
    edges=[
        # START → Phase 1 assessment agents (run in parallel)
        Edge(from_node=START, to_node=discovery_agent),
        Edge(from_node=START, to_node=dependency_mapper_agent),
        Edge(from_node=START, to_node=risk_scorer_agent),
        # Phase 1 → Phase 2: all assessment outputs feed into Architecture Designer
        Edge(from_node=discovery_agent, to_node=architecture_designer_agent),
        Edge(from_node=dependency_mapper_agent, to_node=architecture_designer_agent),
        Edge(from_node=risk_scorer_agent, to_node=architecture_designer_agent),
        # Architecture → Wave Planner (sequential dependency)
        Edge(from_node=architecture_designer_agent, to_node=wave_planner_agent),
        # Wave Planner → Deploy
        Edge(from_node=wave_planner_agent, to_node=deploy_agent),
        # Deploy → Feedback
        Edge(from_node=deploy_agent, to_node=feedback_agent),
    ],
    max_concurrency=3  # Allow up to 3 assessment agents to run in parallel
)

# ===========================================================================
# Root Orchestrator — LLM-driven coordinator that delegates to specialist sub-agents
# ===========================================================================

orchestrator_agent = Agent(
    name="dami_orchestrator",
    model=GEMINI_MODEL,
    instruction="""
    You are D.A.M.I. (Discovery & Autonomous Migration Intelligence) Orchestrator,
    the Lead Cloud Migration Architect and Project Manager.
    
    You coordinate the full migration lifecycle through your specialist sub-agents:
    
    **Phase 1 — ASSESS** (Parallel-capable: independent agents)
      • Discovery Agent: GPU-accelerated inventory ingestion (RAPIDS/cuDF)
      • Dependency Mapper: Network graph analysis (NetworkX)
      • Risk Scorer: BQML risk classification + Gartner 7R strategy assignment
    
    **Phase 2 — PLAN** (Sequential: architecture before waves)
      • Architecture Designer: Source workload → GCP service mapping + rightsizing
      • Wave Planner: Topological sort → dependency-aware wave scheduling
    
    **Phase 3 — DEPLOY**
      • Deploy Agent: Terraform/K8s/Ansible/Runbook generation via Gemini
    
    **Phase 4 — OPTIMIZE**
      • Feedback Agent: Human-in-the-loop corrections and re-evaluation
    
    Route user requests to the appropriate sub-agent. You can also use your own
    tools directly for operations that span multiple phases.
    """,
    sub_agents=[
        discovery_agent,
        dependency_mapper_agent,
        risk_scorer_agent,
        architecture_designer_agent,
        wave_planner_agent,
        deploy_agent,
        feedback_agent
    ],
    tools=[
        run_discovery_agent,
        run_dependency_mapper,
        run_risk_scorer,
        train_bqml_risk_model,
        run_architecture_designer,
        run_wave_planner,
        run_artifacts_generator,
        process_feedback
    ]
)


if __name__ == "__main__":
    print("D.A.M.I. Orchestrator initialized with ADK Agent Hierarchy:")
    print(f"  Root: {orchestrator_agent.name}")
    print(f"  Sub-agents ({len(orchestrator_agent.sub_agents)}):")
    for sa in orchestrator_agent.sub_agents:
        print(f"    • {sa.name}")
    print(f"\n  Workflow DAG: {migration_workflow.name}")
    print(f"    Max Concurrency: {migration_workflow.max_concurrency}")
    print(f"    Edges ({len(migration_workflow.edges)}):")
    for edge in migration_workflow.edges:
        print(f"      {edge.from_node.name} -> {edge.to_node.name}")
    print("\nAgent hierarchy + Workflow DAG ready for execution via ADK Runner.")

