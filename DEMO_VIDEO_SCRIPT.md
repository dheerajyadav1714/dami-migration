# D.A.M.I. — 5-Minute Demo Video Script
### 🏆 Structured to Match the Gen AI Academy "4-Beat Demo Storyboard"

Use this script as a guide to record your 5-minute hackathon submission walkthrough.

---

## ⏱️ Beat 1: User + Data (0:00 - 1:15)
**Visual on screen:** Open the Streamlit App on the **"🏠 Mission Control Dashboard"**. Show the 4-phase lifecycle tracker (ASSESS → PLAN → DEPLOY → OPTIMIZE), the KPI grid, and click "📄 Generate Executive Report".

*   **What to say:**
    > "Hi, I'm presenting **D.A.M.I.**—the Discovery & Autonomous Migration Intelligence platform.
    >
    > In enterprise cloud migrations, the **Cloud Migration Architect** is handed thousands of rows of messy VMware inventory exports and outdated network diagrams, and must answer: What do we retire? What do we migrate? In what order? And will we break dependencies?
    >
    > Traditionally, this takes **6 to 18 months** of manual consulting. D.A.M.I. automates the entire lifecycle using **7 specialist AI agents** orchestrated in a Workflow DAG.
    >
    > Here on our Dashboard, you can see the 4-phase migration lifecycle tracker. I can generate a full Executive Report in one click — it queries all 16 BigQuery tables and produces a downloadable assessment with infrastructure summary, risk distribution, and cost projections."

---

## ⏱️ Beat 2: The AI Pipeline (1:15 - 2:30)
**Visual on screen:**
1. Navigate to **"📂 Upload Center"** → Show the Data Hygiene report (Zombie VMs, IP conflicts).
2. Navigate to **"🧠 Risk Assessment"** → Show BQML risk distribution + 7R strategies.
3. Navigate to **"🕸️ Dependency Map"** → Show the network graph with neon-red circular loops.

*   **What to say:**
    > "Here is our data pipeline in action.
    >
    > When an architect uploads their VM inventory, D.A.M.I. stores it in **Google BigQuery** and runs real-time **Hygiene Audits**. Our scorecard flags **Zombie VMs** — idle servers that can be retired for instant cost savings — and **IP Address Conflicts** that would break routing if migrated.
    >
    > We also parse legacy architecture diagrams using **Gemini Vision** — the multimodal API extracts server names, connections, and technologies directly from PNG/JPG uploads.
    >
    > For risk assessment, we trained a custom **BigQuery ML Logistic Regression** classifier that scores each VM's migration readiness and recommends a **Gartner 7R strategy** — Rehost, Replatform, Refactor, or Retire.
    >
    > And here on the Dependency Map, our **NetworkX** graph analysis automatically detects circular communication loops — shown in glowing neon red — that would block migration wave sequencing."

---

## ⏱️ Beat 3: NVIDIA GPU Acceleration + Agentic Transparency (2:30 - 3:45)
**Visual on screen:**
1. Go to **"📂 Upload Center"** → Click **"📊 Run Multi-Scale GPU Benchmark (1K → 100K rows)"**.
2. Show the two scaling charts + benchmark table + "How RAPIDS Works" explainer.
3. Navigate to **"🔬 Agent Trace"** → Show the Gantt timeline.
4. Navigate to **"🛡️ Compliance & Security"** → Show the framework cards.

*   **What to say:**
    > "To demonstrate how NVIDIA acceleration improves the decision experience, D.A.M.I. includes a **multi-scale benchmark**.
    >
    > We generate synthetic VMware inventory data at 6 progressively larger sizes — from 1,000 to 100,000 rows. CPU processing times are measured live using pandas. GPU times are projected using documented NVIDIA RAPIDS cuDF acceleration factors.
    >
    > As you can see, the **speedup curve** grows from **3.2x at 1K rows** — where GPU kernel launch overhead limits parallelism — all the way to **28.7x at 100K rows** where the RTX 4050's CUDA cores are fully saturated. This is the real scaling behavior documented in NVIDIA's RAPIDS benchmarks.
    >
    > For transparency, every agent execution is logged to BigQuery. Here on our **Agent Trace** page, you can see a Gantt-style timeline of every agent invocation — which tools were called, how long they took, and what records they processed.
    >
    > And our **Compliance & Security** page maps all workloads to HIPAA, PCI-DSS, SOC2, and ISO27001 — with auto-generated security Terraform for VPC Service Controls and Cloud KMS encryption."

---

## ⏱️ Beat 4: Decisions & Actions (3:45 - 5:00)
**Visual on screen:**
1. Navigate to **"💰 FinOps & TCO"** → Move the sidebar sliders (oversubscription ratio, safety margin).
2. Navigate to **"🛠️ IaC & Runbooks"** → Show Terraform HCL + Kubernetes YAML tabs.
3. Navigate to **"🌊 Wave Plan"** → Show the migration wave timeline.
4. Show the **Orchestrator Chat** on the Dashboard sidebar.

*   **What to say:**
    > "Finally, let's see how D.A.M.I. turns analysis into action:
    >
    > 1. **What-If FinOps Planner:** The architect adjusts CPU oversubscription ratios and safety performance buffers. The entire multi-cloud cost breakdown scales in real-time — instant financial decisions without waiting for consultants.
    >
    > 2. **IaC Factory:** For every migration wave, D.A.M.I. generates production-ready **Terraform HCL**, **Kubernetes YAML**, **Ansible Playbooks**, and step-by-step **Runbooks** with rollback procedures — all generated by Gemini.
    >
    > 3. **Wave Orchestration:** Our Wave Planner uses topological sorting of the dependency graph to create dependency-safe migration wave sequences.
    >
    > 4. **Orchestrator Chat:** Architects can interact directly with the D.A.M.I. orchestrator using natural language. The ADK-powered agent routes requests to the appropriate specialist — Discovery, Risk, Architecture, or Wave Planning.
    >
    > D.A.M.I. combines **Google ADK** with a 7-agent Workflow DAG, **BigQuery ML**, **Gemini 2.5 Flash**, and **NVIDIA RAPIDS** acceleration to deliver a real-world decision intelligence system that cloud architects will actually use. Thank you!"
