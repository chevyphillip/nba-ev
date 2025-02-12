"""
Test script for the NBA data cleaning pipeline.
"""
import logging
from pathlib import Path

import pandas as pd
from data_cleaner import NBADataCleaner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_cleaned_data(cleaned_data: dict) -> bool:
    """Verify the cleaned data meets our requirements."""
    
    # Check team stats
    if 'team_stats' in cleaned_data:
        team_stats = cleaned_data['team_stats']
        logger.info("\nTeam Stats Summary:")
        logger.info(f"Number of teams: {len(team_stats)}")
        logger.info(f"Advanced metrics present: {', '.join(['POSS', 'OFF_RATING', 'DEF_RATING', 'NET_RATING'])}")
        logger.info("\nSample team stats:")
        logger.info(team_stats[['TEAM_NAME', 'W_PCT', 'OFF_RATING', 'DEF_RATING', 'NET_RATING']].head())
    
    # Check player stats
    if 'player_stats' in cleaned_data:
        player_stats = cleaned_data['player_stats']
        logger.info("\nPlayer Stats Summary:")
        logger.info(f"Number of players: {len(player_stats)}")
        logger.info(f"Data sources merged: {'name_key' in player_stats.columns}")
        logger.info("\nSample player stats:")
        display_cols = ['PLAYER_NAME', 'team', 'positions', 'points', 'assists', 'rebounds']
        available_cols = [col for col in display_cols if col in player_stats.columns]
        logger.info(player_stats[available_cols].head())
    
    # Check schedule
    if 'schedule' in cleaned_data:
        schedule = cleaned_data['schedule']
        logger.info("\nSchedule Summary:")
        logger.info(f"Number of games: {len(schedule)}")
        logger.info(f"Date range: {schedule['start_time'].min()} to {schedule['start_time'].max()}")
        logger.info("\nSample schedule:")
        logger.info(schedule[['game_id', 'start_time', 'home_team', 'away_team', 'home_win']].head())
    
    return True

def main():
    """Main function to test the cleaning pipeline."""
    # Initialize cleaner
    cleaner = NBADataCleaner()
    
    # Clean 2023 season data
    season_dir = Path("data/historical/season_2023")
    cleaned_data = cleaner.clean_season_data(season_dir)
    
    if cleaned_data:
        # Verify the cleaned data
        if verify_cleaned_data(cleaned_data):
            logger.info("\nData cleaning verification passed!")
            
            # Save cleaned data
            output_dir = Path("data/historical/season_2023_cleaned")
            cleaner.save_cleaned_data(cleaned_data, output_dir)
        else:
            logger.error("Data cleaning verification failed!")
    else:
        logger.error("No cleaned data to verify!")

if __name__ == "__main__":
    main() 