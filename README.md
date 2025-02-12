# NBA Data Analytics and Visualization Platform

A comprehensive platform for collecting, analyzing, and visualizing NBA data with real-time monitoring capabilities. This project combines data collection from multiple sources, advanced statistical analysis, and interactive visualizations with robust monitoring and logging.

## 🌟 Features

- **Data Collection**
  - Real-time NBA data collection from multiple sources
  - Rate-limited and cached data fetching
  - Automated data validation and cleaning
  - Historical data backfilling capabilities

- **Analysis & Visualization**
  - Advanced statistical analysis and data processing
  - Interactive visualizations and dashboards
  - Player and team performance metrics
  - Historical trend analysis

- **Monitoring & Infrastructure**
  - Prometheus/Grafana monitoring system
  - Real-time metric collection
  - Log aggregation with Loki
  - Resource usage tracking
  - Health checks and alerts

- **Development**
  - Containerized deployment with Podman/Docker
  - Efficient data storage with SQLAlchemy
  - Comprehensive test suite
  - Type-checked Python codebase

## 📋 Prerequisites

- Python 3.9+
- Podman or Docker
- Redis (handled by containers)
- 4GB+ RAM for running all services
- Git for version control

## 🚀 Quick Start

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/nba-ev.git
   cd nba-ev
   ```

2. **Set Up Python Environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start Services**

   ```bash
   # Start all services
   podman-compose up -d

   # Verify services are running
   podman-compose ps
   ```

5. **Access Dashboards**
   - Grafana: <http://localhost:3000> (admin/admin)
   - Prometheus: <http://localhost:9090>
   - Application Metrics: <http://localhost:8000/metrics>

## 📊 Data Collection

Start collecting NBA data:

```bash
# Test collection for a single season
python src/collectors/test_collection.py

# Full historical collection
python src/collectors/historical_data.py
```

Monitor collection progress in Grafana dashboard.

## 📈 Monitoring Setup

The monitoring stack includes:

- **Prometheus**: Metric collection and storage
  - Collection progress metrics
  - System resource usage
  - Application performance metrics

- **Grafana**: Visualization and dashboards
  - Real-time collection monitoring
  - System resource usage
  - Application logs
  - Performance metrics

- **Loki**: Log aggregation
  - Application logs
  - Collection error tracking
  - Debug information

## 🔧 Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
pylint src/
```

### Adding New Features

1. Create a feature branch
2. Write tests in `tests/`
3. Implement feature in `src/`
4. Update documentation
5. Submit pull request

## 📁 Project Structure

```
nba-ev/
├── data/                  # Data storage
│   ├── historical/       # Historical data
│   ├── raw/             # Raw collected data
│   └── processed/       # Cleaned data
├── docs/                 # Documentation
│   ├── setup/           # Setup guides
│   ├── guides/          # User guides
│   ├── api/             # API documentation
│   └── architecture/    # System design docs
├── monitoring/          # Monitoring config
│   ├── grafana/        # Grafana dashboards
│   ├── prometheus/     # Prometheus config
│   └── loki/          # Logging config
├── notebooks/          # Jupyter notebooks
├── scripts/            # Utility scripts
├── src/                # Source code
│   ├── analysis/      # Data analysis
│   ├── collectors/    # Data collectors
│   ├── cleaning/      # Data cleaning
│   ├── database/      # Database models
│   ├── frontend/      # Web interface
│   ├── monitoring/    # Metrics code
│   └── visualization/ # Plotting code
├── tests/             # Test suite
└── visualizations/    # Output graphics
```

## 📚 Documentation

- [Installation Guide](docs/setup/installation.md)
- [Configuration Guide](docs/setup/configuration.md)
- [Monitoring Setup](docs/setup/monitoring.md)
- [Data Collection Guide](docs/guides/data_collection.md)
- [Analysis Guide](docs/guides/analysis.md)
- [Visualization Guide](docs/guides/visualization.md)
- [Architecture Overview](docs/architecture/overview.md)
- [API Documentation](docs/api/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a pull request

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- NBA API providers
- Open-source monitoring tools
- Python data science community

## 🔮 Future Enhancements

1. **Advanced Analytics**
   - Machine learning predictions
   - Player performance forecasting
   - Injury risk assessment

2. **Infrastructure**
   - Kubernetes deployment
   - Automated scaling
   - Cloud provider templates

3. **Features**
   - Real-time game tracking
   - Mobile app integration
   - API service layer

## 📞 Contact & Support

- **Author**: Your Name
- **Email**: <your.email@example.com>
- **GitHub**: [@yourusername](https://github.com/yourusername)
- **Issues**: [GitHub Issues](https://github.com/yourusername/nba-ev/issues)

For support questions, please use GitHub Issues or email.
