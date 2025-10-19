#!/bin/sh
# Entrypoint script for SAFT Doctor
set -e

# Use PORT environment variable from Render, fallback to 8080
PORT=${PORT:-8080}

echo "Starting SAFT Doctor on port $PORT..."
echo "Python version: $(python -V)"
echo "Uvicorn version: $(python -c 'import uvicorn,sys;print(uvicorn.__version__)' 2>/dev/null || echo n/a)"
echo "PYTHONPATH: ${PYTHONPATH}"
echo "Working dir: $(pwd)"
ls -la

# Start uvicorn (module under services.main since we set PYTHONPATH=/app)
exec uvicorn services.main:app --host 0.0.0.0 --port "$PORT"
