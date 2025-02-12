"""
Initialize database and load cleaned NBA data.
"""
import logging
from pathlib import Path

from src.database.manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize database and load data."""
    try:
        # Initialize database manager
        manager = DatabaseManager()
        logger.info("Database initialized successfully")
        
        # Load cleaned data
        data_dir = Path("data/historical")
        for season_dir in data_dir.glob("season_*_cleaned"):
            try:
                logger.info(f"Loading data from {season_dir}")
                manager.load_season_data(season_dir)
            except Exception as e:
                logger.error(f"Failed to load data from {season_dir}: {str(e)}")
        
        logger.info("Data loading completed")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

if __name__ == "__main__":
    init_database() 