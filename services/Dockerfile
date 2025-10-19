FROM python:3.11-slim

# System deps (Java for FACTEMICLI, curl for diagnostics)
RUN apt-get update \
	&& apt-get install -y --no-install-recommends openjdk-17-jre-headless curl \
	&& rm -rf /var/lib/apt/lists/*

# Work inside /app (repo root will be copied here)
WORKDIR /app

# Install Python deps first (better layer cache)
COPY services/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the entire repo so that core/ and saft-pt-doctor/ are available
COPY . /app

# Ensure Python can import top-level packages (core, saft_pt_doctor)
ENV PYTHONPATH=/app:${PYTHONPATH}

# Entrypoint
RUN chmod +x /app/services/entrypoint.sh
EXPOSE 8080
ENTRYPOINT ["/app/services/entrypoint.sh"]
