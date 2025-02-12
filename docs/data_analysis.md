# NBA-EV Data Analysis Guide

## Overview

The NBA-EV project implements comprehensive data analysis methodologies to extract insights from NBA statistics. This guide documents the analysis modules, metrics calculations, and statistical methods used in the project.

## Analysis Modules

### 1. Team Efficiency Analysis (`src/analysis/efficiency.py`)

#### Offensive and Defensive Ratings

```python
def calculate_team_efficiency(team_stats: pd.DataFrame) -> pd.DataFrame:
    """Calculate comprehensive team efficiency metrics."""
    efficiency = team_stats.copy()
    
    # Basic Four Factors
    efficiency['four_factors_score'] = (
        0.4 * efficiency['efg_pct'] +
        0.25 * efficiency['tov_pct'] * -1 +
        0.2 * efficiency['oreb_pct'] +
        0.15 * efficiency['ft_rate']
    )
    
    # Per 100 Possessions Stats
    if 'possessions' in efficiency.columns:
        stats_per_100 = ['points', 'assists', 'rebounds']
        for stat in stats_per_100:
            efficiency[f'{stat}_per_100'] = (
                efficiency[stat] / efficiency['possessions'] * 100
            )
    
    return efficiency
```

#### Pace Factors

```python
def calculate_pace_factors(team_stats: pd.DataFrame) -> pd.DataFrame:
    """Calculate comprehensive pace and tempo metrics."""
    pace = team_stats.copy()
    
    # Basic Pace (Possessions per 48 minutes)
    if 'possessions' in pace.columns:
        pace['pace_per_48'] = pace['possessions'] / (pace['minutes'] / 48)
        
        # Relative Pace
        league_avg_pace = pace['pace'].mean()
        pace['relative_pace'] = (
            (pace['pace'] - league_avg_pace) / league_avg_pace * 100
        )
    
    return pace
```

### 2. Player Analysis

#### Player Efficiency

```python
def calculate_player_efficiency(player_stats: pd.DataFrame) -> pd.DataFrame:
    """Calculate player efficiency metrics."""
    efficiency = player_stats.copy()
    
    # Usage Tiers
    efficiency['usage_tier'] = pd.qcut(
        efficiency['usg%'].fillna(efficiency['usg%'].mean()),
        q=5,
        labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
    )
    
    # Scoring Efficiency
    efficiency['points_per_minute'] = (
        efficiency['ppg_x'] / efficiency['mpg_x'].replace(0, 1)
    )
    
    return efficiency
```

### 3. Matchup Analysis

```python
def calculate_matchup_adjustments(
    team_stats: pd.DataFrame,
    player_stats: pd.DataFrame
) -> pd.DataFrame:
    """Calculate matchup-based adjustments."""
    adjustments = pd.DataFrame()
    
    # Defense Factors
    league_avg_drtg = team_stats['defensive_rating'].mean()
    defense_factors = team_stats['defensive_rating'] / league_avg_drtg
    
    # Pace Factors
    league_avg_pace = team_stats['pace'].mean()
    pace_factors = team_stats['pace'] / league_avg_pace
    
    adjustments = pd.DataFrame({
        'team': team_stats['team'],
        'defense_factor': defense_factors,
        'pace_factor': pace_factors
    })
    
    return adjustments
```

## Statistical Methods

### 1. Data Normalization

```python
def normalize_statistics(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """Normalize statistical columns to a 0-1 scale."""
    df_norm = df.copy()
    for col in columns:
        df_norm[f'{col}_normalized'] = (
            (df[col] - df[col].min()) /
            (df[col].max() - df[col].min())
        )
    return df_norm
```

### 2. Outlier Detection

```python
def detect_outliers(df: pd.DataFrame, column: str, threshold: float = 1.5) -> pd.Series:
    """Detect statistical outliers using IQR method."""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    
    return df[
        (df[column] < Q1 - threshold * IQR) |
        (df[column] > Q3 + threshold * IQR)
    ]
```

### 3. Performance Metrics

```python
def calculate_performance_metrics(stats_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate comprehensive performance metrics."""
    metrics = stats_df.copy()
    
    # Shooting Efficiency
    metrics['true_shooting'] = (
        metrics['points'] /
        (2 * (metrics['fga'] + 0.44 * metrics['fta']))
    )
    
    # Usage Rate
    metrics['usage_rate'] = (
        (metrics['fga'] + 0.44 * metrics['fta'] + metrics['turnovers']) /
        metrics['possessions']
    )
    
    return metrics
```

## Analysis Workflows

### 1. Team Performance Analysis

```python
def analyze_team_performance(team_stats: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Complete team performance analysis workflow."""
    results = {}
    
    # Efficiency metrics
    results['efficiency'] = calculate_team_efficiency(team_stats)
    
    # Pace analysis
    results['pace'] = calculate_pace_factors(team_stats)
    
    # Performance metrics
    results['performance'] = calculate_performance_metrics(team_stats)
    
    return results
```

### 2. Player Performance Analysis

```python
def analyze_player_performance(
    player_stats: pd.DataFrame,
    min_minutes: float = 10.0
) -> Dict[str, pd.DataFrame]:
    """Complete player performance analysis workflow."""
    results = {}
    
    # Filter for minimum minutes
    qualified_players = player_stats[player_stats['mpg_x'] >= min_minutes]
    
    # Efficiency metrics
    results['efficiency'] = calculate_player_efficiency(qualified_players)
    
    # Performance metrics
    results['performance'] = calculate_performance_metrics(qualified_players)
    
    return results
```

## Best Practices

### 1. Data Quality

- Handle missing values appropriately
- Remove or flag outliers
- Validate input data types
- Check for data consistency

### 2. Performance

- Use vectorized operations
- Optimize memory usage
- Cache intermediate results
- Profile computation time

### 3. Documentation

- Document assumptions
- Explain methodologies
- Include example usage
- Provide interpretation guides

### 4. Testing

- Unit test core functions
- Validate output ranges
- Check edge cases
- Verify calculations

## Future Enhancements

1. **Advanced Analytics**:
   - Player impact metrics
   - Lineup optimization
   - Win probability models
   - Shot quality analysis

2. **Machine Learning**:
   - Performance prediction
   - Player clustering
   - Injury risk assessment
   - Game outcome prediction

3. **Real-time Analysis**:
   - Live game analytics
   - In-game adjustments
   - Performance tracking
   - Trend analysis

4. **Visualization**:
   - Interactive dashboards
   - Custom plot types
   - Real-time updates
   - Export capabilities
