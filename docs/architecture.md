# NBA Expected Value Analysis - Architecture Overview

## System Architecture

The NBA Expected Value Analysis project is structured as a modular Python application with several key components:

### 1. Data Collection Layer (`src/collectors/`)

#### Lineup Scraper (`lineups_scraper.py`)

- Real-time scraping of NBA lineup information from Rotowire
- Player status tracking (Active, GTD, OUT, etc.)
- Play probability estimation
- Team identification and game time tracking

#### Basketball Reference Collector (`basketball_reference.py`)

- Season statistics collection
- Player performance metrics
- Team statistics and records
- Historical data access

#### NBA API Integration (`nba_api.py`)

- Advanced statistics collection
- Player and team metrics
- Real-time game data
- Detailed performance analytics

#### Odds API Integration (`odds_api.py`)

- Betting odds collection
- Game probability calculations
- Market movement tracking

### 2. Analysis Layer (`src/analysis/`)

#### Efficiency Analysis (`efficiency.py`)

- Team efficiency calculations
- Player performance metrics
- Pace factor analysis
- Advanced statistical computations

#### Data Cleaning (`data/clean_data.py`)

- Data validation and cleaning
- Format standardization
- Missing data handling
- Outlier detection

### 3. Visualization Layer (`src/visualization/`)

#### Plot Generation (`plots.py`)

- Statistical visualizations
- Performance charts
- Trend analysis graphs
- Interactive data displays

## Data Flow

1. **Data Collection**

   ```
   External Sources → Collectors → Raw Data
   (Rotowire, NBA API, Basketball Reference) → (Scrapers, API Clients) → (JSON, DataFrames)
   ```

2. **Data Processing**

   ```
   Raw Data → Cleaning → Analysis → Processed Data
   (JSON, DataFrames) → (Validation, Standardization) → (Calculations, Metrics) → (Clean DataFrames)
   ```

3. **Data Presentation**

   ```
   Processed Data → Visualization → Output
   (Clean DataFrames) → (Plots, Charts) → (PNG, Interactive Displays)
   ```

## Component Interactions

### Data Collection Components

```python
NBALineupScraper
├── _setup_driver()      # Configure web scraping
├── _get_page_content()  # Fetch raw HTML
├── _extract_team_name() # Parse team information
├── _parse_lineup_section() # Extract lineup data
└── get_lineups()        # Main public interface

BasketballReferenceCollector
├── get_season_stats()   # Fetch season data
└── get_player_season_stats() # Fetch player data

NBAAPICollector
├── get_team_advanced_stats()   # Advanced team metrics
├── get_player_advanced_stats() # Advanced player metrics
└── get_real_time_data()        # Live game data

OddsAPICollector
└── get_nba_odds()      # Fetch betting odds
```

### Analysis Components

```python
EfficiencyAnalyzer
├── calculate_team_efficiency()    # Team metrics
├── calculate_player_efficiency()  # Player metrics
└── calculate_pace_factors()       # Pace analysis

DataCleaner
├── clean_team_stats()    # Team data cleaning
├── clean_player_stats()  # Player data cleaning
└── prepare_data_for_visualization() # Final preparation
```

### Visualization Components

```python
Visualizer
├── create_offensive_defensive_plot()
├── create_pace_analysis()
├── create_win_percentage_plot()
├── create_scoring_distribution()
└── create_player_visualizations()
```

## Testing Strategy

The project uses pytest for testing, with tests organized in the `tests/` directory:

```
tests/
└── test_lineups_scraper.py  # Test lineup scraping functionality
```

## Dependencies

Key external dependencies:

- `selenium`: Web scraping
- `beautifulsoup4`: HTML parsing
- `pandas`: Data manipulation
- `numpy`: Numerical computations
- `matplotlib/seaborn`: Visualization
- `requests`: API communication

## Configuration

Environment variables (`.env`):

```
ODDS_API_KEY=<api_key>
```

## Future Considerations

1. **Scalability**
   - Implement caching for API calls
   - Add database integration
   - Implement async data collection

2. **Features**
   - Add more advanced statistical models
   - Implement real-time updates
   - Expand visualization options

3. **Integration**
   - Add more data sources
   - Implement API endpoints
   - Create web interface
