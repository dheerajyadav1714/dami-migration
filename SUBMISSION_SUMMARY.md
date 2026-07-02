# D.A.M.I. — Hackathon Submission Summary
### 🏆 Google Cloud & NVIDIA Gen AI / Data Intelligence Hackathon

---

#### 1. 🌟 Real-World User & Problem Statement
- **Target User:** Enterprise Cloud Migration Lead, Solutions Architect, and IT Infrastructure Directors.
- **The Bottleneck:** Enterprise cloud migrations are notoriously slow, expensive, and manual. Analyzing VMware inventory exports, identifying network dependency loops, and rightsizing workloads typically takes **6-18 months** of consulting. Architects are blocked by:
  - **Data Hygiene:** "Dirty" data (Zombie/idle VMs wasting budgets, duplicate IP address conflicts).
  - **Sequencing Blocker:** Circular communication loops between servers that block migration wave scheduling.
  - **Licensing/Risk Traps:** High licensing risks (e.g. running Oracle DBMS on standard shared compute instances).
  - **Zero Transparency:** No visibility into what AI agents decided and why — blocking audit and compliance sign-off.

#### 2. ⚡ The Accelerated Data Pipeline
D.A.M.I. replaces slow consulting processes with an automated, AI-driven, multi-agent pipeline:
- **GPU-Accelerated Ingestion:** Uses **NVIDIA RAPIDS cuDF** to ingest and process raw VMware RVTools CSV exports in parallel. Multi-scale benchmark proves **3.2x speedup at 1K rows scaling to 28.7x speedup at 100K rows** — demonstrating how GPU parallelism increases with dataset size.
- **Visual Diagram Intake:** Uses **Gemini Vision (multimodal API)** to parse legacy architecture diagram images directly, extracting server and network properties.
- **Topological Dependency Mapping:** Constructs a directed graph of network communication flows using **NetworkX** to automatically detect and highlight circular loops.
- **Predictive Risk Modeling:** Deploys a **BigQuery ML (BQML)** Logistic Regression model to predict migration risk profiles and assign Gartner 7R strategies.
- **Workflow DAG Orchestration:** 7 specialist ADK agents orchestrated via a **Workflow DAG** with `max_concurrency=3` for parallel assessment, sequential planning, and feedback loops.

#### 3. 🏗️ Google Cloud & NVIDIA Tech Stack
- **Google Cloud Data & App Layer:**
  - **Google BigQuery:** Central warehouse for VM inventory, rightsize mappings, risk metrics, and agent execution traces (**16 custom schema tables**).
  - **BigQuery ML (BQML):** Logistic regression classifier for automated Gartner 7R strategy mapping.
  - **Google ADK (Agent Development Kit):** Multi-agent Workflow DAG with 7 specialist agents, `Workflow` + `Edge` graph composition, and `START` node parallel fan-out.
  - **Gemini 2.5 Flash (Vertex AI):** Powers IaC generation, architecture diagram intake, report synthesis, and orchestrator reasoning.
  - **Cloud Storage (GCS):** Object storage for raw inventories and architecture diagram intake.
- **NVIDIA Acceleration Layer:**
  - **NVIDIA RAPIDS cuDF:** High-speed parallel dataframe loading running on local GPU (RTX 4050, 6GB GDDR6).
  - Multi-scale benchmark with 6 dataset sizes proving acceleration curve from 3.2x to 28.7x.

#### 4. 📊 Actionable Outputs & Decision Cockpit
- **Agent Execution Trace & Observability:** Full transparency dashboard with Gantt-style timeline showing every agent invocation, tool calls, execution times, and results. Every agent is instrumented with the `trace_agent` context manager logging to BigQuery.
- **Compliance & Security Posture:** Maps all workloads to HIPAA, PCI-DSS, SOC2, and ISO27001 compliance frameworks with auto-generated security Terraform (VPC Service Controls, Cloud KMS CMEK).
- **Executive Report Generator:** One-click downloadable migration assessment report synthesizing all BigQuery data into infrastructure summary, risk distribution, wave schedule, and cost projections.
- **What-If FinOps Planner:** Interactive sliders adjusting CPU oversubscription ratios (1:1 to 4:1) and performance safety margins (10% to 50%), dynamically updating estimated costs and savings.
- **IaC & Runbook Factory:** Generates Terraform HCL, Kubernetes YAML, Ansible Playbooks, and markdown Runbooks with rollback procedures per migration wave.
- **DevOps Sync Center:** Connectors to synchronize waves to **Jira** tasks, push HCL to **GitHub**, and publish playbooks to **Confluence** (with Secret Manager secure credential storage).
- **Conversational Assistant (RAG):** Natural language assistant grounded on BigQuery tables for instant metrics extraction.

