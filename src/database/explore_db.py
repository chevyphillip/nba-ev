"""
Script to explore and summarize NBA database contents.
"""
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from src.database.models import Game, Player, Team

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_positions(pos):
    """Clean position data."""
    if pd.isna(pos):
        return 'Unknown'
    try:
        if isinstance(pos, bytes):
            return pos.decode('latin1')
        return str(pos)
    except:
        return 'Unknown'

def explore_database(database_url: str = "sqlite:///data/nba.db"):
    """Explore and summarize database contents."""
    engine = create_engine(database_url)
    
    try:
        # Team Statistics
        logger.info("\n=== Team Statistics ===")
        teams_df = pd.read_sql("""
            SELECT 
                name,
                games_played,
                wins,
                losses,
                win_pct,
                offensive_rating,
                defensive_rating,
                net_rating
            FROM teams
            ORDER BY win_pct DESC
        """, engine)
        
        if not teams_df.empty:
            logger.info(f"\nNumber of teams: {len(teams_df)}")
            logger.info("\nTop 5 teams by win percentage:")
            logger.info(teams_df[['name', 'wins', 'losses', 'win_pct']].head())
            
            logger.info("\nTop 5 teams by net rating:")
            logger.info(teams_df[['name', 'offensive_rating', 'defensive_rating', 'net_rating']]
                    .sort_values('net_rating', ascending=False)
                    .head())
        else:
            logger.warning("No team data found in database")
        
        # Player Statistics
        logger.info("\n=== Player Statistics ===")
        players_df = pd.read_sql("""
            SELECT 
                p.name,
                t.name as team_name,
                p.positions,
                p.games_played,
                p.points,
                p.assists,
                p.rebounds,
                p.field_goal_pct,
                p.three_point_pct
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.team_id
            WHERE p.games_played > 0
            ORDER BY p.points DESC
        """, engine)
        
        if not players_df.empty:
            logger.info(f"\nNumber of players: {len(players_df)}")
            logger.info("\nTop 5 scorers:")
            logger.info(players_df[['name', 'team_name', 'points', 'games_played']].head())
            
            # Clean position data
            players_df['positions'] = players_df['positions'].apply(clean_positions)
            
            # Position distribution
            logger.info("\nPosition distribution:")
            position_counts = players_df['positions'].value_counts()
            logger.info(position_counts.head())
            
            # Shooting percentages by position
            logger.info("\nAverage shooting percentages by position:")
            shooting_by_pos = players_df.groupby('positions').agg({
                'field_goal_pct': 'mean',
                'three_point_pct': 'mean'
            }).round(3)
            logger.info(shooting_by_pos)
        else:
            logger.warning("No player data found in database")
        
        # Game Statistics
        logger.info("\n=== Game Statistics ===")
        games_df = pd.read_sql("""
            SELECT 
                g.*,
                ht.name as home_team_name,
                at.name as away_team_name
            FROM games g
            JOIN teams ht ON g.home_team_id = ht.team_id
            JOIN teams at ON g.away_team_id = at.team_id
            ORDER BY g.start_time
        """, engine)
        
        if not games_df.empty:
            logger.info(f"\nNumber of games: {len(games_df)}")
            
            # Home vs Away stats
            home_wins = games_df['home_win'].sum()
            total_games = len(games_df)
            logger.info(f"\nHome team win percentage: {home_wins/total_games:.3f}")
            
            # Scoring stats
            logger.info("\nScoring statistics:")
            logger.info(f"Average total score: {games_df['total_score'].mean():.1f}")
            logger.info(f"Highest scoring game: {games_df['total_score'].max()}")
            
            # Get highest scoring game details
            highest_game = games_df.loc[games_df['total_score'].idxmax()]
            logger.info(f"\nHighest scoring game:")
            logger.info(f"{highest_game['home_team_name']} ({highest_game['home_team_score']}) vs "
                        f"{highest_game['away_team_name']} ({highest_game['away_team_score']})")
            
            # Date range
            logger.info(f"\nGames from {games_df['start_time'].min()} to {games_df['start_time'].max()}")
            
            # Monthly scoring trends
            games_df['month'] = pd.to_datetime(games_df['start_time']).dt.strftime('%Y-%m')
            monthly_scores = games_df.groupby('month')['total_score'].mean().round(1)
            logger.info("\nMonthly scoring averages:")
            logger.info(monthly_scores)
        else:
            logger.warning("No game data found in database")
            
    except Exception as e:
        logger.error(f"Error exploring database: {str(e)}")
        raise

if __name__ == "__main__":
    explore_database() 