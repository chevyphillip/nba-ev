import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Load the data
    team_stats = pd.read_parquet('data/historical/season_2023_cleaned/team_stats_cleaned.parquet')
    schedule = pd.read_parquet('data/historical/season_2023_cleaned/schedule_cleaned.parquet')
    
    # Get unique team names from team stats
    team_names = set(team_stats['TEAM_NAME'].unique())
    logger.info("\nTeam names from team stats:")
    for name in sorted(team_names):
        logger.info(name)
        
    # Get unique team names from schedule
    schedule_teams = set()
    schedule_teams.update(schedule['home_team'].unique())
    schedule_teams.update(schedule['away_team'].unique())
    logger.info("\nTeam names from schedule:")
    for name in sorted(schedule_teams):
        logger.info(name)
        
    # Find mismatches
    logger.info("\nTeams in schedule but not in team stats:")
    for name in sorted(schedule_teams - team_names):
        logger.info(name)
        
    logger.info("\nTeams in team stats but not in schedule:")
    for name in sorted(team_names - schedule_teams):
        logger.info(name)

if __name__ == '__main__':
    main() 