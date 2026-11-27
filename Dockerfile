# SwingSlot - production container
# Used by: local "docker run", the CI smoke test and Google Cloud Run (see README > Docker).
FROM python:3.12-slim

# Don't write .pyc files, show logs immediately (Cloud Logging reads stdout/stderr)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install dependencies first so Docker can cache this layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app ./app
COPY run.py .

# Run as a non-root user; the SQLite database lives in /app/instance
RUN useradd --create-home appuser && mkdir -p /app/instance && chown -R appuser /app
USER appuser

EXPOSE 8000

# Docker marks the container unhealthy if /health stops answering (Cloud Run uses its own probe)
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\", \"8000\")}/health', timeout=2)"

# Cloud Run (and most hosts) pass the port in $PORT.
# One worker process (with threads) so only one process creates the SQLite database.
# Access and error logs go to stdout/stderr so they show up in Cloud Logging (GOLF-83).
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 60 \
    --access-logfile - --error-logfile - "app:create_app()"
