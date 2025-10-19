#!/bin/sh
# Entrypoint script for SAFT Doctor

# Use PORT environment variable from Render, fallback to 8080
PORT=${PORT:-8080}

echo "Starting SAFT Doctor on port $PORT..."

# Start uvicorn
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
