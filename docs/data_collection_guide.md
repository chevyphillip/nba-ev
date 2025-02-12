# NBA Data Collection Guide

This guide provides detailed information about the data collection process in the NBA Expected Value Analysis project.

## Data Sources

### 1. Rotowire Lineup Information

The `NBALineupScraper` class in `lineups_scraper.py` collects real-time lineup information:

```python
from src.collectors.lineups_scraper import NBALineupScraper

# Initialize scraper
scraper = NBALineupScraper()

# Get current lineups
lineups_df = scraper.get_lineups()
```

#### Data Points Collected

- Team names and abbreviations
- Player names
- Player positions
- Player status (Active, GTD, OUT)
- Game time and date
- Venue information

### 2. Basketball Reference Statistics

The `BasketballReferenceCollector` in `basketball_reference.py` gathers historical statistics:

```python
from src.collectors.basketball_reference import BasketballReferenceCollector

# Initialize collector
collector = BasketballReferenceCollector()

# Get season statistics
season_stats = collector.get_season_stats(season="2023-24")

# Get player statistics
player_stats = collector.get_player_season_stats(player_name="Player Name")
```

#### Available Statistics

- Season averages
- Player career statistics
- Team historical data
- Advanced metrics

### 3. NBA API Integration

The `NBAAPICollector` in `nba_api.py` provides access to official NBA statistics:

```python
from src.collectors.nba_api import NBAAPICollector

# Initialize collector
nba_collector = NBAAPICollector()

# Get advanced team statistics
team_stats = nba_collector.get_team_advanced_stats()

# Get player advanced statistics
player_stats = nba_collector.get_player_advanced_stats()
```

#### Available Data

- Advanced team metrics
- Player performance statistics
- Real-time game data
- Historical game logs

### 4. Odds API Integration

The `OddsAPICollector` in `odds_api.py` collects betting market data:

```python
from src.collectors.odds_api import OddsAPICollector
import os

# Initialize collector with API key
collector = OddsAPICollector(api_key=os.getenv("ODDS_API_KEY"))

# Get current NBA odds
odds_data = collector.get_nba_odds()
```

#### Market Data Available

- Moneyline odds
- Point spreads
- Game totals
- Live betting lines

## Data Collection Pipeline

### 1. Setup and Configuration

1. Environment Setup:

   ```bash
   # Create .env file
   touch .env
   
   # Add required API keys
   echo "ODDS_API_KEY=your_api_key_here" >> .env
   ```

2. Dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### 2. Data Collection Process

1. Initialize Collectors:

   ```python
   from src.collectors import (
       NBALineupScraper,
       BasketballReferenceCollector,
       NBAAPICollector,
       OddsAPICollector
   )
   
   # Initialize all collectors
   lineup_scraper = NBALineupScraper()
   bref_collector = BasketballReferenceCollector()
   nba_collector = NBAAPICollector()
   odds_collector = OddsAPICollector()
   ```

2. Collect Data:

   ```python
   # Get current lineups
   lineups = lineup_scraper.get_lineups()
   
   # Get season statistics
   season_stats = bref_collector.get_season_stats()
   
   # Get advanced metrics
   advanced_stats = nba_collector.get_team_advanced_stats()
   
   # Get betting odds
   odds = odds_collector.get_nba_odds()
   ```

### 3. Data Validation

The collection process includes built-in validation:

- Data type checking
- Missing value detection
- Duplicate entry removal
- Format standardization

### 4. Error Handling

The collectors implement robust error handling:

```python
try:
    lineups = scraper.get_lineups()
except Exception as e:
    logger.error(f"Error collecting lineup data: {e}")
    # Implement fallback or retry logic
```

## Best Practices

1. **Rate Limiting**
   - Respect API rate limits
   - Implement appropriate delays between requests
   - Cache responses when possible

2. **Data Freshness**
   - Check data timestamps
   - Implement update frequency rules
   - Archive historical data

3. **Resource Management**
   - Close connections properly
   - Release system resources
   - Manage memory usage

4. **Monitoring**
   - Log collection activities
   - Track success/failure rates
   - Monitor data quality

## Troubleshooting

Common issues and solutions:

1. **Connection Errors**
   - Check internet connectivity
   - Verify API keys
   - Ensure proper proxy configuration

2. **Data Quality Issues**
   - Validate input data
   - Check for schema changes
   - Verify data transformations

3. **Performance Problems**
   - Optimize request patterns
   - Implement caching
   - Use appropriate timeouts

## Future Improvements

1. **Scalability**
   - Implement async data collection
   - Add database integration
   - Optimize resource usage

2. **Features**
   - Add more data sources
   - Implement real-time updates
   - Enhance error recovery

3. **Integration**
   - Add API endpoints
   - Implement webhooks
   - Create monitoring dashboard
