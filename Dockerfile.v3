# ============================================================
# D.A.M.I. v3 — Multi-stage Dockerfile
# Serves: React frontend (static) + FastAPI backend + Streamlit
# ============================================================

# Stage 1: Build React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --production=false
COPY frontend/ .
RUN npm run build

# Stage 2: Production image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=True
ENV PYTHONPATH=/app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Copy built React frontend
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Copy application code
COPY .streamlit/ .streamlit/
COPY agents/ agents/
COPY api/ api/
COPY data/ data/
COPY lib/ lib/
COPY schemas/ schemas/
COPY scripts/ scripts/
COPY ui/ ui/
COPY .env.example .env.example

# Create runtime directories
RUN mkdir -p generated_assets/reports generated_assets/wave_0 \
    generated_assets/wave_1 generated_assets/wave_2 generated_assets/wave_3

# Expose Cloud Run port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Start script: FastAPI serves both API and static React files
COPY deploy/start.sh /app/start.sh
RUN chmod +x /app/start.sh
CMD ["/app/start.sh"]
