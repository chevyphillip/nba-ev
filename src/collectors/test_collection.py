"""
Test script for collecting NBA data for a single season.
"""
import logging
from pathlib import Path
import sys
from os.path import dirname, abspath
import pandas as pd
from tqdm import tqdm
import psutil
import os
from src.monitoring.metrics import (
    GAMES_COLLECTED,
    BOX_SCORES_COLLECTED,
    COLLECTION_ERRORS,
    REQUEST_DURATION,
    BATCH_PROCESSING_TIME,
    MEMORY_USAGE,
    CPU_USAGE
)
import time

# Add the project root to Python path
project_root = dirname(dirname(dirname(abspath(__file__))))
sys.path.append(project_root)

from src.collectors.historical_data import DataCollector
from src.database.manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/collection.log')
    ]
)
logger = logging.getLogger(__name__)

def update_resource_metrics():
    """Update CPU and memory usage metrics."""
    process = psutil.Process(os.getpid())
    
    # Update memory usage (in bytes)
    memory_info = process.memory_info()
    MEMORY_USAGE.set(memory_info.rss)
    
    # Update CPU usage (percentage)
    CPU_USAGE.set(process.cpu_percent())

def verify_database(season: int):
    """Verify that the season data was properly loaded into the database."""
    db = DatabaseManager()
    session = db.Session()
    
    try:
        # Check teams
        team_count = session.query(db.Team).count()
        logger.info(f"Teams in database: {team_count}")
        
        # Check players
        player_count = session.query(db.Player).count()
        logger.info(f"Players in database: {player_count}")
        
        # Check games
        game_count = session.query(db.Game).count()
        logger.info(f"Games in database: {game_count}")
        
        return team_count > 0 and player_count > 0 and game_count > 0
        
    finally:
        session.close()

def test_single_season():
    """Test data collection for the 2022 season."""
    try:
        start_time = time.time()
        
        # Start resource monitoring
        update_resource_metrics()
        
        # Create collector for just the 2022 season
        collector = DataCollector(start_season=2022, end_season=2022)
        
        # Collection progress tracking
        logger.info("Starting test collection for 2022 season...")
        logger.info("This will take approximately 7-10 minutes to complete")
        logger.info("Collection Steps:")
        
        # Step 1: Schedule
        logger.info("1. Schedule Collection (1-2 minutes)")
        schedule_start = time.time()
        collector.collect_all_seasons()
        schedule_duration = time.time() - schedule_start
        logger.info(f"Schedule collection completed in {schedule_duration:.1f} seconds")
        
        # Update resource metrics after schedule collection
        update_resource_metrics()
        
        # Verify the cleaned data files
        season_dir = Path("data/historical/season_2022_cleaned")
        expected_files = [
            'schedule.parquet',
            'player_stats.parquet',
            'team_stats.parquet',
            'box_scores.parquet'
        ]
        
        missing_files = []
        for file in expected_files:
            if not (season_dir / file).exists():
                missing_files.append(file)
                COLLECTION_ERRORS.labels(error_type='missing_file').inc()
        
        if missing_files:
            logger.warning(f"Missing cleaned files: {missing_files}")
            return False
        
        # Print summary statistics
        logger.info("\nData Collection Summary:")
        try:
            schedule = pd.read_parquet(season_dir / 'schedule.parquet')
            players = pd.read_parquet(season_dir / 'player_stats.parquet')
            teams = pd.read_parquet(season_dir / 'team_stats.parquet')
            boxes = pd.read_parquet(season_dir / 'box_scores.parquet')
            
            # Update Prometheus metrics
            GAMES_COLLECTED.inc(len(schedule))
            BOX_SCORES_COLLECTED.inc(len(boxes))
            
            logger.info(f"Total games collected: {len(schedule)}")
            logger.info(f"Total players collected: {len(players)}")
            logger.info(f"Total teams collected: {len(teams)}")
            logger.info(f"Total box scores collected: {len(boxes)}")
            
            # Calculate collection efficiency
            box_scores_per_game = len(boxes) / len(schedule) if len(schedule) > 0 else 0
            logger.info(f"Average box scores per game: {box_scores_per_game:.1f}")
            
            # Update resource metrics after data processing
            update_resource_metrics()
            
        except Exception as e:
            logger.error(f"Error reading summary statistics: {str(e)}")
            COLLECTION_ERRORS.labels(error_type='summary_stats').inc()
        
        # Calculate total duration
        total_duration = time.time() - start_time
        logger.info(f"\nTotal collection time: {total_duration:.1f} seconds")
        BATCH_PROCESSING_TIME.observe(total_duration)
        
        logger.info("\nAll cleaned data files were created successfully!")
        
        # Verify database
        logger.info("\nVerifying database contents...")
        if verify_database(2022):
            logger.info("Database verification successful!")
            return True
        else:
            logger.error("Database verification failed!")
            COLLECTION_ERRORS.labels(error_type='database_verification').inc()
            return False
            
    except Exception as e:
        logger.error(f"Test collection failed: {str(e)}")
        COLLECTION_ERRORS.labels(error_type='collection_failure').inc()
        raise
    finally:
        # Final resource metrics update
        update_resource_metrics()

if __name__ == "__main__":
    test_single_season() 