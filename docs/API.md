# API Documentation

## Classes

### NBADataCollector

The `NBADataCollector` class handles data collection from various sources including Basketball Reference and The Odds API.

#### Constructor

```python
def __init__(self, odds_api_key: str)
```

**Parameters:**

- `odds_api_key` (str): API key for The Odds API

#### Methods

##### get_team_stats

```python
def get_team_stats(self) -> pd.DataFrame
```

Collects team statistics from Basketball Reference and NBA API.

**Returns:**

- DataFrame containing merged team statistics including:
  - Basic stats (points, games played)
  - Advanced metrics (offensive/defensive ratings)
  - Pace and possession statistics

##### get_player_stats

```python
def get_player_stats(self) -> pd.DataFrame
```

Collects player statistics from NBA API and Basketball Reference.

**Returns:**

- DataFrame containing merged player statistics including:
  - Season totals
  - Advanced metrics
  - Per-game averages

##### get_odds_data

```python
async def get_odds_data(self) -> Dict
```

Collects current odds data from The Odds API using httpx.

**Returns:**

- Dictionary containing current betting odds for NBA games

##### get_injuries_and_lineups

```python
def get_injuries_and_lineups(self) -> Tuple[pd.DataFrame, pd.DataFrame]
```

Collects current injuries and lineup data from NBA API.

**Returns:**

- Tuple of DataFrames containing injury reports and lineup information

### NBAAnalyzer

The `NBAAnalyzer` class analyzes collected NBA data and generates predictions.

#### Constructor

```python
def __init__(self, data_collector: NBADataCollector)
```

**Parameters:**

- `data_collector` (NBADataCollector): Instance of NBADataCollector for data retrieval

#### Methods

##### update_data

```python
async def update_data(self)
```

Updates all data from sources.

##### calculate_pace_factors

```python
def calculate_pace_factors(self) -> pd.DataFrame
```

Calculates pace factors for each team.

**Returns:**

- DataFrame containing team pace and possession statistics

##### calculate_efficiency_metrics

```python
def calculate_efficiency_metrics(self) -> Tuple[pd.DataFrame, pd.DataFrame]
```

Calculates efficiency metrics for teams and players.

**Returns:**

- Tuple of DataFrames containing team and player efficiency metrics

##### simulate_game

```python
def simulate_game(self, team1: str, team2: str, n_simulations: int = 10000) -> Dict[str, Any]
```

Simulates a game between two teams using Monte Carlo simulation.

**Parameters:**

- `team1` (str): Name of first team
- `team2` (str): Name of second team
- `n_simulations` (int): Number of simulations to run (default: 10000)

**Returns:**

- Dictionary containing:
  - Win probabilities for both teams
  - Average projected scores

## Utility Functions

### save_to_excel

```python
def save_to_excel(data: Dict[str, Optional[pd.DataFrame]], filename: str)
```

Saves collected data to an Excel file.

**Parameters:**

- `data` (Dict[str, Optional[pd.DataFrame]]): Dictionary of DataFrames to save
- `filename` (str): Output Excel filename

## Data Structures

### Team Statistics DataFrame

The team statistics DataFrame contains the following key columns:

- `team`: Team name/abbreviation
- `points_for`: Average points scored
- `points_against`: Average points allowed
- `games_played`: Number of games played
- `net_rating`: Point differential per 100 possessions
- `win_pct`: Win percentage
- Advanced NBA API metrics (PACE, OFF_RATING, DEF_RATING, etc.)

### Player Statistics DataFrame

The player statistics DataFrame contains the following key columns:

- `name`: Player name
- `team`: Team abbreviation
- `positions`: Player positions
- `age`: Player age
- Basic statistics (points, rebounds, assists, etc.)
- Advanced metrics (PIE, USG_PCT, efficiency ratings, etc.)

## Usage Examples

### Basic Data Collection

```python
from nba_stats import NBADataCollector, NBAAnalyzer

# Initialize collector with API key
collector = NBADataCollector(odds_api_key="your_api_key")

# Get team statistics
team_stats = collector.get_team_stats()

# Get player statistics
player_stats = collector.get_player_stats()
```

### Game Simulation

```python
# Initialize analyzer
analyzer = NBAAnalyzer(collector)

# Update data
await analyzer.update_data()

# Simulate a game
result = analyzer.simulate_game("Lakers", "Celtics")
print(f"Lakers win probability: {result['team1_win_prob']:.2%}")
print(f"Projected score: {result['average_score']['team1']:.1f} - {result['average_score']['team2']:.1f}")
```

### Efficiency Analysis

```python
# Calculate efficiency metrics
team_efficiency, player_efficiency = analyzer.calculate_efficiency_metrics()

# Get top 10 most efficient players
top_players = player_efficiency.nlargest(10, 'PIE')
print("Top 10 players by PIE:")
print(top_players[['name', 'team', 'PIE']])
```
