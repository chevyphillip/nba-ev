# NBA-EV Visualization Guide

## Overview

The NBA-EV project provides comprehensive visualization capabilities through both static and interactive plots. This guide covers the available visualization types, their implementation, and best practices for creating effective visual analytics.

## Visualization Types

### 1. Team Analysis Visualizations

#### Static Plots (Matplotlib/Seaborn)

1. **Offensive vs Defensive Ratings** (`offensive_defensive_ratings.png`):

   ```python
   def create_offensive_defensive_plot(team_stats: pd.DataFrame, output_dir: str):
       plt.figure(figsize=(12, 8))
       plt.scatter(team_stats['offensive_rating'], team_stats['defensive_rating'])
       plt.xlabel('Offensive Rating')
       plt.ylabel('Defensive Rating')
   ```

2. **Team Pace Factors** (`team_pace_factors.png`):

   ```python
   def create_pace_analysis(pace_factors: pd.DataFrame, output_dir: str):
       sns.barplot(data=pace_factors, x='team', y='pace')
       plt.title('Team Pace Factors')
   ```

#### Interactive Plots (Plotly)

1. **Team Comparison Plot**:

   ```python
   def create_team_comparison(team_stats: pd.DataFrame):
       return px.scatter(
           team_stats,
           x='offensive_rating',
           y='defensive_rating',
           color='win_pct',
           size='possessions',
           hover_data=['team', 'win_pct', 'net_rating']
       )
   ```

2. **Win Percentage Analysis**:

   ```python
   def create_win_pct_plot(team_stats: pd.DataFrame):
       return px.bar(
           team_stats.sort_values('win_pct', ascending=False),
           x='team',
           y='win_pct',
           color='net_rating'
       )
   ```

### 2. Player Analysis Visualizations

#### Static Plots

1. **Player Distribution Plots** (`player_stat_distributions.png`):

   ```python
   def create_player_distribution_plots(player_stats: pd.DataFrame, output_dir: str):
       fig, axes = plt.subplots(2, 2, figsize=(20, 16))
       for idx, stat in enumerate(['ppg_x', 'apg_x', 'rpg', 'TS_PCT']):
           sns.violinplot(y=player_stats[stat], ax=axes[idx//2, idx%2])
   ```

2. **Player Correlation Heatmap** (`player_correlation_heatmap.png`):

   ```python
   def create_player_contribution_heatmap(player_stats: pd.DataFrame, output_dir: str):
       corr_matrix = player_stats[stat_columns].corr()
       sns.heatmap(corr_matrix, annot=True, cmap='RdBu')
   ```

#### Interactive Plots

1. **Player Distribution Analysis**:

   ```python
   def create_player_distribution(player_stats: pd.DataFrame, stat_column: str):
       return go.Figure([
           go.Violin(y=player_stats[stat_column], box_visible=True),
           go.Scatter(
               x=[0] * len(top_players),
               y=top_players[stat_column],
               mode='markers+text',
               text=top_players['name']
           )
       ])
   ```

### 3. Matchup Analysis Visualizations

#### Static Plots

1. **Matchup Analysis Plot** (`matchup_analysis.png`):

   ```python
   def plot_matchup_analysis(matchups: pd.DataFrame, team_stats: pd.DataFrame):
       plt.figure(figsize=(15, 12))
       sns.scatterplot(
           data=merged_data,
           x='offensive_rating_home',
           y='offensive_rating_away'
       )
   ```

#### Interactive Plots

1. **Matchup Comparison**:

   ```python
   def create_matchup_analysis(matchups: pd.DataFrame, team_stats: pd.DataFrame):
       return px.scatter(
           merged_data,
           x='offensive_rating_home',
           y='offensive_rating_away',
           hover_data=['home_team', 'away_team']
       )
   ```

## Interactive Dashboard

### Streamlit Integration

The dashboard is built using Streamlit and provides interactive features:

1. **Filters**:

   ```python
   # Date selection
   date = st.sidebar.date_input("Select Date")
   
   # Team selection
   selected_teams = st.sidebar.multiselect(
       "Select Teams",
       options=sorted(team_stats['team'].unique())
   )
   
   # Minutes filter
   min_minutes = st.sidebar.slider("Minimum Minutes Played", 0, 48, 15)
   ```

2. **Interactive Plots**:

   ```python
   # Team comparison plot
   st.plotly_chart(
       create_team_comparison(filtered_team_stats),
       use_container_width=True
   )
   
   # Player distribution plot
   st.plotly_chart(
       create_player_distribution(
           filtered_player_stats,
           selected_stat,
           stat_name
       ),
       use_container_width=True
   )
   ```

## Best Practices

### 1. Plot Styling

```python
def setup_plotting_style():
    """Configure consistent plot styling."""
    plt.style.use('default')
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = [12, 8]
    plt.rcParams['font.size'] = 10
```

### 2. Color Schemes

- Use colorblind-friendly palettes
- Consistent color mapping across plots
- Clear contrast for important data points

### 3. Interactive Features

- Informative hover tooltips
- Zoom and pan capabilities
- Dynamic filtering options
- Linked views where appropriate

### 4. Performance Optimization

- Cache computed data
- Optimize plot rendering
- Use efficient data structures
- Implement lazy loading

### 5. Accessibility

- Clear labels and titles
- Adequate font sizes
- Alternative text descriptions
- Keyboard navigation support

## File Organization

```
src/
├── visualization/
│   ├── plots.py           # Static visualization functions
│   └── lineup_plots.py    # Lineup-specific visualizations
├── frontend/
│   └── app.py            # Streamlit dashboard
└── analysis/
    └── efficiency.py     # Metric calculations
```

## Output Directory Structure

```
visualizations/
├── offensive_defensive_ratings.png
├── team_pace_factors.png
├── player_stat_distributions.png
├── player_correlation_heatmap.png
├── matchup_analysis.png
└── ...
```

## Future Enhancements

1. **Advanced Visualizations**:
   - Shot charts
   - Court diagrams
   - Player movement tracking
   - Real-time updates

2. **Interactive Features**:
   - Custom stat comparisons
   - Advanced filtering
   - Drill-down capabilities
   - Export options

3. **Performance**:
   - Data caching
   - Plot optimization
   - Lazy loading
   - Progressive rendering

4. **Integration**:
   - API endpoints
   - Embedding options
   - Mobile responsiveness
   - Theme customization
