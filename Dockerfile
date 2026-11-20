# SwingSlot - production container
FROM python:3.12-slim

# Don't write .pyc files and show logs immediately
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

# Render (and most hosts) pass the port in $PORT.
# One worker process (with threads) so only one process creates the SQLite database.
CMD gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 "app:create_app()"
