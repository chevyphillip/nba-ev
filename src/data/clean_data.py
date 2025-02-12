"""
Module for cleaning and preprocessing NBA statistics data.
"""

from typing import Tuple

import numpy as np
import pandas as pd


def clean_player_stats(player_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and preprocess player statistics.
    
    Args:
        player_stats: Raw player statistics DataFrame
        
    Returns:
        Cleaned player statistics DataFrame
    """
    # Make a copy to avoid modifying the original
    df = player_stats.copy()
    
    # Convert percentages to floats (0-1 range)
    percentage_cols = ['usg%', 'ft%', '2p%', '3p%']
    for col in percentage_cols:
        if col in df.columns:
            df[col] = df[col].astype(float) / 100
    
    # Handle missing values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Fill missing values with 0 for counting stats
        if col in ['gp', 'mpg', 'ppg', 'rpg', 'apg', 'spg', 'bpg', 'tpg']:
            df[col] = df[col].fillna(0)
        # Fill missing values with median for rate stats
        else:
            df[col] = df[col].fillna(df[col].median())
    
    # Remove rows with missing team information
    df = df.dropna(subset=['team'])
    
    # Ensure all text columns are strings
    text_cols = ['name', 'team', 'pos']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)
    
    # Calculate additional metrics if needed
    if 'vi' not in df.columns and all(col in df.columns for col in ['ppg', 'rpg', 'apg', 'spg', 'bpg', 'tpg', 'mpg']):
        df['vi'] = (
            (df['ppg'] * 1.0) +
            (df['rpg'] * 1.2) +
            (df['apg'] * 1.5) +
            (df['spg'] * 2.0) +
            (df['bpg'] * 2.0) -
            (df['tpg'] * 1.0)
        ) / df['mpg']
    
    return df


def clean_team_stats(team_stats: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and preprocess team statistics.
    
    Args:
        team_stats: Raw team statistics DataFrame
        
    Returns:
        Cleaned team statistics DataFrame
    """
    # Make a copy to avoid modifying the original
    df = team_stats.copy()
    
    # Convert percentages to floats (0-1 range)
    percentage_cols = ['FG_PCT', 'FG3_PCT', 'FT_PCT']
    for col in percentage_cols:
        if col in df.columns:
            df[col] = df[col].astype(float) / 100
    
    # Handle missing values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].median())
    
    # Ensure team names are standardized
    if 'TEAM_NAME' in df.columns:
        df['team'] = df['TEAM_NAME'].str.upper()
    
    return df


def merge_player_positions(
    player_stats: pd.DataFrame,
    positions: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge player statistics with position information.
    
    Args:
        player_stats: Cleaned player statistics DataFrame
        positions: Player positions DataFrame
        
    Returns:
        Merged DataFrame with position information
    """
    return pd.merge(
        player_stats,
        positions[['PLAYER_ID', 'pos']],
        on='PLAYER_ID',
        how='left'
    )


def validate_data(
    player_stats: pd.DataFrame,
    team_stats: pd.DataFrame
) -> Tuple[bool, str]:
    """
    Validate the cleaned data for consistency.
    
    Args:
        player_stats: Cleaned player statistics DataFrame
        team_stats: Cleaned team statistics DataFrame
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    is_valid = True
    error_message = ""
    
    # Check for required columns
    required_player_cols = ['name', 'team', 'pos', 'gp', 'mpg', 'ppg']
    required_team_cols = ['team', 'W', 'L']
    
    missing_player_cols = [col for col in required_player_cols if col not in player_stats.columns]
    missing_team_cols = [col for col in required_team_cols if col not in team_stats.columns]
    
    if missing_player_cols:
        is_valid = False
        error_message += f"Missing required player columns: {missing_player_cols}\n"
    
    if missing_team_cols:
        is_valid = False
        error_message += f"Missing required team columns: {missing_team_cols}\n"
    
    # Check for data consistency
    if is_valid:
        # Verify all players have valid teams
        player_teams = set(player_stats['team'].unique())
        team_names = set(team_stats['team'].unique())
        invalid_teams = player_teams - team_names
        
        if invalid_teams:
            is_valid = False
            error_message += f"Players found with invalid teams: {invalid_teams}\n"
    
    return is_valid, error_message.strip()


def process_data(
    player_stats: pd.DataFrame,
    team_stats: pd.DataFrame,
    positions: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process and clean all NBA statistics data.
    
    Args:
        player_stats: Raw player statistics DataFrame
        team_stats: Raw team statistics DataFrame
        positions: Player positions DataFrame
        
    Returns:
        Tuple of (cleaned_player_stats, cleaned_team_stats)
    """
    # Clean individual datasets
    cleaned_players = clean_player_stats(player_stats)
    cleaned_teams = clean_team_stats(team_stats)
    
    # Merge player positions
    cleaned_players = merge_player_positions(cleaned_players, positions)
    
    # Validate the cleaned data
    is_valid, error_message = validate_data(cleaned_players, cleaned_teams)
    if not is_valid:
        raise ValueError(f"Data validation failed:\n{error_message}")
    
    return cleaned_players, cleaned_teams 