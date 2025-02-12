# Installation Guide

This guide provides detailed instructions for setting up the NBA Data Analytics and Visualization Platform.

## System Requirements

### Hardware Requirements

- CPU: 2+ cores recommended
- RAM: 4GB minimum, 8GB recommended
- Storage: 20GB+ free space

### Software Requirements

- Python 3.9 or higher
- Podman or Docker
- Git
- Make (optional, for using Makefile commands)

## Step-by-Step Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/nba-ev.git
cd nba-ev
```

### 2. Python Environment Setup

#### Using venv (recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
## On Linux/macOS
source .venv/bin/activate
## On Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Using conda (alternative)

```bash
# Create conda environment
conda create -n nba-ev python=3.9
conda activate nba-ev
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
## Linux/macOS
nano .env
## Windows
notepad .env
```

Required environment variables:

```env
# Application Settings
APP_ENV=development
DEBUG=true

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379

# Monitoring Settings
PROMETHEUS_MULTIPROC_DIR=/tmp
```

### 4. Container Setup

#### Using Podman (recommended)

```bash
# Install Podman if not installed
## On macOS
brew install podman
## On Linux
sudo apt-get install podman  # Ubuntu/Debian
sudo dnf install podman      # Fedora

# Initialize Podman machine (macOS only)
podman machine init
podman machine start

# Start services
podman-compose up -d
```

#### Using Docker (alternative)

```bash
# Start services
docker-compose up -d
```

### 5. Verify Installation

```bash
# Check service status
podman-compose ps

# Verify metrics endpoint
curl http://localhost:8000/metrics

# Access dashboards
open http://localhost:3000  # Grafana
open http://localhost:9090  # Prometheus
```

### 6. Initial Data Collection

```bash
# Run test collection
python src/collectors/test_collection.py
```

## Post-Installation Setup

### 1. Grafana Configuration

1. Access Grafana at <http://localhost:3000>
2. Login with default credentials (admin/admin)
3. Change password when prompted
4. Verify data sources (Prometheus, Loki)
5. Import dashboards from monitoring/grafana/dashboards/

### 2. Data Directory Structure

```bash
# Create data directories if not exists
mkdir -p data/{raw,processed,historical}
```

### 3. Jupyter Environment

```bash
# Install Jupyter lab extensions
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install jupyterlab-plotly
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**

   ```bash
   # Check for port usage
   lsof -i :3000  # Grafana
   lsof -i :9090  # Prometheus
   lsof -i :8000  # Metrics
   ```

2. **Container Issues**

   ```bash
   # View container logs
   podman-compose logs app
   podman-compose logs prometheus
   ```

3. **Permission Issues**

   ```bash
   # Fix data directory permissions
   chmod -R 755 data/
   ```

### Health Checks

```bash
# Check application health
curl http://localhost:8000/health

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Loki status
curl http://localhost:3100/ready
```

## Updating

### Update Application

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Rebuild containers
podman-compose up -d --build
```

### Update Documentation

```bash
# Generate latest API docs
python scripts/generate_docs.py
```

## Next Steps

1. Review the [Configuration Guide](configuration.md)
2. Set up [Monitoring](monitoring.md)
3. Start [Collecting Data](../guides/data_collection.md)

## Support

For issues and support:

1. Check the [Troubleshooting Guide](../guides/troubleshooting.md)
2. Search [GitHub Issues](https://github.com/yourusername/nba-ev/issues)
3. Create a new issue if needed
