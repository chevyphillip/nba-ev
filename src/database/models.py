"""
SQLAlchemy models for NBA data.
"""
from datetime import datetime
from typing import List

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                       String, Table)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Team(Base):
    """Team model for storing team statistics."""
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    team_id = Column(String, unique=True)
    name = Column(String)
    games_played = Column(Integer)
    wins = Column(Integer)
    losses = Column(Integer)
    win_pct = Column(Float)
    
    # Basic stats
    points_scored = Column(Float)
    points_allowed = Column(Float)
    points_per_game = Column(Float)
    points_allowed_per_game = Column(Float)
    field_goals_made = Column(Float)
    field_goals_attempted = Column(Float)
    field_goal_pct = Column(Float)
    three_points_made = Column(Float)
    three_points_attempted = Column(Float)
    three_point_pct = Column(Float)
    free_throws_made = Column(Float)
    free_throws_attempted = Column(Float)
    free_throw_pct = Column(Float)
    
    # Rebounding
    offensive_rebounds = Column(Float)
    defensive_rebounds = Column(Float)
    total_rebounds = Column(Float)
    rebounds_per_game = Column(Float)
    
    # Other stats
    assists = Column(Float)
    assists_per_game = Column(Float)
    steals = Column(Float)
    steals_per_game = Column(Float)
    blocks = Column(Float)
    blocks_per_game = Column(Float)
    turnovers = Column(Float)
    turnovers_per_game = Column(Float)
    personal_fouls = Column(Float)
    fouls_per_game = Column(Float)
    
    # Advanced stats
    possessions = Column(Float)
    pace = Column(Float)
    minutes_per_game = Column(Float)
    offensive_rating = Column(Float)
    defensive_rating = Column(Float)
    net_rating = Column(Float)
    effective_fg_pct = Column(Float)
    true_shooting_pct = Column(Float)
    offensive_rebound_pct = Column(Float)
    defensive_rebound_pct = Column(Float)
    total_rebound_pct = Column(Float)
    assist_pct = Column(Float)
    steal_pct = Column(Float)
    block_pct = Column(Float)
    turnover_pct = Column(Float)
    
    # Relationships
    home_games = relationship('Game', back_populates='home_team', foreign_keys='Game.home_team_id')
    away_games = relationship('Game', back_populates='away_team', foreign_keys='Game.away_team_id')
    players = relationship('Player', back_populates='team')

class Player(Base):
    """Player model for storing player statistics."""
    __tablename__ = 'players'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    team_id = Column(String, ForeignKey('teams.team_id'))
    positions = Column(String)
    age = Column(Integer)
    games_played = Column(Integer)
    games_started = Column(Integer)
    minutes_played = Column(Float)
    
    # Basic stats
    points = Column(Float)
    assists = Column(Float)
    rebounds = Column(Float)
    steals = Column(Float)
    blocks = Column(Float)
    turnovers = Column(Float)
    
    # Shooting stats
    field_goals_made = Column(Float)
    field_goals_attempted = Column(Float)
    field_goal_pct = Column(Float)
    three_points_made = Column(Float)
    three_points_attempted = Column(Float)
    three_point_pct = Column(Float)
    free_throws_made = Column(Float)
    free_throws_attempted = Column(Float)
    free_throw_pct = Column(Float)
    
    # Advanced stats
    true_shooting_pct = Column(Float)
    effective_fg_pct = Column(Float)
    usage_rate = Column(Float)
    assist_pct = Column(Float)
    rebound_pct = Column(Float)
    steal_pct = Column(Float)
    block_pct = Column(Float)
    turnover_pct = Column(Float)
    offensive_rating = Column(Float)
    defensive_rating = Column(Float)
    player_efficiency = Column(Float)
    value_over_replacement = Column(Float)
    win_shares = Column(Float)
    box_plus_minus = Column(Float)
    
    # Relationships
    team = relationship('Team', back_populates='players')