---

## 📋 Hackathon Requirements Traceability Matrix

### 1. Ground It in a Real Workflow
*   **Who (Real Person):** **Cloud Migration Lead / Solutions Architect** who faces manual inventory triage and complex migration sequencing on a recurring basis.
*   **Decision (Specific Bottleneck):** Analyzing tens of thousands of VM rows is slow, circular dependency loops block automated wave scheduling, licensing anomalies cause financial risk, and lack of agentic transparency blocks compliance sign-off.
*   **Help (Actionable Outcomes):**
    *   *Zombie VM alerts & duplicate IP warnings* to clean source inventory data.
    *   *Topological sorting* to schedule migration wave sequencing.
    *   *BQML risk scores* to classify target cloud landing strategies (Gartner 7R).
    *   *What-If Oversubscription and Safety Buffer sliders* to dynamically optimize budgets.
    *   *Agent Execution Trace* for full audit trail of every AI decision.
    *   *Compliance posture mapping* for HIPAA/PCI/SOC2/ISO27001 regulatory readiness.
    *   *Executive report export* for board-level migration assessment deliverables.

### 2. The Data Pipeline
*   **Ingest & Clean:**
    *   Ingests raw VMware RVTools CSV exports via GPU-accelerated RAPIDS cuDF.
    *   Automatically runs **Data Hygiene Checks** in BigQuery (Zombie VMs, duplicate IPs).
    *   Multimodal **Gemini Vision Intake** parses legacy architecture diagrams.
*   **Analyze & Model:**
    *   NetworkX directed graph for circular dependency detection.
    *   **BigQuery ML Logistic Regression** for risk scoring and 7R strategy.
    *   Multi-scale benchmark proving GPU acceleration scaling (1K→100K rows).
*   **Visualize & Act:**
    *   13-page Streamlit dashboard with dark "Ethereal Architect" theme.
    *   Agent Trace observability with Gantt timeline and performance charts.
    *   1-click Terraform, Ansible, K8s YAML, and Runbook generation.
    *   Executive report export with downloadable markdown.

### 3. Reference Architecture & Technology Menu
*   **Google Cloud Data Layer:** **Google BigQuery** (16 analytical tables) & **Cloud Storage** (source files).
*   **Google Cloud AI Layer:** **Gemini 2.5 Flash** (Vertex AI) + **Google ADK** (Workflow DAG with 7 agents).
*   **NVIDIA Acceleration Layer:** **NVIDIA RAPIDS cuDF** (RTX 4050, 6GB GDDR6).

### 4. Proof of Acceleration
*   **Multi-Scale Benchmark:** Live CPU measurements at 6 dataset sizes (1K, 5K, 10K, 25K, 50K, 100K rows).
*   **Scaling Curve:** GPU speedup grows from 3.2x (1K rows — GPU kernel launch overhead) to 28.7x (100K rows — full VRAM saturation).
*   **Architecture:** cuDF → Apache Arrow columnar memory → CUDA kernels → GPU VRAM parallel ops.
*   **Decision Freshness:** Real-time feedback loops via What-If simulators and agent execution traces.

### 5. Multi-Agent Agentic Architecture
*   **Workflow DAG:** 9 edges, `max_concurrency=3`, with `__START__` → parallel assessment → sequential planning → deploy → feedback.
*   **7 Specialist Agents:** Discovery, Dependency Mapper, Risk Scorer, Architecture Designer, Wave Planner, Deploy, Feedback Processor.
*   **Human-in-the-Loop:** Feedback Processor agent accepts corrections, logs to BigQuery, flags components for re-evaluation.
*   **Observability:** Every tool function instrumented with `trace_agent` context manager → BigQuery `agent_execution_logs` table → Gantt timeline UI.
