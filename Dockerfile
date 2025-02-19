# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and UV
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# Create virtual environment
RUN uv venv /app/venv

# Activate virtual environment in subsequent commands
ENV PATH="/app/venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/venv"

# Install prometheus-client directly
RUN . /app/venv/bin/activate && pip install prometheus-client==0.17.0

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies and verify installation
RUN . /app/venv/bin/activate && \
    uv pip install -r requirements.txt && \
    uv pip list | grep redis

# Copy the rest of the application
COPY . .

# Create a non-root user
RUN useradd -m worker && chown -R worker:worker /app
USER worker

# Set Python path
ENV PYTHONPATH=/app

# Command to run the worker
CMD ["python", "-m", "src.workers.scraper_worker"] 