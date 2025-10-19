#!/bin/sh
# Entrypoint script for SAFT Doctor
set -e

# Use PORT environment variable from Render, fallback to 8080
PORT=${PORT:-8080}

echo "Starting SAFT Doctor on port $PORT..."
echo "Python version: $(python -V)"
echo "Uvicorn version: $(python - <<'PY'
import sys
try:
	import uvicorn
	print(getattr(uvicorn, '__version__', 'n/a'))
except Exception as e:
	print(f"n/a ({e})")
PY
)"
echo "PYTHONPATH: ${PYTHONPATH}"
echo "Working dir: $(pwd)"
echo "Listing /app:"
ls -la /app || true
echo "Listing /app/services:"
ls -la /app/services || true

# Check FACTEMICLI.jar presence
JAR_PATH=${FACTEMICLI_JAR_PATH:-/opt/factemi/FACTEMICLI.jar}
echo "FACTEMICLI_JAR_PATH: ${JAR_PATH}"
if [ -f "$JAR_PATH" ]; then
	echo "FACTEMICLI.jar found:" && ls -lh "$JAR_PATH"
else
	echo "FACTEMICLI.jar NOT found at ${JAR_PATH}"
fi

# Start uvicorn (module under services.main since we set PYTHONPATH=/app)
exec python -m uvicorn services.main:app --host 0.0.0.0 --port "$PORT"
