# D.A.M.I. — Discovery & Autonomous Migration Intelligence

> **AI-powered enterprise cloud migration accelerator** that replaces months of manual consulting with an autonomous multi-agent pipeline, GPU-accelerated data processing, and intelligent decision support.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-BigQuery%20%7C%20Vertex%20AI%20%7C%20Cloud%20Run-4285F4)
![NVIDIA](https://img.shields.io/badge/NVIDIA-RAPIDS%20cuDF-76B900)

---

## 🎯 The Problem

Enterprise VMware-to-cloud migrations are slow, expensive, and manual:
- Analyzing thousands of VMs takes **6-18 months** of consulting
- Circular dependency loops block migration wave scheduling  
- Licensing risks (Oracle DBMS on shared compute) cause **$500K+ overruns**
- No visibility into what AI agents decided and why

## ⚡ The Solution

D.A.M.I. is an **Accelerated Data Intelligence Tool** that helps Cloud Migration Architects make **faster, better migration decisions** using GPU-accelerated data pipelines and autonomous AI agents.

> *"D.A.M.I. helps a Cloud Migration Architect decide how to sequence and execute datacenter-to-cloud migration using VM inventory data by producing risk-scored wave plans, target architecture recommendations, and IaC templates — all accelerated by NVIDIA RAPIDS cuDF."*

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                     │
│                                                             │
│  ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐  │
│  │ Cloud Run    │   │ BigQuery     │   │ Vertex AI       │  │
│  │ (Streamlit)  │──▶│ 18 Tables   │   │ Gemini 2.5 Flash│  │
│  │              │   │ BQML Models  │   │ ADK Agents (7)  │  │
│  └──────────────┘   └──────────────┘   └─────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ NVIDIA RAPIDS cuDF — GPU-accelerated ETL pipeline       ││
│  │ 3.2x (1K rows) → 28.7x (100K rows) speedup             ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Google Cloud Services Used:
- **BigQuery** — Central data warehouse (18 tables + BQML risk model)
- **Vertex AI / Gemini 2.5 Flash** — Powers all agent reasoning and IaC generation
- **Google ADK** — Multi-agent Workflow DAG with 7 specialist agents
- **Cloud Storage (GCS)** — Raw inventory file storage
- **Cloud Run** — Serverless deployment (pay-per-request)
- **Secret Manager** — Secure credential storage for integrations

### NVIDIA Acceleration:
- **RAPIDS cuDF** — GPU-accelerated DataFrame processing
- Benchmarked: **3.2x speedup at 1K rows → 28.7x at 100K rows**
- Hardware: NVIDIA RTX 4050 Laptop GPU (6GB GDDR6)

---

## 🤖 Multi-Agent Architecture (Google ADK)

7 specialist agents orchestrated via a **Workflow DAG** with `max_concurrency=3`:

| Agent | Role |
|---|---|
| **Discovery Agent** | Ingests CSV/Excel/JSON via RAPIDS cuDF, normalizes to BigQuery |
| **Risk Scorer Agent** | BQML logistic regression → Gartner 7R strategy assignment |
| **Dependency Mapper** | NetworkX directed graph → circular loop detection |
| **Wave Planner** | Topological sorting → migration wave sequencing |
| **Architecture Designer** | Workload analysis → GCP service mapping with rightsizing |
| **Artifacts Generator** | Gemini-powered Terraform, K8s YAML, Ansible, Runbooks |
| **Report Generator** | Executive PDF report synthesis from BigQuery data |

---

## 📊 Key Features (14 Pages)

| Feature | Description |
|---|---|
| 🏠 **Command Center Dashboard** | KPI grid, readiness gauge, progress timeline, agent triggers |
| 📤 **Upload & GPU Benchmark** | Multi-format upload + RAPIDS cuDF benchmark with Decision Impact |
| 📋 **Server Inventory** | Live BigQuery data explorer with filtering |
| ⚠️ **Risk & 7R Assessment** | Risk heatmap, strategy distribution, scoring details |
| 🔗 **Dependency Graph** | Interactive pyvis + static Graphviz + circular loop detection |
| 🏗️ **Target Architecture** | Multi-cloud topology diagrams + AI-reasoned service mapping |
| 🌊 **Wave Gantt Chart** | Migration wave timeline with workload assignments |
| 💰 **TCO & FinOps** | What-If simulator with oversubscription/safety margin sliders |
| 💻 **IaC & Runbooks** | Terraform, K8s, Ansible generation + rollback plans |
| 🛡️ **Compliance** | HIPAA/PCI-DSS/SOC2/ISO27001 gap analysis + remediation |
| 🔬 **Agent Observability** | Full execution trace timeline with Gantt visualization |
| 💬 **Chat Assistant** | Natural language → BigQuery SQL generation + live results |
| 🔌 **DevOps Integrations** | Jira, GitHub, Confluence sync center |
| 🧠 **Self-Learning** | Agent memory feedback loops |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud project with BigQuery enabled
- `gcloud` CLI authenticated (`gcloud auth application-default login`)

### Local Development
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/dami-migration.git
cd dami-migration

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GCP project details

# Setup BigQuery tables
python scripts/create_bq_tables.py

# Seed sample data
python scripts/seed_database.py

# Run the app
streamlit run ui/app.py
```

### Deploy to Cloud Run
```bash
# Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT/dami-app

# Deploy
gcloud run deploy dami-app \
  --image gcr.io/YOUR_PROJECT/dami-app \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --set-env-vars "GCP_PROJECT_ID=YOUR_PROJECT,BIGQUERY_DATASET=dami_data"
```

---

## 📁 Project Structure
```
dami-migration/
├── agents/          # 7 ADK specialist agents
├── api/             # FastAPI backend for orchestration
├── data/seed/       # Sample RVTools CSV data
├── schemas/         # BigQuery table schemas
├── scripts/         # Setup and seeding scripts
├── ui/
│   ├── app.py       # Main Streamlit application
│   └── pages/       # 14 feature pages
├── Dockerfile       # Cloud Run container
├── requirements.txt # Python dependencies
└── README.md
```

---

## 🏆 Hackathon Submission
**Google Cloud & NVIDIA Gen AI Hackathon — Cohort 2**  
**Problem Statement 2:** Accelerated Data Intelligence Challenge

### The 5-Point Checklist:
1. ✅ **Real User:** Cloud Migration Architect  
2. ✅ **Decision Bottleneck:** Manual VM analysis, dependency loops, risk assessment  
3. ✅ **Data Pipeline:** CSV → cuDF → BigQuery → Gemini Agents → Dashboard  
4. ✅ **Useful Output:** Wave plans, IaC, risk scores, cost projections, compliance reports  
5. ✅ **Acceleration Proof:** RAPIDS cuDF 28.7x speedup → real-time What-If scenarios  

---

## 📄 License
This project was built for the Google Cloud & NVIDIA Gen AI Hackathon 2026.
