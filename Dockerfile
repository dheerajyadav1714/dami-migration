FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=True

WORKDIR /app

# Install system dependencies (graphviz for dependency graphs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    graphviz \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

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
COPY README.md README.md
COPY SUBMISSION_SUMMARY.md SUBMISSION_SUMMARY.md

# Create runtime directories
RUN mkdir -p generated_assets/reports generated_assets/wave_0 \
    generated_assets/wave_1 generated_assets/wave_2 generated_assets/wave_3

# Expose Cloud Run port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Run Streamlit on Cloud Run port
ENTRYPOINT ["streamlit", "run", "ui/app.py", \
    "--server.port=8080", \
    "--server.address=0.0.0.0", \
    "--server.headless=true", \
    "--browser.gatherUsageStats=false", \
    "--server.fileWatcherType=none"]
