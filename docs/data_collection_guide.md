# NBA-EV Data Collection Guide

## Overview

This guide documents the data collection process for the NBA-EV project, including data sources, collection methods, and best practices for maintaining data quality.

## Data Sources

### 1. NBA API (`src/collectors/nba_api.py`)

The NBA API provides official statistics and advanced metrics.

```python
from nba_api.stats.endpoints import leaguedashteamstats, leaguedashplayerstats

def get_team_advanced_stats():
    """Collect team advanced statistics from NBA API."""
    response = leaguedashteamstats.LeagueDashTeamStats(
        measure_type_detailed_defense='Advanced',
        per_mode_detailed='PerGame',
        season='2023-24'
    )
    return pd.DataFrame(response.get_data_frames()[0])

def get_player_advanced_stats():
    """Collect player advanced statistics from NBA API."""
    response = leaguedashplayerstats.LeagueDashPlayerStats(
        measure_type_detailed_defense='Advanced',
        per_mode_detailed='PerGame',
        season='2023-24'
    )
    return pd.DataFrame(response.get_data_frames()[0])
```

### 2. Basketball Reference (`src/collectors/basketball_reference.py`)

Basketball Reference provides historical statistics and game logs.

```python
from basketball_reference_web_scraper import client

def get_season_stats(season_year: int):
    """Collect season statistics from Basketball Reference."""
    return pd.DataFrame(client.season_schedule(season=season_year))

def get_player_season_stats(season_year: int):
    """Collect player statistics from Basketball Reference."""
    return pd.DataFrame(client.players_season_totals(season_end_year=season_year))
```

### 3. Rotowire Lineups (`src/collectors/lineups_scraper.py`)

Real-time lineup and injury information from Rotowire.

```python
class LineupsCollector:
    """Collector for NBA lineup data from Rotowire."""
    
    def get_lineups(self):
        """Get current NBA lineups for all games."""
        return self._scrape_lineups()
    
    def get_injuries(self):
        """Get current NBA injury reports."""
        return self._scrape_injuries()
    
    def get_depth_charts(self):
        """Get NBA team depth charts."""
        return self._scrape_depth_charts()
```

### 4. Odds API (`src/collectors/odds_api.py`)

Game odds and betting information.

```python
class OddsAPICollector:
    """Collector for NBA odds data."""
    
    def get_nba_odds(self):
        """Get current NBA game odds."""
        return self._fetch_odds()
```

## Collection Process

### 1. Authentication

```python
# Load environment variables
load_dotenv()

# Initialize collectors with API keys
odds_api_key = os.getenv("ODDS_API_KEY")
odds_collector = OddsAPICollector(odds_api_key)
```

### 2. Data Collection

```python
async def collect_data():
    """Collect data from all sources."""
    # NBA API data
    team_stats = get_team_advanced_stats()
    player_stats = get_player_advanced_stats()
    
    # Basketball Reference data
    season_stats = get_season_stats(2024)
    player_season_stats = get_player_season_stats(2024)
    
    # Rotowire data
    lineups_collector = LineupsCollector()
    lineups = lineups_collector.get_lineups()
    injuries = lineups_collector.get_injuries()
    depth_charts = lineups_collector.get_depth_charts()
    
    # Odds data
    odds = await odds_collector.get_nba_odds()
    
    return {
        'team_stats': team_stats,
        'player_stats': player_stats,
        'season_stats': season_stats,
        'player_season_stats': player_season_stats,
        'lineups': lineups,
        'injuries': injuries,
        'depth_charts': depth_charts,
        'odds': odds
    }
```

## Error Handling

### 1. API Rate Limits

```python
def handle_rate_limit(func):
    """Decorator for handling API rate limits."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise
    return wrapper
```

### 2. Connection Errors

```python
def handle_connection_errors(func):
    """Decorator for handling connection errors."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger.error(f"Connection error: {e}")
            return None
    return wrapper
```

### 3. Data Validation

```python
def validate_data(data: dict) -> bool:
    """Validate collected data."""
    required_columns = {
        'team_stats': ['team', 'wins', 'losses', 'offensive_rating'],
        'player_stats': ['name', 'team', 'ppg_x', 'mpg_x'],
        'lineups': ['home_team', 'away_team', 'date'],
        'odds': ['home_team', 'away_team', 'odds']
    }
    
    for key, columns in required_columns.items():
        if key not in data or not all(col in data[key].columns for col in columns):
            return False
    return True
```

## Data Quality Checks

### 1. Completeness Check

```python
def check_data_completeness(data: dict) -> bool:
    """Check if all required data is present."""
    return all(
        not df.empty
        for df in data.values()
        if isinstance(df, pd.DataFrame)
    )
```

### 2. Consistency Check

```python
def check_data_consistency(data: dict) -> bool:
    """Check for data consistency across sources."""
    team_names = set(data['team_stats']['team'])
    return all(
        team in team_names
        for df in [data['lineups'], data['odds']]
        for team in df[['home_team', 'away_team']].values.flatten()
    )
```

## Best Practices

### 1. Data Collection

- Use asynchronous operations for API calls
- Implement proper rate limiting
- Handle errors gracefully
- Validate data immediately after collection

### 2. Data Storage

- Store raw data before processing
- Use consistent date formats
- Maintain data versioning
- Implement backup procedures

### 3. Monitoring

- Log all collection activities
- Track API usage and limits
- Monitor data quality metrics
- Alert on collection failures

### 4. Maintenance

- Update API credentials regularly
- Review and update rate limits
- Monitor for API changes
- Update data schemas as needed

## Configuration

### 1. Environment Variables

```bash
# .env file
ODDS_API_KEY=your_api_key
NBA_API_KEY=your_api_key
PROXY_URL=your_proxy_url
```

### 2. Collection Settings

```python
# settings.py
COLLECTION_SETTINGS = {
    'max_retries': 3,
    'retry_delay': 2,
    'timeout': 30,
    'batch_size': 100
}
```

## Future Enhancements

1. **Additional Data Sources**:
   - Player tracking data
   - Social media sentiment
   - Injury history database
   - Advanced analytics providers

2. **Collection Improvements**:
   - Parallel data collection
   - Incremental updates
   - Real-time streaming
   - Historical data backfilling

3. **Quality Improvements**:
   - Machine learning validation
   - Automated anomaly detection
   - Data quality scoring
   - Source reliability tracking

4. **Infrastructure**:
   - Distributed collection
   - Cloud storage integration
   - Automated failover
   - Load balancing
