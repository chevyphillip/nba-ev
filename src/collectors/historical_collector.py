"""
Module for collecting historical NBA statistics.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashteamstats
from nba_api.stats.static import teams
from tqdm import tqdm

from src.data.database import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HistoricalDataCollector:
    """Collects historical NBA statistics."""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the collector.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.seasons = range(2012, 2025)  # 2011-12 to 2024-25 seasons
    
    async def collect_all_historical_data(self):
        """Collect all historical data for configured seasons."""
        logger.info("Starting historical data collection")
        
        for season in tqdm(self.seasons, desc="Collecting seasons"):
            season_str = f"{season-1}-{str(season)[2:]}"
            
            try:
                # Collect and store team statistics
                team_stats = await self._get_team_stats(season_str)
                if not team_stats.empty:
                    self.db_manager.store_team_stats(team_stats, season)
                
                # Collect and store player statistics
                player_stats = await self._get_player_stats(season_str)
                if not player_stats.empty:
                    self.db_manager.store_player_stats(player_stats, season)
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting data for season {season_str}: {e}")
                continue
        
        logger.info("Historical data collection completed")
    
    async def _get_team_stats(self, season: str) -> pd.DataFrame:
        """
        Collect team statistics for a season.
        
        Args:
            season: Season string (e.g., '2023-24')
            
        Returns:
            DataFrame containing team statistics
        """
        logger.info(f"Collecting team statistics for season {season}")
        
        try:
            # Regular season team stats
            regular_stats = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                measure_type_detailed_defense='Advanced',
                per_mode_detailed='PerGame',
                season_type_all_star='Regular Season'
            )
            
            # Additional advanced stats
            advanced_stats = leaguedashteamstats.LeagueDashTeamStats(
                season=season,
                measure_type_detailed_defense='Advanced',
                per_mode_detailed='PerGame',
                season_type_all_star='Regular Season'
            )
            
            regular_df = pd.DataFrame(regular_stats.get_data_frames()[0])
            advanced_df = pd.DataFrame(advanced_stats.get_data_frames()[0])
            
            # Merge statistics
            team_stats = pd.merge(
                regular_df,
                advanced_df,
                on='TEAM_ID',
                suffixes=('', '_advanced')
            )
            
            # Clean and rename columns
            team_stats = team_stats.rename(columns={
                'TEAM_NAME': 'team',
                'W': 'wins',
                'L': 'losses',
                'OFF_RATING': 'offensive_rating',
                'DEF_RATING': 'defensive_rating',
                'NET_RATING': 'net_rating',
                'PACE': 'pace'
            })
            
            return team_stats
            
        except Exception as e:
            logger.error(f"Error collecting team stats for season {season}: {e}")
            return pd.DataFrame()
    
    async def _get_player_stats(self, season: str) -> pd.DataFrame:
        """
        Collect player statistics for a season.
        
        Args:
            season: Season string (e.g., '2023-24')
            
        Returns:
            DataFrame containing player statistics
        """
        logger.info(f"Collecting player statistics for season {season}")
        
        try:
            # Regular season player stats
            regular_stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                measure_type_detailed_defense='Base',
                per_mode_detailed='PerGame',
                season_type_all_star='Regular Season'
            )
            
            # Advanced stats
            advanced_stats = leaguedashplayerstats.LeagueDashPlayerStats(
                season=season,
                measure_type_detailed_defense='Advanced',
                per_mode_detailed='PerGame',
                season_type_all_star='Regular Season'
            )
            
            regular_df = pd.DataFrame(regular_stats.get_data_frames()[0])
            advanced_df = pd.DataFrame(advanced_stats.get_data_frames()[0])
            
            # Merge statistics
            player_stats = pd.merge(
                regular_df,
                advanced_df,
                on='PLAYER_ID',
                suffixes=('', '_advanced')
            )
            
            # Clean and rename columns
            player_stats = player_stats.rename(columns={
                'PLAYER_NAME': 'name',
                'TEAM_ABBREVIATION': 'team',
                'AGE': 'age',
                'GP': 'games_played',
                'MIN': 'minutes_played',
                'PTS': 'points',
                'REB': 'rebounds',
                'AST': 'assists',
                'STL': 'steals',
                'BLK': 'blocks',
                'TOV': 'turnovers',
                'FGA': 'field_goals_attempted',
                'FGM': 'field_goals_made',
                'FG3A': 'three_point_attempted',
                'FG3M': 'three_point_made',
                'FTA': 'free_throws_attempted',
                'FTM': 'free_throws_made'
            })
            
            return player_stats
            
        except Exception as e:
            logger.error(f"Error collecting player stats for season {season}: {e}")
            return pd.DataFrame()

async def main():
    """Main function to run historical data collection."""
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Initialize collector
    collector = HistoricalDataCollector(db_manager)
    
    try:
        # Collect all historical data
        await collector.collect_all_historical_data()
    finally:
        # Close database connections
        db_manager.close()

if __name__ == "__main__":
    asyncio.run(main()) 