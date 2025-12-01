FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

# Install system deps if ever needed (kept minimal for slim image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
  && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create non-root user and switch
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8080

# Simple healthcheck hitting the Flask health endpoint
HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.getenv('PORT','8080'))"

# Gunicorn with gthread workers; override via env if desired
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-k", "gthread", "--threads", "4", "--workers", "2", "app:app"]