class Game(Base):
    """Game model for storing game data."""
    __tablename__ = 'games'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String, unique=True)
    start_time = Column(DateTime)
    
    home_team_id = Column(String, ForeignKey('teams.team_id'))
    away_team_id = Column(String, ForeignKey('teams.team_id'))
    
    home_team_score = Column(Integer)
    away_team_score = Column(Integer)
    total_score = Column(Integer)
    score_margin = Column(Integer)
    home_win = Column(Boolean)
    
    # Relationships
    home_team = relationship('Team', foreign_keys=[home_team_id], back_populates='home_games')
    away_team = relationship('Team', foreign_keys=[away_team_id], back_populates='away_games')
    box_scores = relationship('BoxScore', back_populates='game', cascade='all, delete-orphan')
    plays = relationship('PlayByPlay', back_populates='game', cascade='all, delete-orphan')

class BoxScore(Base):
    """Model for storing player box scores for each game."""
    __tablename__ = 'box_scores'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String, ForeignKey('games.game_id'))
    player_id = Column(String, ForeignKey('players.id'))
    team_id = Column(String, ForeignKey('teams.team_id'))
    is_starter = Column(Boolean)
    
    # Minutes played
    minutes_played = Column(Float)
    
    # Basic stats
    points = Column(Integer)
    assists = Column(Integer)
    offensive_rebounds = Column(Integer)
    defensive_rebounds = Column(Integer)
    total_rebounds = Column(Integer)
    steals = Column(Integer)
    blocks = Column(Integer)
    turnovers = Column(Integer)
    personal_fouls = Column(Integer)
    plus_minus = Column(Integer)
    
    # Shooting stats
    field_goals_made = Column(Integer)
    field_goals_attempted = Column(Integer)
    field_goal_pct = Column(Float)
    three_points_made = Column(Integer)
    three_points_attempted = Column(Integer)
    three_point_pct = Column(Float)
    free_throws_made = Column(Integer)
    free_throws_attempted = Column(Integer)
    free_throw_pct = Column(Float)
    
    # Advanced stats for the game
    true_shooting_pct = Column(Float)
    effective_fg_pct = Column(Float)
    usage_rate = Column(Float)
    offensive_rating = Column(Float)
    defensive_rating = Column(Float)
    game_score = Column(Float)  # John Hollinger's GameScore metric
    
    # Relationships
    game = relationship('Game', back_populates='box_scores')
    player = relationship('Player', back_populates='box_scores')
    team = relationship('Team')

class PlayByPlay(Base):
    """Model for storing play-by-play data for each game."""
    __tablename__ = 'play_by_play'
    
    id = Column(Integer, primary_key=True)
    game_id = Column(String, ForeignKey('games.game_id'))
    period = Column(Integer)  # Quarter or overtime period
    time_remaining = Column(String)  # Time remaining in period
    description = Column(String)  # Description of the play
    score = Column(String)  # Score at the time of the play
    team_id = Column(String, ForeignKey('teams.team_id'))  # Team involved in the play
    player_id = Column(String, ForeignKey('players.id'))  # Player involved in the play
    event_type = Column(String)  # Type of event (shot, rebound, turnover, etc.)
    shot_type = Column(String, nullable=True)  # Type of shot if applicable
    shot_distance = Column(Float, nullable=True)  # Distance of shot if applicable
    shot_made = Column(Boolean, nullable=True)  # Whether shot was made if applicable
    assist_player_id = Column(String, ForeignKey('players.id'), nullable=True)  # Player who made assist if applicable
    block_player_id = Column(String, ForeignKey('players.id'), nullable=True)  # Player who made block if applicable
    steal_player_id = Column(String, ForeignKey('players.id'), nullable=True)  # Player who made steal if applicable
    foul_type = Column(String, nullable=True)  # Type of foul if applicable
    points_scored = Column(Integer, nullable=True)  # Points scored on play if applicable
    possession_team_id = Column(String, ForeignKey('teams.team_id'))  # Team with possession
    home_score = Column(Integer)  # Home team score after play
    away_score = Column(Integer)  # Away team score after play
    
    # Relationships
    game = relationship('Game', back_populates='plays')
    team = relationship('Team', foreign_keys=[team_id])
    possession_team = relationship('Team', foreign_keys=[possession_team_id])
    player = relationship('Player', foreign_keys=[player_id])
    assist_player = relationship('Player', foreign_keys=[assist_player_id])
    block_player = relationship('Player', foreign_keys=[block_player_id])
    steal_player = relationship('Player', foreign_keys=[steal_player_id])

# Add relationships to existing models
Player.box_scores = relationship('BoxScore', back_populates='player', cascade='all, delete-orphan') 