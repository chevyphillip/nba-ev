"""
Module for creating visualizations specific to NBA lineup data.
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pathlib import Path

def plot_injury_impact(injuries_df: pd.DataFrame, save_dir: str) -> None:
    """
    Create a visualization showing injury impact by team and position.
    
    Args:
        injuries_df: DataFrame containing injury data
        save_dir: Directory to save the visualization
    """
    plt.figure(figsize=(12, 8))
    
    # Count injuries by team and position
    injury_pivot = pd.crosstab(injuries_df['team'], injuries_df['position'])
    
    # Create heatmap
    sns.heatmap(injury_pivot, cmap='YlOrRd', annot=True, fmt='d', cbar_kws={'label': 'Number of Injuries'})
    
    plt.title('Team Injury Impact by Position')
    plt.xlabel('Position')
    plt.ylabel('Team')
    plt.tight_layout()
    
    # Save plot
    save_path = Path(save_dir) / 'injury_impact_heatmap.png'
    plt.savefig(save_path)
    plt.close()

def plot_lineup_stability(starting_lineups: pd.DataFrame, save_dir: str) -> None:
    """
    Create a visualization showing lineup stability for each team.
    
    Args:
        starting_lineups: DataFrame containing starting lineup data
        save_dir: Directory to save the visualization
    """
    plt.figure(figsize=(15, 8))
    
    # Calculate lineup consistency score (number of unique lineups used)
    lineup_changes = starting_lineups.nunique(axis=1)
    
    # Create bar plot
    lineup_changes.sort_values().plot(kind='bar')
    
    plt.title('Team Lineup Stability')
    plt.xlabel('Team')
    plt.ylabel('Number of Different Starting Lineups Used')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save plot
    save_path = Path(save_dir) / 'lineup_stability.png'
    plt.savefig(save_path)
    plt.close()

def plot_depth_chart_distribution(depth_charts: pd.DataFrame, save_dir: str) -> None:
    """
    Create a visualization showing depth chart distribution across positions.
    
    Args:
        depth_charts: DataFrame containing depth chart data
        save_dir: Directory to save the visualization
    """
    plt.figure(figsize=(12, 8))
    
    # Count players by position and depth level
    depth_dist = depth_charts.groupby(['position', 'depth_level']).size().unstack()
    
    # Create stacked bar plot
    depth_dist.plot(kind='bar', stacked=True)
    
    plt.title('Position Depth Distribution')
    plt.xlabel('Position')
    plt.ylabel('Number of Players')
    plt.legend(title='Depth Level')
    plt.tight_layout()
    
    # Save plot
    save_path = Path(save_dir) / 'depth_chart_distribution.png'
    plt.savefig(save_path)
    plt.close()

def plot_matchup_analysis(matchups: pd.DataFrame, team_stats: pd.DataFrame, save_dir: str) -> None:
    """
    Create a visualization comparing matchup statistics.
    
    Args:
        matchups: DataFrame containing matchup data
        team_stats: DataFrame containing team statistics
        save_dir: Directory to save the visualization
    """
    plt.figure(figsize=(15, 12))
    
    # Ensure team names match between datasets
    team_stats = team_stats.copy()
    matchups = matchups.copy()
    
    # Standardize team names if needed
    team_stats['team'] = team_stats['team'].str.upper()
    matchups['home_team'] = matchups['home_team'].str.upper()
    matchups['away_team'] = matchups['away_team'].str.upper()
    
    # Merge matchup data with team statistics
    merged_data = pd.merge(
        matchups,
        team_stats[['team', 'offensive_rating', 'defensive_rating']],
        left_on='home_team',
        right_on='team',
        suffixes=('', '_home')
    ).merge(
        team_stats[['team', 'offensive_rating', 'defensive_rating']],
        left_on='away_team',
        right_on='team',
        suffixes=('_home', '_away')
    )
    
    # Create subplot for offensive ratings comparison
    plt.subplot(2, 1, 1)
    sns.scatterplot(
        data=merged_data,
        x='offensive_rating_home',
        y='offensive_rating_away',
        s=100,
        alpha=0.6
    )
    
    # Add team labels with better positioning
    for _, row in merged_data.iterrows():
        plt.annotate(
            f"{row['home_team']} vs {row['away_team']}",
            (row['offensive_rating_home'], row['offensive_rating_away']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            alpha=0.8
        )
    
    # Add diagonal line and improve aesthetics
    min_off = min(merged_data['offensive_rating_home'].min(), 
                 merged_data['offensive_rating_away'].min())
    max_off = max(merged_data['offensive_rating_home'].max(), 
                 merged_data['offensive_rating_away'].max())
    plt.plot([min_off, max_off], [min_off, max_off], 'k--', alpha=0.3)
    
    plt.title('Offensive Ratings Comparison in Matchups', pad=20)
    plt.xlabel('Home Team Offensive Rating')
    plt.ylabel('Away Team Offensive Rating')
    plt.grid(True, alpha=0.3)
    
    # Create subplot for defensive ratings comparison
    plt.subplot(2, 1, 2)
    sns.scatterplot(
        data=merged_data,
        x='defensive_rating_home',
        y='defensive_rating_away',
        s=100,
        alpha=0.6
    )
    
    # Add team labels with better positioning
    for _, row in merged_data.iterrows():
        plt.annotate(
            f"{row['home_team']} vs {row['away_team']}",
            (row['defensive_rating_home'], row['defensive_rating_away']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=8,
            alpha=0.8
        )
    
    # Add diagonal line and improve aesthetics
    min_def = min(merged_data['defensive_rating_home'].min(), 
                 merged_data['defensive_rating_away'].min())
    max_def = max(merged_data['defensive_rating_home'].max(), 
                 merged_data['defensive_rating_away'].max())
    plt.plot([min_def, max_def], [min_def, max_def], 'k--', alpha=0.3)
    
    plt.title('Defensive Ratings Comparison in Matchups', pad=20)
    plt.xlabel('Home Team Defensive Rating')
    plt.ylabel('Away Team Defensive Rating')
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save plot with higher DPI
    save_path = Path(save_dir) / 'matchup_analysis.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_lineup_visualizations(data: dict, save_dir: str) -> None:
    """
    Create all lineup-related visualizations.
    
    Args:
        data: Dictionary containing all NBA data
        save_dir: Directory to save visualizations
    """
    # Create save directory if it doesn't exist
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    # Create each visualization
    if 'injuries' in data:
        plot_injury_impact(data['injuries'], save_dir)
    
    if 'starting_lineups' in data:
        plot_lineup_stability(data['starting_lineups'], save_dir)
    
    if 'depth_charts' in data:
        plot_depth_chart_distribution(data['depth_charts'], save_dir)
    
    if all(key in data for key in ['matchups', 'team_stats']):
        plot_matchup_analysis(data['matchups'], data['team_stats'], save_dir) 