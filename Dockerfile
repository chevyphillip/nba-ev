# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY data/ ./data/

# Set environment variables
ENV PYTHONPATH=/app
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV PROMETHEUS_MULTIPROC_DIR=/tmp

# Create volume for persistent data storage
VOLUME ["/app/data"]

# Expose metrics port
EXPOSE 8000

# Copy the startup script
COPY scripts/start.sh .
RUN chmod +x start.sh

# Run both the metrics server and collection script
CMD ["./start.sh"] 