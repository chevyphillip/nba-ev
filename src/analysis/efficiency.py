"""
Module for calculating efficiency metrics for NBA teams and players.
"""

import numpy as np
import pandas as pd


def calculate_team_efficiency(team_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate comprehensive team efficiency metrics.
    
    Args:
        team_stats: DataFrame containing team statistics
        
    Returns:
        DataFrame with calculated efficiency metrics
    """
    efficiency = team_stats.copy()
    
    # Basic Four Factors
    if all(col in efficiency.columns for col in ['efg_pct', 'tov_pct', 'oreb_pct', 'ft_rate']):
        efficiency['four_factors_score'] = (
            0.4 * efficiency['efg_pct'] +
            0.25 * efficiency['tov_pct'] * -1 +  # Negative impact
            0.2 * efficiency['oreb_pct'] +
            0.15 * efficiency['ft_rate']
        )
    
    # Per 100 Possessions Stats
    if 'possessions' in efficiency.columns:
        stats_per_100 = [
            'points', 'assists', 'rebounds', 'steals', 'blocks', 'turnovers'
        ]
        for stat in stats_per_100:
            if stat in efficiency.columns:
                efficiency[f'{stat}_per_100'] = efficiency[stat] / efficiency['possessions'] * 100
    
    # Opponent-Adjusted Metrics
    if 'defensive_rating' in efficiency.columns:
        league_avg_drtg = efficiency['defensive_rating'].mean()
        efficiency['defense_vs_league'] = league_avg_drtg - efficiency['defensive_rating']
    
    if 'offensive_rating' in efficiency.columns:
        league_avg_ortg = efficiency['offensive_rating'].mean()
        efficiency['offense_vs_league'] = efficiency['offensive_rating'] - league_avg_ortg
    
    # Advanced Team Metrics
    if all(col in efficiency.columns for col in ['wins', 'losses', 'point_differential']):
        # Pythagorean Win Expectation
        efficiency['expected_win_pct'] = (
            efficiency['point_differential'] ** 16.5 /
            (efficiency['point_differential'] ** 16.5 + (-efficiency['point_differential']) ** 16.5)
        )
        
        # Luck Rating (actual wins vs expected wins)
        efficiency['luck_rating'] = efficiency['win_pct'] - efficiency['expected_win_pct']
    
    return efficiency

def calculate_player_efficiency(player_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate player efficiency metrics.
    
    Args:
        player_stats: DataFrame containing player statistics
        
    Returns:
        DataFrame with efficiency metrics added
    """
    efficiency = player_stats.copy()
    
    # Calculate efficiency metrics
    if 'usg%' in efficiency.columns:
        try:
            # Try to create usage tiers, handling edge cases
            efficiency['usage_tier'] = pd.qcut(
                efficiency['usg%'].fillna(efficiency['usg%'].mean()),
                q=5,
                labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
            )
        except ValueError:
            # If qcut fails, use simple thresholds
            efficiency['usage_tier'] = pd.cut(
                efficiency['usg%'].fillna(efficiency['usg%'].mean()),
                bins=5,
                labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
            )
    
    # Calculate other efficiency metrics
    if all(col in efficiency.columns for col in ['ppg_x', 'mpg_x']):
        efficiency['points_per_minute'] = efficiency['ppg_x'] / efficiency['mpg_x'].replace(0, 1)
    
    if all(col in efficiency.columns for col in ['apg_x', 'tpg_x']):
        efficiency['assist_to_turnover'] = efficiency['apg_x'] / efficiency['tpg_x'].replace(0, 1)
    
    if 'fg%' in efficiency.columns and 'ft%_x' in efficiency.columns:
        efficiency['scoring_efficiency'] = (
            efficiency['fg%'].fillna(0) + efficiency['ft%_x'].fillna(0)
        ) / 2
    
    return efficiency

def calculate_pace_factors(team_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate comprehensive pace and tempo metrics.
    
    Args:
        team_stats: DataFrame containing team statistics
        
    Returns:
        DataFrame with calculated pace metrics
    """
    pace = team_stats.copy()
    
    if 'possessions' in pace.columns:
        # Basic Pace (Possessions per 48 minutes)
        if 'minutes' in pace.columns:
            pace['pace_per_48'] = pace['possessions'] / (pace['minutes'] / 48)
        
        # Offensive Time per Possession
        if 'points' in pace.columns:
            pace['points_per_possession'] = pace['points'] / pace['possessions']
        
        # Pace Tiers
        pace['pace_tier'] = pd.qcut(
            pace['pace'], 
            q=5, 
            labels=['Very Slow', 'Slow', 'Medium', 'Fast', 'Very Fast']
        )
        
        # Relative Pace (compared to league average)
        league_avg_pace = pace['pace'].mean()
        pace['relative_pace'] = (pace['pace'] - league_avg_pace) / league_avg_pace * 100
        
        # Consistency Score (standard deviation of game-by-game pace)
        if 'game_pace' in pace.columns:
            pace['pace_consistency'] = pace.groupby('team')['game_pace'].transform('std')
    
    return pace

def calculate_matchup_adjustments(
    team_stats: pd.DataFrame,
    player_stats: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate matchup-based adjustments for player and team projections.
    
    Args:
        team_stats: DataFrame containing team statistics
        player_stats: DataFrame containing player statistics
        
    Returns:
        DataFrame with matchup adjustment factors
    """
    adjustments = pd.DataFrame()
    
    if all(col in team_stats.columns for col in ['defensive_rating', 'pace']):
        # Team Defense Factors
        league_avg_drtg = team_stats['defensive_rating'].mean()
        defense_factors = team_stats['defensive_rating'] / league_avg_drtg
        
        # Pace Factors
        league_avg_pace = team_stats['pace'].mean()
        pace_factors = team_stats['pace'] / league_avg_pace
        
        # Position-Specific Defense
        if 'position_defense_rating' in team_stats.columns:
            position_factors = team_stats.pivot(
                columns='position',
                values='position_defense_rating'
            )
            
            # Combine factors
            adjustments = pd.DataFrame({
                'team': team_stats['team'],
                'defense_factor': defense_factors,
                'pace_factor': pace_factors
            })
            
            if not position_factors.empty:
                adjustments = adjustments.join(position_factors)
    
    return adjustments 