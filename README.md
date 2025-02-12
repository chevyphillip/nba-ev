# NBA Expected Value Analysis

## Overview

This project provides tools for analyzing NBA game data, with a focus on lineup information and player statistics. It combines data from multiple sources including Rotowire, Basketball Reference, and the NBA API to create comprehensive insights for game analysis.

## Features

- Real-time lineup information scraping
- Player status and probability tracking
- Team performance analytics
- Advanced statistical visualizations
- Automated data collection pipeline

## Documentation

Detailed documentation is available in the `docs` directory:

- [Architecture Overview](docs/architecture.md)
- [API Documentation](docs/API.md)
- [Data Collection Guide](docs/data_collection_guide.md)
- [Data Cleaning Guidelines](docs/data_cleaning.md)
- [Data Analysis Guide](docs/data_analysis.md)
- [Visualization Guide](docs/visualization_guide.md)
- [Analysis Insights](docs/analysis_insights.md)
- [Contributing Guidelines](docs/CONTRIBUTING.md)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/nba-ev.git
cd nba-ev
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` with your API keys:

```
ODDS_API_KEY=your_key_here
```

## Usage

### Lineup Scraping

```python
from src.collectors.lineups_scraper import NBALineupScraper

scraper = NBALineupScraper()
lineups = scraper.get_lineups()

# Access lineup information
for game_id, game_lineups in lineups.items():
    print(f"\nGame: {game_id}")
    for team, lineup_df in game_lineups.items():
        print(f"\n{team} Lineup:")
        print(lineup_df)
```

### Data Analysis

```python
from src.analysis.efficiency import calculate_team_efficiency
from src.collectors.basketball_reference import get_season_stats

# Get team statistics
team_stats = get_season_stats(2024)

# Calculate efficiency metrics
efficiency_metrics = calculate_team_efficiency(team_stats)
print(efficiency_metrics)
```

## Project Structure

```
nba-ev/
├── docs/               # Documentation files
├── src/               # Source code
│   ├── collectors/    # Data collection modules
│   │   ├── lineups_scraper.py
│   │   ├── basketball_reference.py
│   │   ├── nba_api.py
│   │   └── odds_api.py
│   ├── analysis/      # Analysis modules
│   ├── visualization/ # Visualization modules
│   └── data/         # Data processing
├── tests/            # Test files
└── requirements.txt  # Project dependencies
```

## Contributing

Please read [CONTRIBUTING.md](docs/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Basketball Reference](https://www.basketball-reference.com/)
- [NBA API](https://github.com/swar/nba_api)
- [Rotowire](https://www.rotowire.com/)
