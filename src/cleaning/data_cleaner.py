"""
NBA data cleaning module.
Handles cleaning and preprocessing of collected NBA data.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TeamStatsCleaner:
    """Cleaner for team statistics data."""
    
    def __init__(self):
        """Initialize the team stats cleaner."""
        self.pct_columns = ['FG_PCT', 'FG3_PCT', 'FT_PCT', 'W_PCT']
        self.numeric_columns = [
            'GP', 'W', 'L', 'MIN', 'FGM', 'FGA', 'FG3M', 'FG3A',
            'FTM', 'FTA', 'OREB', 'DREB', 'REB', 'AST', 'TOV',
            'STL', 'BLK', 'BLKA', 'PF', 'PFD', 'PTS', 'PLUS_MINUS'
        ]
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean team statistics data."""
        df = df.copy()
        
        # Convert percentage columns to proper decimals
        for col in self.pct_columns:
            if col in df.columns:
                df[col] = df[col].astype(float)
        
        # Convert numeric columns to proper types
        for col in self.numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculate advanced metrics
        df['POSS'] = self._calculate_possessions(df)
        df['OFF_RATING'] = self._calculate_offensive_rating(df)
        df['DEF_RATING'] = self._calculate_defensive_rating(df)
        df['NET_RATING'] = df['OFF_RATING'] - df['DEF_RATING']
        
        return df
    
    def _calculate_possessions(self, df: pd.DataFrame) -> pd.Series:
        """Calculate team possessions."""
        return (df['FGA'] - df['OREB'] + df['TOV'] + (0.44 * df['FTA']))
    
    def _calculate_offensive_rating(self, df: pd.DataFrame) -> pd.Series:
        """Calculate offensive rating (points per 100 possessions)."""
        return (df['PTS'] / df['POSS']) * 100
    
    def _calculate_defensive_rating(self, df: pd.DataFrame) -> pd.Series:
        """Calculate defensive rating (points allowed per 100 possessions)."""
        return (df['PLUS_MINUS'] - df['PTS']) / df['POSS'] * 100

class PlayerStatsCleaner:
    """Cleaner for player statistics data."""
    
    def __init__(self):
        """Initialize the player stats cleaner."""
        self.name_corrections = {}  # Add name corrections if needed
    
    def clean(self, nba_stats: pd.DataFrame, bref_stats: pd.DataFrame) -> pd.DataFrame:
        """Clean and merge player statistics data."""
        nba_stats = nba_stats.copy()
        bref_stats = bref_stats.copy()
        
        # Clean NBA API stats
        nba_stats = self._clean_nba_stats(nba_stats)
        
        # Clean Basketball Reference stats
        bref_stats = self._clean_bref_stats(bref_stats)
        
        # Merge datasets
        merged_stats = self._merge_player_stats(nba_stats, bref_stats)
        
        return merged_stats
    
    def _clean_nba_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean NBA API player statistics."""
        # Convert numeric columns
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Standardize player names
        df['PLAYER_NAME'] = df['PLAYER_NAME'].str.strip()
        
        return df
    
    def _clean_bref_stats(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean Basketball Reference player statistics."""
        # Convert positions list to string
        df['positions'] = df['positions'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
        
        # Convert numeric columns
        numeric_cols = [
            'age', 'games_played', 'games_started', 'minutes_played',
            'made_field_goals', 'attempted_field_goals', 'made_three_point_field_goals',
            'attempted_three_point_field_goals', 'made_free_throws',
            'attempted_free_throws', 'offensive_rebounds', 'defensive_rebounds',
            'assists', 'steals', 'blocks', 'turnovers', 'personal_fouls', 'points'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _merge_player_stats(self, nba_stats: pd.DataFrame, bref_stats: pd.DataFrame) -> pd.DataFrame:
        """Merge NBA API and Basketball Reference player statistics."""
        # Implement fuzzy matching for player names if needed
        # For now, we'll use basic name matching
        nba_stats['name_key'] = nba_stats['PLAYER_NAME'].str.lower()
        bref_stats['name_key'] = bref_stats['name'].str.lower()
        
        merged = pd.merge(
            nba_stats,
            bref_stats,
            on='name_key',
            how='outer',
            suffixes=('_nba', '_bref')
        )
        
        return merged

class ScheduleCleaner:
    """Cleaner for schedule data."""
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean schedule data."""
        df = df.copy()
        
        # Convert start_time to datetime
        df['start_time'] = pd.to_datetime(df['start_time'])
        
        # Add game ID
        df['game_id'] = self._create_game_ids(df)
        
        # Ensure score columns are numeric
        df['away_team_score'] = pd.to_numeric(df['away_team_score'], errors='coerce')
        df['home_team_score'] = pd.to_numeric(df['home_team_score'], errors='coerce')
        
        # Add derived columns
        df['total_score'] = df['away_team_score'] + df['home_team_score']
        df['score_margin'] = df['home_team_score'] - df['away_team_score']
        df['home_win'] = df['score_margin'] > 0
        
        return df
    
    def _create_game_ids(self, df: pd.DataFrame) -> pd.Series:
        """Create unique game IDs based on date and teams."""
        return df.apply(
            lambda x: f"{x['start_time'].strftime('%Y%m%d')}_{x['away_team']}_{x['home_team']}",
            axis=1
        )

class NBADataCleaner:
    """Main class for cleaning all NBA data."""
    
    def __init__(self):
        """Initialize the NBA data cleaner."""
        self.team_cleaner = TeamStatsCleaner()
        self.player_cleaner = PlayerStatsCleaner()
        self.schedule_cleaner = ScheduleCleaner()
    
    def clean_season_data(self, season_dir: Union[str, Path]) -> Dict[str, pd.DataFrame]:
        """Clean all data for a specific season."""
        season_dir = Path(season_dir)
        cleaned_data = {}
        
        try:
            # Clean team stats
            team_stats = pd.read_parquet(season_dir / 'team_stats.parquet')
            cleaned_data['team_stats'] = self.team_cleaner.clean(team_stats)
            
            # Clean player stats
            player_stats = pd.read_parquet(season_dir / 'player_stats.parquet')
            player_totals = pd.read_parquet(season_dir / 'player_totals.parquet')
            cleaned_data['player_stats'] = self.player_cleaner.clean(player_stats, player_totals)
            
            # Clean schedule
            schedule = pd.read_parquet(season_dir / 'season_schedule.parquet')
            cleaned_data['schedule'] = self.schedule_cleaner.clean(schedule)
            
            logger.info(f"Successfully cleaned data in {season_dir}")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error cleaning data in {season_dir}: {str(e)}")
            return {}
    
    def save_cleaned_data(self, cleaned_data: Dict[str, pd.DataFrame], output_dir: Union[str, Path]):
        """Save cleaned data to parquet files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for name, df in cleaned_data.items():
            file_path = output_dir / f"{name}_cleaned.parquet"
            df.to_parquet(file_path)
            logger.info(f"Saved cleaned {name} to {file_path}")

def main():
    """Main function to clean all collected data."""
    data_dir = Path("data/historical")
    cleaner = NBADataCleaner()
    
    # Clean each season's data
    for season_dir in data_dir.glob("season_*"):
        cleaned_data = cleaner.clean_season_data(season_dir)
        if cleaned_data:
            output_dir = data_dir / f"{season_dir.name}_cleaned"
            cleaner.save_cleaned_data(cleaned_data, output_dir)

if __name__ == "__main__":
    main() 