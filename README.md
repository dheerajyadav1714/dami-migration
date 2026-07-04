# D.A.M.I. — Discovery & Autonomous Migration Intelligence

> **AI-powered enterprise cloud migration accelerator** that replaces months of manual consulting with an autonomous multi-agent pipeline, GPU-accelerated data processing, and intelligent decision support.

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Cloud_Run-4285F4?style=for-the-badge)](https://dami-app-573585543580.us-central1.run.app)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.58-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Google Cloud](https://img.shields.io/badge/Google_Cloud-BigQuery_|_Vertex_AI_|_Cloud_Run-4285F4?style=flat-square&logo=googlecloud&logoColor=white)](https://cloud.google.com)
[![NVIDIA](https://img.shields.io/badge/NVIDIA-RAPIDS_cuDF-76B900?style=flat-square&logo=nvidia&logoColor=white)](https://rapids.ai)

---

## 🏆 Hackathon Submission

**Google Cloud & NVIDIA Gen AI Hackathon — Cohort 2 (APAC Edition)**  
**Problem Statement:** Accelerated Data Intelligence Challenge

### The 5-Point Checklist
| # | Requirement | D.A.M.I. |
|---|---|---|
| 1 | **Real User** | Cloud Migration Architect / IT Infrastructure Director |
| 2 | **Decision Bottleneck** | Manual VM analysis, dependency loops, risk assessment takes 6-18 months |
| 3 | **Data Pipeline** | CSV → RAPIDS cuDF (GPU) → BigQuery (17 tables) → BQML → Gemini Agents |
| 4 | **Useful Output** | Wave plans, risk scores, architecture mappings, IaC, compliance reports, PDF |
| 5 | **Acceleration Proof** | NVIDIA RAPIDS cuDF **28.7x GPU speedup** + AI pipeline **500x faster** than manual |

### Technologies Used (6+)
| Technology | Category | Usage |
|---|---|---|
| **BigQuery** | Data Warehouse | 17-table migration schema + BQML logistic regression risk model |
| **BigQuery ML** | ML/AI | `CREATE MODEL` → `ML.PREDICT` → `ML.EVALUATE` for risk classification |
| **Vertex AI / Gemini** | LLM/Agent | 8 agents with Flash ↔ Pro intelligent routing |
| **Cloud Storage** | Storage | Inventory uploads, IaC artifacts, benchmark results |
| **Cloud Run** | Compute | Serverless deployment (auto-scaling, pay-per-request) |
| **Google ADK** | Agent Framework | Multi-agent workflow DAG orchestration |
| **NVIDIA RAPIDS cuDF** | GPU Acceleration | 28.7x faster data processing at 100K rows |
| **NVIDIA GPU** | Hardware | Benchmarked on RTX 4050 (local dev); production-ready for T4/A100 on GKE |
| **Gemini Vision** | Multimodal AI | Extracts architecture components from uploaded diagrams (PNG/draw.io) |

---

## 🎯 The Problem

Enterprise VMware-to-cloud migrations are slow, expensive, and manual:
- Analyzing thousands of VMs takes **6-18 months** of consulting at **$300/hr**
- Circular dependency loops block migration wave scheduling
- Licensing risks (Oracle DBMS on shared compute) cause **$500K+ overruns**
- No visibility into what AI agents decided and why — blocking compliance sign-off

## ⚡ The Solution

D.A.M.I. is an **Accelerated Data Intelligence Tool** that helps Cloud Migration Architects make **faster, better migration decisions** using GPU-accelerated data pipelines and autonomous AI agents.

> *"D.A.M.I. helps a Cloud Migration Architect decide how to sequence and execute datacenter-to-cloud migration using VM inventory data by producing risk-scored wave plans, target architecture recommendations, and IaC templates — all accelerated by NVIDIA RAPIDS cuDF."*

### Acceleration Impact
| Metric | Traditional | D.A.M.I. | Improvement |
|---|---|---|---|
| **Time-to-Decision** | 6-18 months | ~8 minutes | **500x faster** |
| **Data Processing** | Pandas (CPU) | RAPIDS cuDF (GPU) | **28.7x at 100K rows** |
| **Risk Assessment** | Manual interviews | BQML ML.PREDICT | **Real-time** |
| **Architecture Design** | Weeks of research | Gemini AI (10 batches) | **~7 minutes** |
| **Wave Planning** | Spreadsheets | AI topological sorting | **~30 seconds** |
| **IaC Generation** | Handwritten | Gemini Pro | **Instant** |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                               │
│                   Streamlit UI (14 Pages)                           │
│              Cloud Run (Auto-scaling, Serverless)                   │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                    AI AGENT PIPELINE (Google ADK)                    │
│                                                                     │
│  ASSESS (Parallel)          PLAN                    DEPLOY          │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│  │ ⚡ Discovery     │  │ 🧠 Architecture  │  │ 🧠 IaC Generator   │ │
│  │ ⚡ Dep. Mapper   │→│    Designer      │→│ ⚡ Report Generator │ │
│  │ ⚡ Risk Scorer   │  │ 🧠 Wave Planner  │  │ ⚡ Feedback Agent  │ │
│  └─────────────────┘  └──────────────────┘  └────────────────────┘ │
│  gemini-2.5-flash       gemini-2.5-pro        gemini-flash/pro     │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│              GOOGLE CLOUD DATA & APPLICATION LAYER                  │
│                                                                     │
│  BigQuery (17 Tables)  │  BigQuery ML     │  Vertex AI / Gemini    │
│  Cloud Storage (GCS)   │  (Risk Models)   │  (Flash ↔ Pro Routing) │
└─────────────────────────┬───────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────────┐
│                  NVIDIA ACCELERATION LAYER                          │
│                                                                     │
│  RAPIDS cuDF            │  GPU DataFrames  │  28.7x Peak Speedup   │
│  (GPU-accelerated ETL)  │  (cudf.pandas)   │  at 100K rows         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Multi-Agent Architecture (8 Agents)

| Phase | Agent | Model | Role |
|---|---|---|---|
| **ASSESS** | Discovery Agent | ⚡ gemini-2.5-flash | Ingests CSV/Excel/JSON via RAPIDS cuDF → BigQuery |
| **ASSESS** | Dependency Mapper | ⚡ gemini-2.5-flash | NetworkX directed graph → circular loop detection |
| **ASSESS** | Risk Scorer | ⚡ gemini-2.5-flash + BQML | `ML.PREDICT` → Gartner 7R strategy assignment |
| **PLAN** | Architecture Designer | 🧠 gemini-2.5-pro | Deep BQ context (deps, diagrams, compliance) → GCP service mapping |
| **PLAN** | Wave Planner | 🧠 gemini-2.5-pro | AI topological sorting → wave sequencing with rationale |
| **DEPLOY** | IaC Generator | 🧠 gemini-2.5-pro | Terraform, K8s YAML, Ansible, Dockerfiles → GCS |
| **OPTIMIZE** | Report Generator | ⚡ gemini-2.5-flash | Executive PDF/Markdown report synthesis |
| **OPTIMIZE** | Feedback Agent | ⚡ gemini-2.5-flash | Human corrections → self-learning memory loop |

### Intelligent LLM Routing
D.A.M.I. automatically routes queries to the optimal Gemini model:
- **⚡ Flash** — Data lookups, SQL generation, quick responses (sub-second)
- **🧠 Pro** — Architecture design, IaC generation, complex reasoning

---

## 🖥️ NVIDIA RAPIDS GPU Acceleration

| Dataset Size | Pandas (CPU) | cuDF (GPU) | Speedup |
|---|---|---|---|
| 1,000 rows | 29.7ms | 9.28ms | **3.2x** |
| 5,000 rows | 20.4ms | 2.62ms | **7.8x** |
| 10,000 rows | 24.2ms | 1.95ms | **12.4x** |
| 25,000 rows | 44.0ms | 2.36ms | **18.6x** |
| 50,000 rows | 78.6ms | 3.26ms | **24.1x** |
| 100,000 rows | 114.8ms | 4.00ms | **28.7x** |

**Why acceleration matters:** Without GPU, processing 100K VMs takes ~8.6 seconds per analysis run. Migration architects can only run 2-3 "what-if" scenarios per day. With RAPIDS cuDF (28.7x faster), the same analysis runs in ~0.3 seconds — architects test 50+ scenarios per hour, and dashboards refresh in real-time during stakeholder meetings.

**Hardware:** NVIDIA GeForce RTX 4050 Laptop GPU (6GB GDDR6)

---

## 📊 Key Features (14 Pages)

| Feature | Description |
|---|---|
| 🏠 **Mission Control Dashboard** | KPI grid, readiness gauge, acceleration impact, progress timeline |
| 📤 **Upload & GPU Benchmark** | Multi-format upload to GCS + RAPIDS cuDF CPU vs GPU benchmark |
| ⚡ **NVIDIA RAPIDS Benchmark** | Dedicated benchmark page with live GPU profiling |
| 📋 **Server Inventory** | Live BigQuery data explorer with filtering |
| 🔗 **Dependency Graph** | Interactive PyVis + Graphviz + circular loop detection |
| ⚠️ **Risk & 7R Assessment** | BQML risk heatmap, strategy distribution, model training |
| 🏗️ **Target Architecture** | AI-recommended GCP service mapping + multi-cloud topology with CIDR ranges |
| 🌊 **Wave Gantt Chart** | AI-powered wave timeline with Gemini-generated rationale |
| 💰 **TCO & FinOps** | What-If cost simulator with oversubscription sliders |
| 💻 **IaC & Runbooks** | Terraform, K8s, Ansible, Dockerfile generation + rollback plans |
| 🛡️ **Compliance** | HIPAA/PCI-DSS/SOC2/ISO27001 gap analysis + remediation |
| 🔬 **Agent Observability** | Full execution trace timeline with Gantt visualization |
| 💬 **Conversational AI** | NL → SQL → BigQuery with persistent chat + model routing badge |
| 🧠 **Self-Learning** | BigQuery + AlloyDB pgvector agent memory feedback loops |

---

## 🖼️ Multimodal AI — Architecture Diagram Analysis

D.A.M.I. uses **Gemini Vision** to extract infrastructure components from uploaded architecture diagrams:

1. **Upload** existing on-premises architecture diagrams (PNG, JPEG, draw.io exports)
2. **Gemini Vision** analyzes the image and extracts: VM components, network topology, database tiers, firewall rules, load balancers
3. **Results stored** in BigQuery `diagram_analysis` table
4. **Fed into AI agents** — Architecture Designer uses diagram context for richer GCP service recommendations

> Zero manual data entry from diagrams — upload a whiteboard photo of your datacenter, and D.A.M.I. understands it.

---

## 🎯 Quick Demo (for Judges)

> Follow these 5 steps to see D.A.M.I. in action:

| Step | Page | What You'll See |
|---|---|---|
| 1 | **Dashboard** | KPI grid, readiness gauge, acceleration impact (500x), NVIDIA benchmark |
| 2 | **Upload Center** | Upload a CSV → GPU benchmark runs → data flows to BigQuery |
| 3 | **Risk Assessment** | BQML risk heatmap + Gartner 7R strategy distribution |
| 4 | **Target Architecture** | AI-recommended GCP services + multi-cloud topology with CIDR ranges |
| 5 | **Chat** | Ask "How many high risk servers?" → NL→SQL→BigQuery in real-time |

**Bonus pages:** Wave Gantt Chart (AI sequencing), IaC & Runbooks (Terraform generation), Compliance (HIPAA/PCI-DSS gap analysis)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud project with BigQuery & Vertex AI enabled
- NVIDIA GPU with CUDA support (for RAPIDS cuDF acceleration)
- `gcloud` CLI authenticated (`gcloud auth application-default login`)

### Local Development
```bash
# Clone
git clone https://github.com/dheerajyadav1714/dami-migration.git
cd dami-migration

# Setup
python -m venv .venv
source .venv/bin/activate    # Linux/Mac
# .venv\Scripts\activate     # Windows

pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your GCP project details

# Bootstrap BigQuery
python scripts/create_bq_tables.py
python scripts/seed_database.py

# Run
streamlit run ui/app.py
```

### Deploy to Cloud Run
```bash
gcloud run deploy dami-app \
  --source . \
  --project=YOUR_PROJECT \
  --region=us-central1 \
  --allow-unauthenticated \
  --memory=2Gi --cpu=2 \
  --set-env-vars="GCP_PROJECT_ID=YOUR_PROJECT,BIGQUERY_DATASET=dami_data,GCS_BUCKET=YOUR_BUCKET,VERTEX_AI_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash"
```

---

## 📁 Project Structure
```
dami-migration/
├── agents/                    # 8 ADK specialist agents
│   ├── orchestrator.py        # DAG workflow with Flash ↔ Pro routing
│   ├── discovery.py           # RAPIDS cuDF ingestion
│   ├── intake.py              # Gemini Vision diagram analysis
│   ├── dependency_mapper.py   # NetworkX graph + loop detection
│   ├── risk_scorer.py         # BQML ML.PREDICT pipeline
│   ├── architecture_designer.py # Deep BQ context → GCP service mapping
│   ├── wave_planner.py        # AI topological sorting + rationale
│   ├── artifacts_generator.py # Terraform/K8s/Ansible → GCS
│   ├── report_generator.py    # Executive PDF/MD reports
│   ├── memory_store.py        # AlloyDB pgvector feedback loops
│   └── trace_logger.py        # Agent execution tracing
├── api/                       # FastAPI backend
├── data/seed/                 # Sample RVTools CSV data
├── schemas/                   # BigQuery table schemas (17 tables)
├── scripts/                   # Setup and seeding scripts
├── ui/
│   ├── app.py                 # Main Streamlit app + CSS design system
│   └── pages/                 # 14 feature pages
├── Dockerfile                 # Cloud Run container
├── requirements.txt           # Local dependencies
├── requirements-cloud.txt     # Cloud Run dependencies
└── README.md
```

---

## 👤 Team

| Name | Role |
|---|---|
| **Dheeraj Yadav** | Full-stack developer — agents, UI, deployment |

---

## 📄 License
Built for the Google Cloud & NVIDIA Gen AI Hackathon 2026 — APAC Edition (Cohort 2).
