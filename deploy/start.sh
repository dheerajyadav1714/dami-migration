#!/bin/bash
# D.A.M.I. v3 — Production start script
# Runs FastAPI (serves both API + React static files) on port 8080

exec python -m uvicorn api.main:app \
  --host 0.0.0.0 \
  --port 8080 \
  --workers 2 \
  --timeout-keep-alive 30
