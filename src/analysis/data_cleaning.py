"""
Module for cleaning and preprocessing NBA statistics data.

This module implements best practices for sports data cleaning, including:
- Handling missing values
- Removing duplicates
- Standardizing formats
- Detecting outliers
- Validating data accuracy
- Feature engineering
"""

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from pandas.api.types import is_numeric_dtype


def clean_team_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and preprocess team statistics.
    
    Args:
        df: Raw team statistics DataFrame from either NBA API or Basketball Reference
        
    Returns:
        Cleaned DataFrame with standardized team statistics
    """
    # Create a copy to avoid modifying the original
    cleaned = df.copy()
    
    # Map NBA API column names to our standardized names
    if 'TEAM_NAME' in cleaned.columns:
        cleaned = cleaned.rename(columns={
            'TEAM_NAME': 'team',
            'W': 'wins',
            'L': 'losses',
            'W_PCT': 'win_pct',
            'OFF_RATING': 'offensive_rating',
            'DEF_RATING': 'defensive_rating',
            'NET_RATING': 'net_rating',
            'EFG_PCT': 'efg_pct',
            'TS_PCT': 'ts_pct',
            'PACE': 'pace',
            'AST_PCT': 'ast_pct',
            'AST_TO': 'ast_to',
            'AST_RATIO': 'ast_ratio',
            'POSS': 'possessions'
        })
    # Map Basketball Reference column names
    elif 'home_team' in cleaned.columns:
        # Create a team stats DataFrame from home and away games
        home_stats = cleaned[['home_team', 'home_team_score']].rename(
            columns={'home_team': 'team', 'home_team_score': 'points'})
        away_stats = cleaned[['away_team', 'away_team_score']].rename(
            columns={'away_team': 'team', 'away_team_score': 'points'})
        
        # Combine home and away stats
        cleaned = pd.concat([home_stats, away_stats])
        cleaned = cleaned.groupby('team').agg({
            'points': ['count', 'sum', 'mean']
        }).reset_index()
        cleaned.columns = ['team', 'games_played', 'total_points', 'points_per_game']
    
    # Standardize team names if the team column exists and is a Series
    if 'team' in cleaned.columns and isinstance(cleaned['team'], pd.Series):
        cleaned['team'] = cleaned['team'].str.upper()
    
    # Handle missing values for numeric columns
    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Use median for efficiency stats
        if 'rating' in col.lower() or 'pct' in col.lower():
            cleaned[col] = cleaned[col].fillna(cleaned[col].median())
        # Use mean for counting stats
        else:
            cleaned[col] = cleaned[col].fillna(cleaned[col].mean())
    
    # Remove duplicates if we have a team column
    if 'team' in cleaned.columns:
        cleaned = cleaned.drop_duplicates(subset=['team'], keep='last')
    
    # Detect and handle outliers
    for col in numeric_cols:
        cleaned[col] = handle_outliers(cleaned[col])
    
    return cleaned

def clean_player_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and preprocess player statistics.
    
    Args:
        df: Raw player statistics DataFrame
        
    Returns:
        Cleaned DataFrame with standardized player statistics
    """
    # Create a copy to avoid modifying the original
    cleaned = df.copy()
    
    # Debug: Print available columns
    print("\nAvailable columns in player stats:")
    print(cleaned.columns.tolist())
    
    # Map NBA API column names to our standardized names if they exist
    if 'PLAYER_NAME' in cleaned.columns:
        cleaned = cleaned.rename(columns={
            'PLAYER_NAME': 'name',
            'TEAM_ABBREVIATION': 'team',
            'OFF_RATING': 'offensive_rating',
            'DEF_RATING': 'defensive_rating',
            'NET_RATING': 'net_rating',
            'AST_PCT': 'ast_pct',
            'AST_TO': 'ast_to',
            'AST_RATIO': 'ast_ratio',
            'USG_PCT': 'usage_pct',
            'MIN': 'minutes_played'
        })
    
    # Standardize team names and player names if they exist
    if 'team' in cleaned.columns and isinstance(cleaned['team'], pd.Series):
        cleaned['team'] = cleaned['team'].str.upper()
    if 'name' in cleaned.columns and isinstance(cleaned['name'], pd.Series):
        cleaned['name'] = cleaned['name'].str.title()
    
    # Handle missing values
    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Use 0 for counting stats
        if any(stat in col.lower() for stat in ['points', 'rebounds', 'assists', 'steals', 'blocks']):
            cleaned[col] = cleaned[col].fillna(0)
        # Use median for efficiency stats
        elif any(stat in col.lower() for stat in ['pct', 'rating', 'efficiency']):
            cleaned[col] = cleaned[col].fillna(cleaned[col].median())
        # Use mean for other numeric stats
        else:
            cleaned[col] = cleaned[col].fillna(cleaned[col].mean())
    
    # Remove duplicates if we have both name and team columns
    if all(col in cleaned.columns for col in ['name', 'team']):
        cleaned = cleaned.drop_duplicates(subset=['name', 'team'], keep='last')
    
    # Detect and handle outliers
    for col in numeric_cols:
        cleaned[col] = handle_outliers(cleaned[col])
    
    # Calculate per-game averages if possible
    if 'games_played' in cleaned.columns:
        counting_stats = ['points', 'rebounds', 'assists', 'steals', 'blocks']
        for stat in counting_stats:
            if stat in cleaned.columns and f'{stat}_per_game' not in cleaned.columns:
                cleaned[f'{stat}_per_game'] = cleaned[stat] / cleaned['games_played']
    
    # Debug: Print columns after cleaning
    print("\nColumns after cleaning:")
    print(cleaned.columns.tolist())
    
    return cleaned

