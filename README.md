# NBA Stats and Betting Analysis Tool

A comprehensive Python-based tool for collecting and analyzing NBA statistics and betting data. This tool leverages multiple data sources including Basketball Reference and the NBA API to provide detailed insights for basketball analysis and betting purposes.

## 🚀 Features

### Data Collection

- **Team Statistics**
  - Advanced metrics from NBA API (PACE, Offensive/Defensive Ratings)
  - Historical game data from Basketball Reference
  - Win/Loss records and scoring statistics
- **Player Statistics**
  - Advanced player metrics
  - Season totals and per-game averages
  - Efficiency ratings and usage statistics
- **Betting Information**
  - Real-time odds data from The Odds API
  - Multiple betting markets (h2h, spreads, totals)
  - US region odds in decimal format

### Analysis Capabilities

- **Team Analysis**
  - Pace factors calculation
  - Offensive and defensive efficiency metrics
  - Net rating analysis
- **Player Analysis**
  - Player Impact Estimate (PIE)
  - Usage percentages
  - Efficiency ratings
- **Game Simulation**
  - Monte Carlo simulation for game outcomes
  - Win probability calculations
  - Projected scoring distributions

### Data Export

- Automated Excel report generation
- Multiple data sheets for different metrics
- Daily updates with timestamp-based filenames

## 📋 Requirements

### System Requirements

- Python 3.11 or higher
- Operating system: Windows/macOS/Linux

### Dependencies

```bash
pandas>=2.1.0
numpy>=1.24.0
basketball-reference-web-scraper>=4.15.3
nba-api>=1.7
httpx>=0.28.1
openpyxl>=3.1.2
python-dotenv>=1.0.0
```

## 🛠️ Installation

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd nba-ev
   ```

2. **Install Dependencies**
   Using uv (recommended):

   ```bash
   uv sync
   ```

   Or using pip:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   Create a `.env` file in the project root:

   ```
   ODDS_API_KEY=your_odds_api_key_here
   ```

## 📊 Usage

### Basic Usage

Run the main script:

```bash
python collect_nba_stats.py
```

### Output

The script generates an Excel file (`nba_stats_YYYYMMDD.xlsx`) containing:

- Team statistics
- Player statistics
- Pace factors
- Team efficiency metrics
- Player efficiency metrics

### Example Analysis

```python
from nba_stats import NBAAnalyzer

# Initialize analyzer
analyzer = NBAAnalyzer(collector)

# Simulate a game
result = analyzer.simulate_game("Lakers", "Celtics", n_simulations=10000)
print(f"Win probability: {result['team1_win_prob']:.2%}")
```

## 📚 Data Sources

### Basketball Reference

- Team and player statistics
- Historical game data
- Season totals and averages

### NBA API

- Advanced team metrics
- Player performance data
- Real-time statistics

### The Odds API

- Current betting odds
- Multiple betting markets
- US sportsbook data

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new features
- Update documentation as needed
- Use type hints for better code clarity

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔍 API Documentation

For detailed API documentation, see [API.md](docs/API.md).

## 🛣️ Roadmap

- [ ] Add support for historical odds data
- [ ] Implement machine learning predictions
- [ ] Add player prop betting analysis
- [ ] Create web interface for data visualization
- [ ] Add support for real-time updates during games

## 📫 Support

For support, please open an issue in the GitHub repository or contact the maintainers directly.
