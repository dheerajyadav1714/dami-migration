# D.A.M.I. — Pitch Deck Slide Outline
### 🏆 Google Cloud & NVIDIA Gen AI / Data Intelligence Hackathon

Use this slide-by-slide structure to build your submission presentation.

---

### Slide 1: Title Slide (First Impressions)
*   **Slide Title:** D.A.M.I. — Discovery & Autonomous Migration Intelligence
*   **Subtitle:** GPU-Accelerated Multi-Agent Cloud Migration Decisioning with NVIDIA RAPIDS & Google Cloud Gen AI
*   **Visuals:** Screenshot of D.A.M.I.'s Dashboard showing the 4-phase lifecycle tracker (ASSESS → PLAN → DEPLOY → OPTIMIZE) and KPI grid.
*   **Key Message:** Replacing 6-18 months of manual migration consulting with an autonomous, GPU-accelerated, multi-agent intelligence system.

---

### Slide 2: The Problem & The Decision Bottleneck
*   **Slide Title:** The Multi-Month Migration Bottleneck
*   **Bullet Points:**
    *   **Scale Complexity:** Analyzing 10,000+ VM inventories manually leads to spreadsheet fatigue and human error.
    *   **Dirty Data:** Ghost/Zombie VMs inflate target budgets; overlapping IP allocations threaten routing conflicts.
    *   **Circular Dependencies:** Blind migrations break databases due to unidentified network loop bottlenecks.
    *   **Compliance Blindspot:** No automated mapping from workloads to regulatory frameworks (HIPAA, PCI-DSS, SOC2).
    *   **Zero Transparency:** Manual processes leave no audit trail of why migration decisions were made.
*   **Key Message:** IT Directors need automated, auditable, AI-driven intelligence — not static spreadsheets.

---

### Slide 3: Multi-Agent Architecture & Workflow DAG
*   **Slide Title:** D.A.M.I. Core Architecture — 7 Specialist Agents
*   **Bullet Points:**
    *   **ADK Workflow DAG:** 9 edges defining a parallel→sequential pipeline with `max_concurrency=3`.
    *   **Phase 1 — ASSESS (Parallel):** Discovery Agent (RAPIDS cuDF), Dependency Mapper (NetworkX), Risk Scorer (BQML) run simultaneously.
    *   **Phase 2 — PLAN (Sequential):** Architecture Designer → Wave Planner (topological sort).
    *   **Phase 3 — DEPLOY:** Terraform, Kubernetes, Ansible, and Runbook generation via Gemini.
    *   **Phase 4 — OPTIMIZE:** Human feedback corrections logged and re-evaluated.
*   **Visuals:** Workflow DAG diagram showing `__START__` → 3 parallel agents → Architecture → Waves → Deploy → Feedback.

---

### Slide 4: NVIDIA GPU Acceleration Proof
*   **Slide Title:** Breaking Ingestion Bottlenecks with NVIDIA RAPIDS
*   **Bullet Points:**
    *   **Multi-Scale Benchmark:** Tested at 6 progressively larger dataset sizes (1K, 5K, 10K, 25K, 50K, 100K rows).
    *   **Live CPU Measurement:** Actual pandas processing times measured on every run.
    *   **Scaling Curve:** GPU speedup grows from **3.2x** (1K rows — kernel launch overhead) to **28.7x** (100K rows — full VRAM saturation on RTX 4050).
    *   **Architecture:** cuDF → Apache Arrow columnar memory → CUDA kernels → GPU VRAM parallel ops.
*   **Visuals:** Two charts — (1) CPU vs GPU processing time scaling curve, (2) Speedup factor growth curve with 28.7x annotation.

---

### Slide 5: Agent Transparency & Compliance
*   **Slide Title:** Full Agentic Observability & Regulatory Readiness
*   **Bullet Points:**
    *   **Agent Execution Trace:** Gantt-style timeline showing every agent invocation — tool calls, execution times, records processed, and error status — all logged to BigQuery.
    *   **Compliance Posture Dashboard:** Maps workloads to HIPAA (🏥), PCI-DSS (💳), SOC2 (🔒), and ISO27001 (🌐) with auto-mapped GCP security controls.
    *   **Security IaC:** Auto-generated Terraform for VPC Service Controls and Cloud KMS CMEK encryption.
    *   **Executive Report Export:** One-click downloadable migration assessment report from Dashboard.
*   **Visuals:** Screenshot of Agent Trace page (Gantt timeline) + Compliance framework cards.

---

### Slide 6: Interactive Decision Cockpit
*   **Slide Title:** From Analysis to Action — What Architects Actually Use
*   **Bullet Points:**
    *   **What-If FinOps Planner:** Interactive sidebar sliders dynamically adjusting CPU oversubscription ratios and safety headroom — cost estimates update in real-time.
    *   **Dependency Loop Highlighting:** NetworkX/Pyvis graphs with circular loops highlighted in glowing neon red dashes.
    *   **Multi-Cloud Architecture Maps:** Graphviz SVG diagrams showing target landing zones for GCP, AWS, and Azure.
    *   **IaC Factory:** Browse, preview, and download Terraform HCL, Kubernetes YAML, Ansible Playbooks, and step-by-step Runbooks per wave.
    *   **BQ-Grounded Chatbot:** Conversational assistant for natural language data queries.
*   **Visuals:** Screenshots of FinOps sliders + dependency map with neon loops + IaC code preview.

---

### Slide 7: Technology Stack & What's Next
*   **Slide Title:** Built on Google Cloud + NVIDIA — Ready for Enterprise
*   **Tech Stack Table:**

| Layer | Technology |
|---|---|
| AI Orchestration | Google ADK — Workflow DAG (7 agents, 9 edges) |
| LLM | Gemini 2.5 Flash (Vertex AI) |
| Data Warehouse | Google BigQuery (16 tables) |
| ML Engine | BigQuery ML (Logistic Regression) |
| GPU Acceleration | NVIDIA RAPIDS cuDF (RTX 4050) |
| Frontend | Streamlit (13 pages) |
| Backend | FastAPI |
| Observability | Agent Trace → BigQuery → Plotly Gantt |

*   **What's Next:** AlloyDB Omni for self-learning feedback memory, Cloud Run deployment, Managed Spark for large-scale ETL.
