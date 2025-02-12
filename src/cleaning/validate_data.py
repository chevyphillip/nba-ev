"""
Data validation script for cleaned NBA data.
Checks for data quality issues including missing values, duplicates, and consistency.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataValidator:
    """Validator for cleaned NBA data."""
    
    def __init__(self, data_dir: Path):
        """Initialize the validator with data directory."""
        self.data_dir = data_dir
        self.validation_results = {
            'team_stats': {},
            'player_stats': {},
            'schedule': {}
        }
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Load cleaned data files."""
        team_stats = pd.read_parquet(self.data_dir / 'team_stats_cleaned.parquet')
        player_stats = pd.read_parquet(self.data_dir / 'player_stats_cleaned.parquet')
        schedule = pd.read_parquet(self.data_dir / 'schedule_cleaned.parquet')
        return team_stats, player_stats, schedule
    
    def validate_team_stats(self, df: pd.DataFrame) -> Dict:
        """Validate team statistics data."""
        results = {}
        
        # Check for missing values
        missing_values = df.isnull().sum()
        results['missing_values'] = missing_values[missing_values > 0].to_dict()
        
        # Check for duplicates
        duplicates = df.duplicated().sum()
        results['duplicate_rows'] = duplicates
        
        # Validate value ranges
        results['invalid_ranges'] = {
            'negative_games': (df['GP'] < 0).sum(),
            'invalid_win_pct': ((df['W_PCT'] < 0) | (df['W_PCT'] > 1)).sum(),
            'wins_greater_than_games': (df['W'] > df['GP']).sum(),
            'losses_greater_than_games': (df['L'] > df['GP']).sum()
        }
        
        # Check win-loss consistency
        results['inconsistent_records'] = (df['W'] + df['L'] != df['GP']).sum()
        
        # Validate team count
        results['total_teams'] = len(df)
        if results['total_teams'] != 30:  # NBA has 30 teams
            logger.warning(f"Unexpected number of teams: {results['total_teams']}")
        
        return results
    
    def validate_player_stats(self, df: pd.DataFrame) -> Dict:
        """Validate player statistics data."""
        results = {}
        
        # Check for missing values
        missing_values = df.isnull().sum()
        results['missing_values'] = missing_values[missing_values > 0].to_dict()
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['name', 'team']).sum()
        results['duplicate_players'] = duplicates
        
        # Validate value ranges
        results['invalid_ranges'] = {
            'negative_games': (df['games_played'] < 0).sum(),
            'negative_points': (df['points'] < 0).sum(),
            'negative_minutes': (df['minutes_played'] < 0).sum(),
            'invalid_fg_pct': ((df['field_goal_pct'] < 0) | (df['field_goal_pct'] > 1)).sum(),
            'invalid_3pt_pct': ((df['three_point_pct'] < 0) | (df['three_point_pct'] > 1)).sum(),
            'invalid_ft_pct': ((df['free_throw_pct'] < 0) | (df['free_throw_pct'] > 1)).sum()
        }
        
        # Check shooting statistics consistency
        results['inconsistent_stats'] = {
            'fg_attempts_less_than_made': (df['field_goals_attempted'] < df['field_goals_made']).sum(),
            '3pt_attempts_less_than_made': (df['three_points_attempted'] < df['three_points_made']).sum(),
            'ft_attempts_less_than_made': (df['free_throws_attempted'] < df['free_throws_made']).sum()
        }
        
        return results
    
    def validate_schedule(self, df: pd.DataFrame) -> Dict:
        """Validate schedule data."""
        results = {}
        
        # Check for missing values
        missing_values = df.isnull().sum()
        results['missing_values'] = missing_values[missing_values > 0].to_dict()
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['start_time', 'home_team', 'away_team']).sum()
        results['duplicate_games'] = duplicates
        
        # Validate value ranges
        results['invalid_ranges'] = {
            'negative_scores': ((df['home_team_score'] < 0) | (df['away_team_score'] < 0)).sum(),
            'unrealistic_scores': ((df['home_team_score'] > 200) | (df['away_team_score'] > 200)).sum()
        }
        
        # Check game date consistency
        df['date'] = pd.to_datetime(df['start_time']).dt.date
        results['date_issues'] = {
            'future_games': (df['date'] > pd.Timestamp.now().date()).sum(),
            'games_before_2000': (df['date'] < pd.Timestamp('2000-01-01').date()).sum()
        }
        
        # Check team matchup validity
        results['invalid_matchups'] = (df['home_team'] == df['away_team']).sum()
        
        # Verify game outcomes
        results['inconsistent_outcomes'] = {
            'score_margin_mismatch': (
                (df['score_margin'] != (df['home_team_score'] - df['away_team_score'])).sum()
            ),
            'home_win_mismatch': (
                (df['home_win'] != (df['home_team_score'] > df['away_team_score'])).sum()
            )
        }
        
        return results
    
    def validate_relationships(
        self,
        team_stats: pd.DataFrame,
        player_stats: pd.DataFrame,
        schedule: pd.DataFrame
    ) -> Dict:
        """Validate relationships between datasets."""
        results = {}
        
        # Get unique teams from each dataset
        team_names = set(team_stats['TEAM_NAME'].unique())
        player_teams = set(player_stats['team'].unique())
        schedule_teams = set(pd.concat([schedule['home_team'], schedule['away_team']]).unique())
        
        # Check team consistency across datasets
        results['team_consistency'] = {
            'teams_in_player_stats_not_in_team_stats': len(player_teams - team_names),
            'teams_in_schedule_not_in_team_stats': len(schedule_teams - team_names),
            'teams_in_team_stats_not_in_schedule': len(team_names - schedule_teams)
        }
        
        return results
    
    def run_validation(self) -> Dict:
        """Run all validation checks."""
        try:
            # Load data
            team_stats, player_stats, schedule = self.load_data()
            
            # Run validations
            self.validation_results['team_stats'] = self.validate_team_stats(team_stats)
            self.validation_results['player_stats'] = self.validate_player_stats(player_stats)
            self.validation_results['schedule'] = self.validate_schedule(schedule)
            self.validation_results['relationships'] = self.validate_relationships(
                team_stats, player_stats, schedule
            )
            
            # Log validation results
            self._log_validation_results()
            
            return self.validation_results
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            raise
    
    def _log_validation_results(self):
        """Log validation results in a readable format."""
        logger.info("\n=== Validation Results ===")
        
        # Team Stats Validation
        logger.info("\nTeam Statistics Validation:")
        team_results = self.validation_results['team_stats']
        if team_results['missing_values']:
            logger.warning(f"Missing values found: {team_results['missing_values']}")
        if team_results['duplicate_rows']:
            logger.warning(f"Found {team_results['duplicate_rows']} duplicate team entries")
        if any(team_results['invalid_ranges'].values()):
            logger.warning(f"Invalid value ranges detected: {team_results['invalid_ranges']}")
        if team_results['inconsistent_records']:
            logger.warning(f"Found {team_results['inconsistent_records']} inconsistent win-loss records")
        
        # Player Stats Validation
        logger.info("\nPlayer Statistics Validation:")
        player_results = self.validation_results['player_stats']
        if player_results['missing_values']:
            logger.warning(f"Missing values found: {player_results['missing_values']}")
        if player_results['duplicate_players']:
            logger.warning(f"Found {player_results['duplicate_players']} duplicate player entries")
        if any(player_results['invalid_ranges'].values()):
            logger.warning(f"Invalid value ranges detected: {player_results['invalid_ranges']}")
        if any(player_results['inconsistent_stats'].values()):
            logger.warning(f"Inconsistent shooting statistics found: {player_results['inconsistent_stats']}")
        
        # Schedule Validation
        logger.info("\nSchedule Validation:")
        schedule_results = self.validation_results['schedule']
        if schedule_results['missing_values']:
            logger.warning(f"Missing values found: {schedule_results['missing_values']}")
        if schedule_results['duplicate_games']:
            logger.warning(f"Found {schedule_results['duplicate_games']} duplicate game entries")
        if any(schedule_results['invalid_ranges'].values()):
            logger.warning(f"Invalid score ranges detected: {schedule_results['invalid_ranges']}")
        if schedule_results['invalid_matchups']:
            logger.warning(f"Found {schedule_results['invalid_matchups']} invalid team matchups")
        if any(schedule_results['inconsistent_outcomes'].values()):
            logger.warning(f"Inconsistent game outcomes found: {schedule_results['inconsistent_outcomes']}")
        
        # Relationship Validation
        logger.info("\nData Relationship Validation:")
        rel_results = self.validation_results['relationships']
        if any(rel_results['team_consistency'].values()):
            logger.warning(f"Team consistency issues found: {rel_results['team_consistency']}")

def main():
    """Main function to run data validation."""
    data_dir = Path("data/historical/season_2023_cleaned")
    validator = DataValidator(data_dir)
    validator.run_validation()

 