"""
Module for cleaning and validating NBA statistics data.
"""

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataValidator:
    """Validates NBA statistics data."""
    
    REQUIRED_TEAM_COLUMNS = [
        'team', 'wins', 'losses', 'offensive_rating', 'defensive_rating',
        'pace', 'possessions', 'points', 'points_allowed'
    ]
    
    REQUIRED_PLAYER_COLUMNS = [
        'name', 'team', 'position', 'age', 'games_played', 'minutes_played',
        'points', 'rebounds', 'assists', 'steals', 'blocks', 'turnovers',
        'field_goals_attempted', 'field_goals_made', 'three_point_attempted',
        'three_point_made', 'free_throws_attempted', 'free_throws_made'
    ]
    
    VALID_POSITIONS = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'C-F', 'F-C', 'G-F', 'F-G']
    
    @staticmethod
    def validate_team_stats(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate team statistics DataFrame.
        
        Args:
            df: DataFrame containing team statistics
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required columns
        missing_cols = [col for col in DataValidator.REQUIRED_TEAM_COLUMNS 
                       if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Check for duplicates
        duplicates = df['team'].duplicated()
        if duplicates.any():
            errors.append(f"Duplicate team entries found: {df[duplicates]['team'].tolist()}")
        
        # Validate numeric ranges
        if 'win_pct' in df.columns:
            invalid_pct = df[~df['win_pct'].between(0, 1)]
            if not invalid_pct.empty:
                errors.append(f"Invalid win percentages found: {invalid_pct['team'].tolist()}")
        
        # Validate game counts
        if all(col in df.columns for col in ['wins', 'losses']):
            invalid_games = df[df['wins'] + df['losses'] > 82]
            if not invalid_games.empty:
                errors.append(f"Invalid game counts found: {invalid_games['team'].tolist()}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_player_stats(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate player statistics DataFrame.
        
        Args:
            df: DataFrame containing player statistics
            
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check required columns
        missing_cols = [col for col in DataValidator.REQUIRED_PLAYER_COLUMNS 
                       if col not in df.columns]
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['name', 'team', 'season'])
        if duplicates.any():
            errors.append(f"Duplicate player entries found: {df[duplicates]['name'].tolist()}")
        
        # Validate positions
        if 'position' in df.columns:
            invalid_pos = df[~df['position'].isin(DataValidator.VALID_POSITIONS)]
            if not invalid_pos.empty:
                errors.append(f"Invalid positions found: {invalid_pos['position'].unique().tolist()}")
        
        # Validate numeric ranges
        if 'age' in df.columns:
            invalid_age = df[~df['age'].between(18, 45)]
            if not invalid_age.empty:
                errors.append(f"Invalid ages found: {invalid_age['name'].tolist()}")
        
        return len(errors) == 0, errors

class DataCleaner:
    """Cleans NBA statistics data."""
    
    @staticmethod
    def clean_team_names(df: pd.DataFrame, team_col: str) -> pd.DataFrame:
        """
        Standardize team names across different sources.
        
        Args:
            df: DataFrame containing team names
            team_col: Name of the team column
            
        Returns:
            DataFrame with standardized team names
        """
        team_mappings = {
            'GSW': 'Golden State Warriors',
            'GS': 'Golden State Warriors',
            'GOLDEN STATE': 'Golden State Warriors',
            'LAL': 'Los Angeles Lakers',
            'LA Lakers': 'Los Angeles Lakers',
            'LAC': 'Los Angeles Clippers',
            'LA Clippers': 'Los Angeles Clippers',
            'PHX': 'Phoenix Suns',
            'PHI': 'Philadelphia 76ers',
            'BKN': 'Brooklyn Nets',
            'BRK': 'Brooklyn Nets',
            'CHA': 'Charlotte Hornets',
            'CHO': 'Charlotte Hornets',
            # Add more mappings as needed
        }
        
        df = df.copy()
        df[team_col] = df[team_col].replace(team_mappings)
        return df
    
    @staticmethod
    def clean_player_names(df: pd.DataFrame, name_col: str) -> pd.DataFrame:
        """
        Standardize player names.
        
        Args:
            df: DataFrame containing player names
            name_col: Name of the player name column
            
        Returns:
            DataFrame with standardized player names
        """
        df = df.copy()
        
        # Remove Jr., Sr., III, etc.
        df[name_col] = df[name_col].str.replace(r'\s+(Jr\.|Sr\.|I{2,}|IV)$', '', regex=True)
        
        # Remove periods from initials
        df[name_col] = df[name_col].str.replace(r'\.', '', regex=True)
        
        # Capitalize names
        df[name_col] = df[name_col].str.title()
        
        return df
    
    @staticmethod
    def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        """
        Handle missing values in the DataFrame.
        
        Args:
            df: DataFrame containing NBA statistics
            
        Returns:
            DataFrame with handled missing values
        """
        df = df.copy()
        
        # Fill missing numeric values with 0
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
        df[numeric_cols] = df[numeric_cols].fillna(0)
        
        # Fill missing categorical values with 'Unknown'
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        df[categorical_cols] = df[categorical_cols].fillna('Unknown')
        
        return df
    
    @staticmethod
    def calculate_advanced_stats(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate advanced statistics.
        
        Args:
            df: DataFrame containing basic statistics
            
        Returns:
            DataFrame with additional advanced statistics
        """
        df = df.copy()
        
        # True Shooting Percentage
        if all(col in df.columns for col in ['points', 'field_goals_attempted', 'free_throws_attempted']):
            df['true_shooting_pct'] = (
                df['points'] / 
                (2 * (df['field_goals_attempted'] + 0.44 * df['free_throws_attempted']))
            )
        
        # Effective Field Goal Percentage
        if all(col in df.columns for col in ['field_goals_made', 'three_point_made', 'field_goals_attempted']):
            df['efg_pct'] = (
                (df['field_goals_made'] + 0.5 * df['three_point_made']) / 
                df['field_goals_attempted']
            )
        
        # Assist to Turnover Ratio
        if all(col in df.columns for col in ['assists', 'turnovers']):
            df['ast_to_ratio'] = df['assists'] / df['turnovers'].replace(0, 1)
        
        return df

def prepare_data_for_visualization(
    team_stats: pd.DataFrame,
    player_stats: pd.DataFrame,
    odds_data: Optional[pd.DataFrame] = None
) -> Dict[str, pd.DataFrame]:
    """
    Clean and prepare data for visualization.
    
    Args:
        team_stats: DataFrame containing team statistics
        player_stats: DataFrame containing player statistics
        odds_data: Optional DataFrame containing odds data
        
    Returns:
        Dictionary containing cleaned DataFrames
    """
    logger.info("Starting data preparation for visualization")
    
    # Initialize data cleaner and validator
    cleaner = DataCleaner()
    validator = DataValidator()
    
    # Clean team statistics
    team_stats_clean = (
        team_stats.pipe(cleaner.clean_team_names, 'team')
        .pipe(cleaner.handle_missing_values)
    )
    
    # Validate team statistics
    is_valid, errors = validator.validate_team_stats(team_stats_clean)
    if not is_valid:
        logger.warning(f"Team statistics validation errors: {errors}")
    
    # Clean player statistics
    player_stats_clean = (
        player_stats.pipe(cleaner.clean_player_names, 'name')
        .pipe(cleaner.clean_team_names, 'team')
        .pipe(cleaner.handle_missing_values)
        .pipe(cleaner.calculate_advanced_stats)
    )
    
    # Validate player statistics
    is_valid, errors = validator.validate_player_stats(player_stats_clean)
    if not is_valid:
        logger.warning(f"Player statistics validation errors: {errors}")
    
    # Clean odds data if provided
    if odds_data is not None:
        odds_data_clean = (
            odds_data.pipe(cleaner.clean_team_names, 'home_team')
            .pipe(cleaner.clean_team_names, 'away_team')
            .pipe(cleaner.handle_missing_values)
        )
    else:
        odds_data_clean = None
    
    return {
        'team_stats': team_stats_clean,
        'player_stats': player_stats_clean,
        'odds_data': odds_data_clean
    } 