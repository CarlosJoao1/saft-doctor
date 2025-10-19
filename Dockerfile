# Root-level Dockerfile shim
# Delegates to the real Dockerfile under services/

FROM python:3.11-slim AS base

# Rebuild using the actual Dockerfile with full context
# Keep context explicit to avoid missing paths when building via root

# Re-run the same steps as services/Dockerfile but from repo root context
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY services/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
# Normalize Windows line endings in entrypoint to avoid /bin/sh^M on Linux
RUN sed -i 's/\r$//' /app/services/entrypoint.sh && chmod +x /app/services/entrypoint.sh
EXPOSE 8080
ENTRYPOINT ["/app/services/entrypoint.sh"]
