"""
Database manager for NBA data.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base, Game, Player, Team, BoxScore, PlayByPlay

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
        if isinstance(pos, list):
            return ', '.join(pos)
        if isinstance(pos, bytes):
            return pos.decode('latin1')
        return str(pos)
    except:
        return 'Unknown'

class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, database_url: str = "sqlite:///data/nba.db"):
        """Initialize database manager."""
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        self.team_id_map = {}
        self.team_name_map = {}
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def load_season_data(self, cleaned_data_dir: Path):
        """Load cleaned season data into database."""
        try:
            # Read cleaned data
            team_stats = pd.read_parquet(cleaned_data_dir / 'team_stats_cleaned.parquet')
            player_stats = pd.read_parquet(cleaned_data_dir / 'player_stats_cleaned.parquet')
            schedule = pd.read_parquet(cleaned_data_dir / 'schedule_cleaned.parquet')
            box_scores = pd.read_parquet(cleaned_data_dir / 'box_scores_cleaned.parquet')
            play_by_play = pd.read_parquet(cleaned_data_dir / 'play_by_play_cleaned.parquet')
            
            # Create database session
            session = self.Session()
            
            try:
                # Load teams first
                self._load_teams(session, team_stats)
                session.commit()
                
                # Get team name to ID mapping
                teams_df = pd.read_sql("SELECT team_id, name FROM teams", self.engine)
                self.team_id_map = dict(zip(teams_df['name'], teams_df['team_id']))
                
                # Load players
                self._load_players(session, player_stats)
                
                # Load games
                self._load_games(session, schedule)
                
                # Load box scores
                self._load_box_scores(session, box_scores)
                
                # Load play-by-play data
                self._load_play_by_play(session, play_by_play)
                
                # Commit changes
                session.commit()
                logger.info(f"Successfully loaded data from {cleaned_data_dir}")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error loading data: {str(e)}")
                raise
            
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Error reading data files: {str(e)}")
            raise
    
    def _load_teams(self, session: Session, team_stats: pd.DataFrame):
        """Load team data into database."""
        self.team_id_map = {}  # Reset the map
        
        for _, row in team_stats.iterrows():
            try:
                team_name = row['team_name']
                if not team_name:
                    continue
                    
                team = Team(
                    team_id=str(len(self.team_id_map) + 1),  # Generate sequential team IDs
                    name=team_name,
                    games_played=row['games_played'],
                    wins=row['wins'],
                    losses=row['losses'],
                    win_pct=row['win_pct'],
                    
                    # Basic stats
                    points_scored=row['points_scored'],
                    points_allowed=row['points_allowed'],
                    points_per_game=row['points_per_game'],
                    points_allowed_per_game=row['points_allowed_per_game'],
                    field_goals_made=row.get('field_goals_made', 0),
                    field_goals_attempted=row.get('field_goals_attempted', 0),
                    field_goal_pct=row['field_goal_pct'],
                    three_points_made=row.get('three_points_made', 0),
                    three_points_attempted=row.get('three_points_attempted', 0),
                    three_point_pct=row['three_point_pct'],
                    free_throws_made=row.get('free_throws_made', 0),
                    free_throws_attempted=row.get('free_throws_attempted', 0),
                    free_throw_pct=row['free_throw_pct'],
                    
                    # Per game stats
                    minutes_per_game=row['minutes_per_game'],
                    rebounds_per_game=row['rebounds_per_game'],
                    assists_per_game=row['assists_per_game'],
                    steals_per_game=row['steals_per_game'],
                    blocks_per_game=row['blocks_per_game'],
                    turnovers_per_game=row['turnovers_per_game'],
                    fouls_per_game=row['fouls_per_game'],
                    
                    # Advanced stats
                    possessions=row['possessions'],
                    pace=row['pace'],
                    offensive_rating=row['offensive_rating'],
                    defensive_rating=row['defensive_rating'],
                    net_rating=row['net_rating'],
                    true_shooting_pct=row['true_shooting_pct'],
                    effective_fg_pct=row['effective_fg_pct'],
                    offensive_rebound_pct=row.get('offensive_rebound_pct', 0),
                    defensive_rebound_pct=row.get('defensive_rebound_pct', 0),
                    total_rebound_pct=row.get('total_rebound_pct', 0),
                    assist_pct=row.get('assist_pct', 0),
                    steal_pct=row.get('steal_pct', 0),
                    block_pct=row.get('block_pct', 0),
                    turnover_pct=row.get('turnover_pct', 0)
                )
                session.merge(team)
                session.flush()  # Ensure the team has an ID
                
                # Store the team ID mapping
                self.team_id_map[team_name] = team.team_id
                
            except Exception as e:
                logger.error(f"Error loading team {row.get('team_name', 'Unknown')}: {str(e)}")
                raise
    
    def _normalize_team_name(self, name: str) -> str:
        """Normalize team name for consistent matching."""
        if not name:
            return ""
        
        # Convert to uppercase for comparison
        name = str(name).upper()
        
        # Handle special cases
        name_map = {
            "LA CLIPPERS": "LOS ANGELES CLIPPERS",
        }
        
        return name_map.get(name, name)
    
    def _get_team_id(self, name: Union[str, None]) -> Union[int, None]:
        """Get team ID from name, handling different formats."""
        if not name:
            return None
        
        # Normalize the input name
        normalized_name = self._normalize_team_name(name)
        
        # Try to find the team ID using the normalized name
        for orig_name, team_id in self.team_id_map.items():
            if self._normalize_team_name(orig_name) == normalized_name:
                return team_id
        
        return None
    
    def _load_players(self, session: Session, player_stats: pd.DataFrame):
        """Load player data into database."""
        for _, row in player_stats.iterrows():
            try:
                # Get team ID from name
                team_name = row.get('team')
                team_id = self.team_id_map.get(team_name) if team_name else None
                
                # Clean positions
                positions = clean_positions(row.get('positions'))
                
                # Calculate shooting percentages
                fg_pct = (row.get('made_field_goals', 0) / row.get('attempted_field_goals', 1)) if row.get('attempted_field_goals', 0) > 0 else None
                three_pt_pct = (row.get('made_three_point_field_goals', 0) / row.get('attempted_three_point_field_goals', 1)) if row.get('attempted_three_point_field_goals', 0) > 0 else None
                ft_pct = (row.get('made_free_throws', 0) / row.get('attempted_free_throws', 1)) if row.get('attempted_free_throws', 0) > 0 else None
                
                player = Player(
                    name=row.get('name', row.get('PLAYER_NAME')),
                    team_id=team_id,
                    positions=positions,
                    age=row.get('age', row.get('AGE')),
                    games_played=row.get('games_played', row.get('GP')),
                    games_started=row.get('games_started'),
                    minutes_played=row.get('minutes_played', row.get('MIN')),
                    points=row.get('points', row.get('PTS')),
                    assists=row.get('assists', row.get('AST')),
                    rebounds=row.get('rebounds', row.get('REB')),
                    steals=row.get('steals', row.get('STL')),
                    blocks=row.get('blocks', row.get('BLK')),
                    turnovers=row.get('turnovers', row.get('TOV')),
                    field_goals_made=row.get('made_field_goals', row.get('FGM')),
                    field_goals_attempted=row.get('attempted_field_goals', row.get('FGA')),
                    field_goal_pct=fg_pct,
                    three_points_made=row.get('made_three_point_field_goals', row.get('FG3M')),
                    three_points_attempted=row.get('attempted_three_point_field_goals', row.get('FG3A')),
                    three_point_pct=three_pt_pct,
                    free_throws_made=row.get('made_free_throws', row.get('FTM')),
                    free_throws_attempted=row.get('attempted_free_throws', row.get('FTA')),
                    free_throw_pct=ft_pct
                )
                session.merge(player)
            except Exception as e:
                logger.error(f"Error loading player {row.get('name', row.get('PLAYER_NAME', 'Unknown'))}: {str(e)}")
    
    def _load_games(self, session: Session, schedule: pd.DataFrame):
        """Load game data into database."""
        for _, row in schedule.iterrows():
            try:
                # Get team IDs
                home_team = str(row.get('home_team', ''))
                away_team = str(row.get('away_team', ''))
                
                home_team_id = self._get_team_id(home_team)
                away_team_id = self._get_team_id(away_team)
                
                if home_team_id and away_team_id:
                    # Safely convert start_time
                    start_time = row.get('start_time')
                    if start_time is None:
                        logger.warning(f"Missing start time for game: {home_team} vs {away_team}")
                        continue
                    
                    game = Game(
                        game_id=row.get('game_id'),
                        start_time=start_time if isinstance(start_time, pd.Timestamp) else pd.to_datetime(str(start_time)),
                        home_team_id=home_team_id,
                        away_team_id=away_team_id,
                        home_team_score=row.get('home_team_score'),
                        away_team_score=row.get('away_team_score'),
                        total_score=row.get('total_score'),
                        score_margin=row.get('score_margin'),
                        home_win=row.get('home_win')
                    )
                    session.add(game)
                else:
                    logger.warning(f"Could not find team IDs for game: {home_team} vs {away_team}")
                
            except Exception as e:
                logger.error(f"Error loading game {row.get('start_time')}: {str(e)}")
    
    def _load_box_scores(self, session: Session, box_scores: pd.DataFrame):
        """Load box score data into database."""
        for _, row in box_scores.iterrows():
            try:
                # Get team ID
                team_id = self._get_team_id(row['team'])
                if not team_id:
                    logger.warning(f"Could not find team ID for {row['team']}, skipping box score")
                    continue
                
                # Create box score entry
                box_score = BoxScore(
                    game_id=row['game_id'],
                    player_id=row['player_id'],
                    team_id=team_id,
                    is_starter=row['is_starter'],
                    
                    # Minutes played
                    minutes_played=row['minutes_played'],
                    
                    # Basic stats
                    points=row['points'],
                    assists=row['assists'],
                    offensive_rebounds=row['offensive_rebounds'],
                    defensive_rebounds=row['defensive_rebounds'],
                    total_rebounds=row['total_rebounds'],
                    steals=row['steals'],
                    blocks=row['blocks'],
                    turnovers=row['turnovers'],
                    personal_fouls=row['personal_fouls'],
                    
                    # Shooting stats
                    field_goals_made=row['field_goals_made'],
                    field_goals_attempted=row['field_goals_attempted'],
                    field_goal_pct=row['field_goal_pct'],
                    three_points_made=row['three_points_made'],
                    three_points_attempted=row['three_points_attempted'],
                    three_point_pct=row['three_point_pct'],
                    free_throws_made=row['free_throws_made'],
                    free_throws_attempted=row['free_throws_attempted'],
                    free_throw_pct=row['free_throw_pct'],
                    
                    # Advanced stats
                    true_shooting_pct=row['true_shooting_pct'],
                    effective_fg_pct=row['effective_fg_pct'],
                    usage_rate=row['usage_rate'],
                    game_score=row['game_score']
                )
                session.merge(box_score)
                
            except Exception as e:
                logger.error(f"Error loading box score for player {row.get('name', 'Unknown')}: {str(e)}")
                continue
        
        session.flush()

    def _load_play_by_play(self, session: Session, play_by_play: pd.DataFrame):
        """Load play-by-play data into database."""
        for _, row in play_by_play.iterrows():
            try:
                # Get team IDs
                team_id = self._get_team_id(row['team_id'])
                possession_team_id = self._get_team_id(row['possession_team_id'])
                
                if not team_id or not possession_team_id:
                    logger.warning(f"Could not find team IDs for play, skipping")
                    continue
                
                # Create play-by-play entry
                play = PlayByPlay(
                    game_id=row['game_id'],
                    period=row['period'],
                    time_remaining=row['time_remaining'],
                    description=row['description'],
                    score=row['score'],
                    team_id=team_id,
                    player_id=row['player_id'],
                    event_type=row['event_type'],
                    shot_type=row['shot_type'],
                    shot_distance=row['shot_distance'],
                    shot_made=row['shot_made'],
                    assist_player_id=row['assist_player_id'],
                    block_player_id=row['block_player_id'],
                    steal_player_id=row['steal_player_id'],
                    foul_type=row['foul_type'],
                    points_scored=row['points_scored'],
                    possession_team_id=possession_team_id,
                    home_score=row['home_score'],
                    away_score=row['away_score']
                )
                session.merge(play)
                
            except Exception as e:
                logger.error(f"Error loading play-by-play data: {str(e)}")
                continue
        
        session.flush()

def main():
    """Main function to load all cleaned data into database."""
    manager = DatabaseManager()
    data_dir = Path("data/historical")
    
    # Load each season's cleaned data
    for season_dir in data_dir.glob("season_*_cleaned"):
        try:
            manager.load_season_data(season_dir)
        except Exception as e:
            logger.error(f"Failed to load data from {season_dir}: {str(e)}")

if __name__ == "__main__":
    main() 