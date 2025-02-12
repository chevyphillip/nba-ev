"""
Module for creating NBA statistics visualizations.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from src.visualization.lineup_plots import create_lineup_visualizations


def setup_plotting_style():
    """Configure the plotting style for consistent visualizations."""
    plt.style.use('default')
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = [12, 8]
    plt.rcParams['font.size'] = 10

def create_offensive_defensive_plot(team_stats: pd.DataFrame, output_dir: str) -> None:
    """
    Create scatter plot of offensive vs defensive ratings.
    
    Args:
        team_stats: DataFrame containing team statistics
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(12, 8))
    
    # Create scatter plot
    plt.scatter(team_stats['offensive_rating'], team_stats['defensive_rating'], alpha=0.6)
    
    # Add team labels
    for i, txt in enumerate(team_stats['team']):
        plt.annotate(str(txt), (team_stats['offensive_rating'].iloc[i], team_stats['defensive_rating'].iloc[i]))
    
    # Add median lines
    plt.axvline(team_stats['offensive_rating'].median(), color='gray', linestyle='--', alpha=0.3)
    plt.axhline(team_stats['defensive_rating'].median(), color='gray', linestyle='--', alpha=0.3)
    
    plt.xlabel('Offensive Rating')
    plt.ylabel('Defensive Rating')
    plt.title('Team Offensive vs Defensive Ratings')
    
    plt.savefig(Path(output_dir) / 'offensive_defensive_ratings.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_pace_analysis(pace_factors: pd.DataFrame, output_dir: str) -> None:
    """
    Create bar plot of team pace factors.
    
    Args:
        pace_factors: DataFrame containing team pace statistics
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(15, 6))
    
    # Create bar plot
    sns.barplot(data=pace_factors.sort_values('pace', ascending=False),
                x='team', y='pace')
    
    plt.xticks(rotation=45, ha='right')
    plt.title('Team Pace Factors')
    plt.xlabel('Team')
    plt.ylabel('Pace')
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'team_pace_factors.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_win_percentage_plot(team_stats: pd.DataFrame, output_dir: str) -> None:
    """
    Create horizontal bar plot of team win percentages.
    
    Args:
        team_stats: DataFrame containing team statistics
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(10, 12))
    
    # Sort teams by win percentage
    sorted_teams = team_stats.sort_values('win_pct', ascending=True)
    
    # Create horizontal bar plot
    bars = plt.barh(sorted_teams['team'].astype(str), sorted_teams['win_pct'])
    
    # Add percentage labels
    for bar in bars:
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2,
                f'{width:.3f}', 
                ha='left', va='center', fontweight='bold')
    
    plt.title('Team Win Percentages')
    plt.xlabel('Win Percentage')
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'team_win_percentages.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_scoring_distribution(team_stats: pd.DataFrame, output_dir: str) -> None:
    """
    Create box plot of points scored and allowed.
    
    Args:
        team_stats: DataFrame containing team statistics
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(12, 6))
    
    # Prepare data for box plot
    if 'points_per_game' in team_stats.columns:
        scoring_data = pd.DataFrame({
            'Points Per Game': team_stats['points_per_game']
        })
    elif 'home_team_score' in team_stats.columns:
        # Combine home and away scores
        scores = pd.concat([
            team_stats['home_team_score'],
            team_stats['away_team_score']
        ])
        scoring_data = pd.DataFrame({
            'Points Per Game': scores
        })
    else:
        print("Warning: No scoring data available for visualization")
        return
    
    # Create box plot
    sns.boxplot(data=scoring_data)
    
    plt.title('Distribution of Team Scoring')
    plt.ylabel('Points per Game')
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'scoring_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_net_rating_plot(team_stats: pd.DataFrame, output_dir: str) -> None:
    """
    Create horizontal bar plot of team net ratings.
    
    Args:
        team_stats: DataFrame containing team statistics
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(10, 12))
    
    # Sort teams by net rating
    sorted_teams = team_stats.sort_values('net_rating', ascending=True)
    
    # Create horizontal bar plot with color coding
    bars = plt.barh(sorted_teams['team'].astype(str), sorted_teams['net_rating'])
    
    # Color bars based on positive/negative values
    for bar in bars:
        if bar.get_width() < 0:
            bar.set_color('red')
        else:
            bar.set_color('green')
    
    plt.title('Team Net Ratings')
    plt.xlabel('Net Rating (Points per 100 Possessions)')
    
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.2)
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'team_net_ratings.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_player_distribution_plots(player_stats: pd.DataFrame, output_dir: str) -> None:
    """
    Create distribution plots for key player statistics.
    
    Args:
        player_stats: DataFrame containing player statistics
        output_dir: Directory to save the plot
    """
    # Select key statistics for distribution analysis
    key_stats = ['ppg_x', 'apg_x', 'rpg', 'TS_PCT']
    stat_labels = ['Points Per Game', 'Assists Per Game', 'Rebounds Per Game', 'True Shooting %']
    
    # Set up the figure with a larger size and better spacing
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    axes = axes.flatten()
    
    # Set style for better readability
    plt.style.use('seaborn')
    
    for idx, (stat, label) in enumerate(zip(key_stats, stat_labels)):
        # Filter out players with minimal playing time
        min_minutes = 10
        filtered_stats = player_stats[player_stats['mpg_x'] >= min_minutes].copy()
        
        # Create violin plot with improved styling
        sns.violinplot(y=filtered_stats[stat], ax=axes[idx], color='lightblue', alpha=0.6)
        
        # Add individual points for top players
        threshold = filtered_stats[stat].quantile(0.9)
        top_players = filtered_stats[filtered_stats[stat] >= threshold]
        
        # Sort top players by stat value for better labeling
        top_players = top_players.nlargest(10, stat)
        
        axes[idx].scatter(
            x=np.zeros_like(top_players[stat]),
            y=top_players[stat],
            color='red',
            alpha=0.8,
            s=100
        )
        
        # Add labels for top players with better positioning
        for _, player in top_players.iterrows():
            axes[idx].annotate(
                player['name'],
                xy=(0, player[stat]),
                xytext=(10, 0),
                textcoords='offset points',
                fontsize=10,
                alpha=0.8,
                bbox=dict(facecolor='white', edgecolor='none', alpha=0.7)
            )
        
        axes[idx].set_title(f'Distribution of {label}', fontsize=14, pad=20)
        axes[idx].grid(True, alpha=0.3)
        axes[idx].set_ylabel(label, fontsize=12)
    
    plt.tight_layout(pad=3.0)
    plt.savefig(Path(output_dir) / 'player_stat_distributions.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_player_scoring_efficiency(player_stats: pd.DataFrame, output_dir: str) -> None:
    """
    Create scatter plot of points per game vs true shooting percentage.
    
    Args:
        player_stats: DataFrame containing player statistics
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(15, 10))
    
    # Filter for players with minimum minutes played
    min_minutes = 15
    qualified_players = player_stats[player_stats['mpg_x'] >= min_minutes].copy()
    
    # Create scatter plot with better styling
    plt.scatter(
        qualified_players['ppg_x'],
        qualified_players['TS_PCT'],
        alpha=0.6,
        s=100,
        c=qualified_players['mpg_x'],
        cmap='viridis'
    )
    
    # Add colorbar for minutes played
    plt.colorbar(label='Minutes Per Game')
    
    # Label top scorers and efficient players
    top_scorers = qualified_players.nlargest(10, 'ppg_x')
    efficient_scorers = qualified_players[
        (qualified_players['ppg_x'] >= 15) & 
        (qualified_players['TS_PCT'] >= qualified_players['TS_PCT'].quantile(0.9))
    ]
    
    players_to_label = pd.concat([top_scorers, efficient_scorers]).drop_duplicates()
    
    for _, player in players_to_label.iterrows():
        plt.annotate(
            player['name'],
            (player['ppg_x'], player['TS_PCT']),
            xytext=(5, 5),
            textcoords='offset points',
            fontsize=10,
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.7)
        )
    
    plt.xlabel('Points Per Game', fontsize=12)
    plt.ylabel('True Shooting Percentage', fontsize=12)
    plt.title('Scoring Efficiency by Player', fontsize=14, pad=20)
    
    # Add quadrant lines at median values
    plt.axvline(qualified_players['ppg_x'].median(), color='gray', linestyle='--', alpha=0.3)
    plt.axhline(qualified_players['TS_PCT'].median(), color='gray', linestyle='--', alpha=0.3)
    
    plt.grid(True, alpha=0.3)
    plt.savefig(Path(output_dir) / 'player_scoring_efficiency.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_player_contribution_heatmap(player_stats: pd.DataFrame, output_dir: str) -> None:
    """
    Create heatmap of correlations between player statistics.
    
    Args:
        player_stats: DataFrame containing player statistics
        output_dir: Directory to save the plot
    """
    plt.figure(figsize=(15, 12))
    
    # Select relevant columns and create readable labels
    stat_columns = [
        'ppg_x', 'apg_x', 'rpg', 'spg_x', 'bpg_x', 'tpg_x',
        'mpg_x', 'fg%', '3p%_x', 'ft%_x', 'TS_PCT', 'usg%'
    ]
    
    stat_labels = [
        'Points', 'Assists', 'Rebounds', 'Steals', 'Blocks', 'Turnovers',
        'Minutes', 'FG%', '3P%', 'FT%', 'TS%', 'Usage%'
    ]
    
    # Calculate correlation matrix for selected columns
    corr_matrix = player_stats[stat_columns].corr()
    
    # Create heatmap with improved styling
    sns.heatmap(
        corr_matrix,
        annot=True,
        cmap='RdBu',
        center=0,
        fmt='.2f',
        square=True,
        cbar_kws={'label': 'Correlation Coefficient'},
        xticklabels=stat_labels,
        yticklabels=stat_labels,
        annot_kws={'size': 8}
    )
    
    plt.title('Correlation of Player Statistics', fontsize=14, pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'player_correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_player_versatility_plot(player_stats: pd.DataFrame, output_dir: str) -> None:
    """
    Create radar charts for most versatile players.
    
    Args:
        player_stats: DataFrame containing player statistics
        output_dir: Directory to save the plot
    """
    # Create a copy of the DataFrame to avoid modifying the original
    stats_df = player_stats.copy()
    
    # Calculate versatility index using vectorized operations
    versatility_components = pd.DataFrame({
        'scoring': stats_df['ppg_x'] * 1.0,
        'rebounding': stats_df['rpg'] * 1.2,
        'playmaking': stats_df['apg_x'] * 1.5,
        'defense': (stats_df['spg_x'] + stats_df['bpg_x']) * 2.0,
        'turnovers': stats_df['tpg_x'] * -1.0
    })
    
    # Calculate versatility index in a single operation
    stats_df['versatility_index'] = (
        versatility_components.sum(axis=1) / stats_df['mpg_x']
    )
    
    # Select top 5 players by versatility index
    top_versatile = stats_df.nlargest(5, 'versatility_index')
    
    # Categories for radar chart
    categories = ['Scoring', 'Playmaking', 'Rebounding', 'Defense', 'Efficiency']
    
    # Create figure with subplots for each player
    fig, axes = plt.subplots(2, 3, figsize=(20, 12), subplot_kw=dict(projection='polar'))
    axes = axes.flatten()
    
    for idx, (_, player) in enumerate(top_versatile.iterrows()):
        # Normalize stats for radar chart using vectorized operations
        stats = np.array([
            player['ppg_x'] / stats_df['ppg_x'].max(),
            player['apg_x'] / stats_df['apg_x'].max(),
            player['rpg'] / stats_df['rpg'].max(),
            (player['spg_x'] + player['bpg_x']) / 
            (stats_df['spg_x'] + stats_df['bpg_x']).max(),
            player['TS_PCT'] / stats_df['TS_PCT'].max()
        ])
        
        # Number of variables
        num_vars = len(categories)
        
        # Compute angle for each axis
        angles = [n / float(num_vars) * 2 * np.pi for n in range(num_vars)]
        angles += angles[:1]
        
        # Plot data
        ax = axes[idx]
        ax.plot(angles, np.concatenate([stats, [stats[0]]]))
        ax.fill(angles, np.concatenate([stats, [stats[0]]]), alpha=0.25)
        
        # Set labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories)
        ax.set_title(f"{player['name']}\nVersatility Index: {player['versatility_index']:.2f}")
    
    # Remove empty subplots
    for idx in range(len(top_versatile), len(axes)):
        fig.delaxes(axes[idx])
    
    plt.tight_layout()
    plt.savefig(Path(output_dir) / 'player_versatility_radar.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_team_visualizations(data: dict, save_dir: str) -> None:
    """
    Create team-related visualizations.
    
    Args:
        data: Dictionary containing NBA data
        save_dir: Directory to save visualizations
    """
    # Create save directory if it doesn't exist
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    if 'team_stats' in data:
        # Team Net Ratings
        plt.figure(figsize=(12, 8))
        sns.scatterplot(
            data=data['team_stats'],
            x='offensive_rating',
            y='defensive_rating',
            hue='win_pct'
        )
        plt.title('Team Net Ratings')
        plt.xlabel('Offensive Rating')
        plt.ylabel('Defensive Rating')
        plt.savefig(Path(save_dir) / 'team_net_ratings.png')
        plt.close()
        
        # Win Percentages
        plt.figure(figsize=(15, 8))
        data['team_stats'].sort_values('win_pct', ascending=False)['win_pct'].plot(kind='bar')
        plt.title('Team Win Percentages')
        plt.xlabel('Team')
        plt.ylabel('Win Percentage')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(Path(save_dir) / 'team_win_percentages.png')
        plt.close()

def create_player_visualizations(data: dict, save_dir: str) -> None:
    """
    Create player-related visualizations.
    
    Args:
        data: Dictionary containing NBA data
        save_dir: Directory to save visualizations
    """
    # Create save directory if it doesn't exist
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    if 'player_stats' in data:
        # Scoring Distribution
        plt.figure(figsize=(10, 6))
        sns.histplot(data=data['player_stats'], x='ppg_x', bins=30)
        plt.title('Scoring Distribution')
        plt.xlabel('Points Per Game')
        plt.ylabel('Count')
        plt.savefig(Path(save_dir) / 'scoring_distribution.png')
        plt.close()
        
        # Player Correlation Heatmap
        plt.figure(figsize=(12, 10))
        numeric_cols = data['player_stats'].select_dtypes(include=['float64', 'int64']).columns
        sns.heatmap(
            data['player_stats'][numeric_cols].corr(),
            annot=True,
            cmap='coolwarm',
            center=0
        )
        plt.title('Player Statistics Correlation Heatmap')
        plt.tight_layout()
        plt.savefig(Path(save_dir) / 'player_correlation_heatmap.png')
        plt.close()

def create_efficiency_visualizations(data: dict, save_dir: str) -> None:
    """
    Create efficiency-related visualizations.
    
    Args:
        data: Dictionary containing NBA data
        save_dir: Directory to save visualizations
    """
    # Create save directory if it doesn't exist
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    if 'team_efficiency' in data:
        # Offensive vs Defensive Ratings
        plt.figure(figsize=(12, 8))
        sns.scatterplot(
            data=data['team_efficiency'],
            x='offensive_rating',
            y='defensive_rating',
            hue='win_pct'
        )
        plt.title('Team Efficiency: Offense vs Defense')
        plt.xlabel('Offensive Rating')
        plt.ylabel('Defensive Rating')
        plt.savefig(Path(save_dir) / 'offensive_defensive_ratings.png')
        plt.close()
    
    if 'pace_factors' in data:
        # Team Pace Factors
        plt.figure(figsize=(15, 8))
        if 'relative_pace' in data['pace_factors'].columns:
            data['pace_factors'].sort_values('relative_pace', ascending=False)['relative_pace'].plot(kind='bar')
            ylabel = 'Relative Pace (%)'
        else:
            data['pace_factors'].sort_values('pace', ascending=False)['pace'].plot(kind='bar')
            ylabel = 'Pace'
            
        plt.title('Team Pace Factors')
        plt.xlabel('Team')
        plt.ylabel(ylabel)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(Path(save_dir) / 'team_pace_factors.png')
        plt.close()

def create_all_visualizations(data: dict, save_dir: str) -> None:
    """
    Create all visualizations.
    
    Args:
        data: Dictionary containing all NBA data
        save_dir: Directory to save visualizations
    """
    # Create save directory if it doesn't exist
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    
    # Create visualizations by category
    create_team_visualizations(data, save_dir)
    create_player_visualizations(data, save_dir)
    create_efficiency_visualizations(data, save_dir)
    create_lineup_visualizations(data, save_dir) 