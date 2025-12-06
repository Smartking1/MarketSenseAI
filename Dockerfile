# Production Dockerfile for FastAPI application
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Cloud Run uses PORT environment variable
ENV PORT=8080
ENV ENVIRONMENT=production
ENV DEBUG=False

# Expose port
EXPOSE 8080

# Health check - calls root endpoint which responds immediately
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Run through startup wrapper that handles environment setup
CMD exec python src/cloud_run_startup.py