def clean_odds_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and preprocess betting odds data.
    
    Args:
        df: Raw betting odds DataFrame
        
    Returns:
        Cleaned DataFrame with standardized odds data
    """
    # Create a copy to avoid modifying the original
    cleaned = df.copy()
    
    # Standardize team names
    cleaned['home_team'] = cleaned['home_team'].str.upper()
    cleaned['away_team'] = cleaned['away_team'].str.upper()
    
    # Handle missing values
    numeric_cols = cleaned.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Use median for odds and lines
        cleaned[col] = cleaned[col].fillna(cleaned[col].median())
    
    # Remove duplicates
    cleaned = cleaned.drop_duplicates(subset=['game_id'], keep='last')
    
    # Convert odds to probabilities if not already done
    if 'home_odds' in cleaned.columns and 'home_probability' not in cleaned.columns:
        cleaned['home_probability'] = 1 / cleaned['home_odds']
        cleaned['away_probability'] = 1 / cleaned['away_odds']
        # Normalize probabilities
        total_prob = cleaned['home_probability'] + cleaned['away_probability']
        cleaned['home_probability'] = cleaned['home_probability'] / total_prob
        cleaned['away_probability'] = cleaned['away_probability'] / total_prob
    
    return cleaned

def handle_outliers(series: pd.Series, n_std: float = 3) -> pd.Series:
    """
    Handle outliers in a numeric series using the z-score method.
    
    Args:
        series: Numeric pandas Series
        n_std: Number of standard deviations to use for outlier detection
        
    Returns:
        Series with outliers handled
    """
    if not is_numeric_dtype(series):
        return series
    
    # Create a copy to avoid SettingWithCopyWarning
    series = series.copy()
    
    # Calculate z-scores
    z_scores = np.abs((series - series.mean()) / series.std())
    
    # Replace outliers with the nearest non-outlier value
    outliers = z_scores > n_std
    if outliers.any():
        series.loc[outliers] = series.loc[~outliers].median()
    
    return series

def validate_data_consistency(
    team_stats: pd.DataFrame,
    player_stats: pd.DataFrame
) -> Tuple[bool, Dict[str, str]]:
    """
    Validate consistency between team and player statistics.
    
    Args:
        team_stats: Team statistics DataFrame
        player_stats: Player statistics DataFrame
        
    Returns:
        Tuple of (is_valid, validation_messages)
    """
    validation_messages = {}
    is_valid = True
    
    # Check team names consistency
    team_names = set(team_stats['team'])
    player_team_names = set(player_stats['team'])
    
    if not player_team_names.issubset(team_names):
        is_valid = False
        unknown_teams = player_team_names - team_names
        validation_messages['team_names'] = f"Unknown teams in player stats: {unknown_teams}"
    
    # Check basic statistics consistency
    if all(col in team_stats.columns for col in ['points_for', 'games_played']):
        team_ppg = team_stats.set_index('team')['points_for']
        player_ppg = (player_stats.groupby('team')['points']
                     .sum()
                     .div(team_stats.set_index('team')['games_played']))
        
        # Allow for small differences due to rounding
        ppg_diff = np.abs(team_ppg - player_ppg)
        large_diffs = ppg_diff[ppg_diff > 1].index.tolist()
        
        if large_diffs:
            is_valid = False
            validation_messages['scoring'] = (
                f"Large scoring discrepancies for teams: {large_diffs}"
            )
    
    return is_valid, validation_messages

def prepare_data_for_visualization(
    team_stats: pd.DataFrame,
    player_stats: pd.DataFrame,
    odds_data: Optional[pd.DataFrame] = None
) -> Dict[str, pd.DataFrame]:
    """
    Prepare cleaned data for visualization.
    
    Args:
        team_stats: Team statistics DataFrame
        player_stats: Player statistics DataFrame
        odds_data: Optional betting odds DataFrame
        
    Returns:
        Dictionary of cleaned DataFrames ready for visualization
    """
    # Clean each dataset
    cleaned_team_stats = clean_team_stats(team_stats)
    cleaned_player_stats = clean_player_stats(player_stats)
    cleaned_odds = clean_odds_data(odds_data) if odds_data is not None else None
    
    # Validate data consistency
    is_valid, messages = validate_data_consistency(cleaned_team_stats, cleaned_player_stats)
    if not is_valid:
        print("Data consistency warnings:")
        for key, message in messages.items():
            print(f"- {key}: {message}")
    
    # Prepare final dictionary
    prepared_data = {
        'team_stats': cleaned_team_stats,
        'player_stats': cleaned_player_stats
    }
    
    if cleaned_odds is not None:
        prepared_data['odds_data'] = cleaned_odds
    
    return prepared_data 