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
    Calculate comprehensive player efficiency metrics.
    
    Args:
        player_stats: DataFrame containing player statistics
        
    Returns:
        DataFrame with calculated efficiency metrics
    """
    efficiency = player_stats.copy()
    
    # Per 36 Minutes Stats
    if 'mpg_x' in efficiency.columns:
        stats_per_36 = [
            'ppg_x', 'apg_x', 'rpg', 'spg_x', 'bpg_x', 'tpg_x'
        ]
        for stat in stats_per_36:
            if stat in efficiency.columns:
                efficiency[f'{stat}_per_36'] = efficiency[stat] * (36 / efficiency['mpg_x'])
    
    # Usage Rate Tiers
    if 'usg%' in efficiency.columns:
        efficiency['usage_tier'] = pd.qcut(
            efficiency['usg%'], 
            q=5, 
            labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
        )
    
    # Scoring Efficiency
    if all(col in efficiency.columns for col in ['ppg_x', 'fga', 'fta']):
        # Points per Shot Attempt
        efficiency['points_per_shot'] = efficiency['ppg_x'] / (efficiency['fga'] + 0.44 * efficiency['fta'])
        
        # True Shooting Attempts
        efficiency['true_shooting_attempts'] = efficiency['fga'] + 0.44 * efficiency['fta']
    
    # Creation Metrics
    if all(col in efficiency.columns for col in ['apg_x', 'tpg_x']):
        # Assist to Turnover Ratio
        efficiency['ast_to_ratio'] = efficiency['apg_x'] / efficiency['tpg_x'].replace(0, 1)
        
        # Playmaking Score
        efficiency['playmaking_score'] = (
            efficiency['apg_x'] * 2.0 - 
            efficiency['tpg_x'] * 1.5
        )
    
    # Versatility Score
    key_stats = ['ppg_x', 'rpg', 'apg_x', 'spg_x', 'bpg_x']
    if all(stat in efficiency.columns for stat in key_stats):
        # Normalize each stat
        normalized_stats = {}
        for stat in key_stats:
            normalized_stats[stat] = (
                efficiency[stat] - efficiency[stat].min()
            ) / (efficiency[stat].max() - efficiency[stat].min())
        
        # Calculate versatility score
        efficiency['versatility_score'] = sum(normalized_stats.values()) / len(normalized_stats)
    
    # Floor Spacing
    if all(col in efficiency.columns for col in ['3p%_x', '3pa']):
        efficiency['spacing_impact'] = efficiency['3p%_x'] * efficiency['3pa']
    
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