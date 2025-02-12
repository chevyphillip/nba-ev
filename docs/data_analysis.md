# Data Analysis Guide

This guide describes the data analysis procedures and visualizations available in the NBA-EV project.

## Available Data

The project collects and processes several types of NBA statistics:

### Team Statistics (`team_stats`)

- Basic game data from Basketball Reference:
  - `start_time`: Game start time
  - `away_team`: Away team name
  - `home_team`: Home team name
  - `away_team_score`: Away team score
  - `home_team_score`: Home team score

- Advanced metrics from NBA API:
  - `offensive_rating`: Points scored per 100 possessions
  - `defensive_rating`: Points allowed per 100 possessions
  - `net_rating`: Point differential per 100 possessions
  - `pace`: Possessions per 48 minutes
  - `win_pct`: Win percentage
  - `ast_pct`: Assist percentage
  - `ast_to`: Assist to turnover ratio
  - `ast_ratio`: Assist ratio
  - `efg_pct`: Effective field goal percentage
  - `ts_pct`: True shooting percentage

### Efficiency Metrics (`team_efficiency`, `player_efficiency`)

- Team efficiency metrics:
  - `offensive_efficiency`: Normalized offensive rating
  - `defensive_efficiency`: Normalized defensive rating
  - Various advanced statistics ratios

- Player efficiency metrics:
  - `name`: Player name
  - `team`: Team abbreviation
  - `pie`: Player Impact Estimate
  - `usage_pct`: Usage percentage
  - Efficiency ratings and percentages

### Pace Factors (`pace_factors`)

- `team`: Team abbreviation
- `pace`: Team pace
- `possessions`: Total possessions
- `pace_factor`: Relative pace compared to league average

## Analysis Procedures

### 1. Data Loading

```python
import pandas as pd
from pathlib import Path

# Load most recent data file
data_dir = Path("data")
latest_file = sorted(data_dir.glob("nba_stats_*.xlsx"))[-1]
data = pd.read_excel(latest_file, sheet_name=None)

# Access specific sheets
team_stats = data['team_stats']
player_stats = data['player_stats']
team_efficiency = data['team_efficiency']
player_efficiency = data['player_efficiency']
pace_factors = data['pace_factors']
```

### 2. Team Performance Analysis

#### Offensive vs Defensive Ratings

```python
plt.figure(figsize=(12, 8))
plt.scatter(team_stats['offensive_rating'], 
           team_stats['defensive_rating'], 
           alpha=0.6)

# Add team labels
for i, txt in enumerate(team_stats['team']):
    plt.annotate(str(txt), 
                (team_stats['offensive_rating'].iloc[i],
                 team_stats['defensive_rating'].iloc[i]))

plt.xlabel('Offensive Rating')
plt.ylabel('Defensive Rating')
plt.title('Team Offensive vs Defensive Ratings')
```

#### Pace Analysis

```python
plt.figure(figsize=(15, 6))
sns.barplot(data=pace_factors.sort_values('pace', ascending=False),
            x='team', y='pace')

plt.xticks(rotation=45, ha='right')
plt.title('Team Pace Factors')
```

#### Scoring Distribution

```python
# Combine home and away scores
scores = pd.concat([
    team_stats['home_team_score'],
    team_stats['away_team_score']
])

plt.figure(figsize=(12, 6))
sns.boxplot(data=pd.DataFrame({'Points': scores}))
plt.title('Distribution of Team Scoring')
```

### 3. Win Percentage Analysis

```python
plt.figure(figsize=(10, 12))
sorted_teams = team_stats.sort_values('win_pct', ascending=True)
bars = plt.barh(sorted_teams['team'], sorted_teams['win_pct'])

# Add percentage labels
for bar in bars:
    width = bar.get_width()
    plt.text(width, bar.get_y() + bar.get_height()/2,
            f'{width:.3f}',
            ha='left', va='center')

plt.title('Team Win Percentages')
```

## Visualization Best Practices

1. **Color Usage**
   - Use colorblind-friendly palettes
   - Apply consistent color schemes across related visualizations
   - Use color to highlight important insights

2. **Layout and Formatting**
   - Set appropriate figure sizes for each plot type
   - Use clear, readable fonts and labels
   - Include titles and axis labels
   - Add legends where necessary

3. **Data Representation**
   - Choose appropriate plot types for different metrics
   - Use error bars or confidence intervals where applicable
   - Include reference lines (e.g., league averages)

4. **Interactivity**
   - Add tooltips for detailed information
   - Enable zooming for dense visualizations
   - Allow filtering and sorting of data

## Common Analysis Tasks

### 1. Team Performance Assessment

```python
def analyze_team_performance(team_name: str, team_stats: pd.DataFrame) -> None:
    """Analyze performance metrics for a specific team."""
    team_data = team_stats[team_stats['team'] == team_name].iloc[0]
    
    print(f"Performance Analysis for {team_name}")
    print(f"Offensive Rating: {team_data['offensive_rating']:.1f}")
    print(f"Defensive Rating: {team_data['defensive_rating']:.1f}")
    print(f"Net Rating: {team_data['net_rating']:.1f}")
    print(f"Win Percentage: {team_data['win_pct']:.3f}")
```

### 2. League-wide Trends

```python
def analyze_league_trends(team_stats: pd.DataFrame) -> None:
    """Analyze league-wide statistical trends."""
    print("League Averages:")
    metrics = ['offensive_rating', 'defensive_rating', 'pace']
    for metric in metrics:
        mean = team_stats[metric].mean()
        std = team_stats[metric].std()
        print(f"{metric}: {mean:.1f} ± {std:.1f}")
```

### 3. Statistical Correlations

```python
def analyze_correlations(team_stats: pd.DataFrame) -> None:
    """Analyze correlations between key metrics."""
    metrics = ['offensive_rating', 'defensive_rating', 
              'pace', 'win_pct']
    correlation_matrix = team_stats[metrics].corr()
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
    plt.title('Correlation Matrix of Key Metrics')
```

## Data Export

### Excel Export

```python
def export_analysis(data: dict, filename: str) -> None:
    """Export analysis results to Excel."""
    with pd.ExcelWriter(filename) as writer:
        for sheet_name, df in data.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
```

### Visualization Export

```python
def save_visualizations(output_dir: str = 'visualizations') -> None:
    """Save all visualizations to files."""
    Path(output_dir).mkdir(exist_ok=True)
    
    # Save each plot
    plt.savefig(f'{output_dir}/plot_name.png', 
                dpi=300, bbox_inches='tight')
```
