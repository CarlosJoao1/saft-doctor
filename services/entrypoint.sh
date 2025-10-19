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

# Ensure MASTER_KEY is valid for dev/local. If missing or invalid, generate one in /var/saft/master.key
KEY_FILE=/var/saft/master.key
ensure_master_key() {
	if [ -z "${MASTER_KEY}" ]; then
		if [ -f "$KEY_FILE" ]; then
			export MASTER_KEY="$(tr -d '\r\n' < "$KEY_FILE")"
			echo "MASTER_KEY loaded from $KEY_FILE"
		else
			echo "Generating development MASTER_KEY at $KEY_FILE"
			mkdir -p /var/saft || true
			python - <<'PY' > "$KEY_FILE"
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
			chmod 600 "$KEY_FILE" || true
			export MASTER_KEY="$(tr -d '\r\n' < "$KEY_FILE")"
			echo "MASTER_KEY generated."
		fi
	else
		# Validate provided MASTER_KEY; if invalid, replace with generated dev key
		STATUS=$(python - <<'PY'
import os, sys
from cryptography.fernet import Fernet
k=os.environ.get('MASTER_KEY')
try:
	Fernet(k.encode() if not isinstance(k,(bytes,bytearray)) else k)
	print('OK')
except Exception:
	print('INVALID')
PY
)
		if [ "$STATUS" != "OK" ]; then
			echo "Provided MASTER_KEY is invalid. Replacing with a development key at $KEY_FILE"
			mkdir -p /var/saft || true
			python - <<'PY' > "$KEY_FILE"
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
PY
			chmod 600 "$KEY_FILE" || true
			export MASTER_KEY="$(tr -d '\r\n' < "$KEY_FILE")"
		fi
	fi
}

ensure_master_key

# Start uvicorn (module under services.main since we set PYTHONPATH=/app)
exec python -m uvicorn services.main:app --host 0.0.0.0 --port "$PORT"
