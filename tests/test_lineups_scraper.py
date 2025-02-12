"""
Test module for lineups.com scraper.
"""

import pandas as pd
import pytest

from src.collectors.lineups_scraper import LineupsCollector


@pytest.fixture
def scraper():
    """Create a LineupsCollector instance."""
    return LineupsCollector()


def test_get_matchups(scraper):
    """Test getting NBA matchups."""
    matchups = scraper.get_matchups()
    
    # Check if we got a DataFrame
    assert isinstance(matchups, pd.DataFrame)
    
    # Check required columns
    required_columns = ['date', 'time', 'away_team', 'home_team']
    assert all(col in matchups.columns for col in required_columns)
    
    # Check data types
    assert pd.api.types.is_datetime64_any_dtype(matchups['date'])
    assert pd.api.types.is_string_dtype(matchups['time'])
    assert pd.api.types.is_string_dtype(matchups['away_team'])
    assert pd.api.types.is_string_dtype(matchups['home_team'])


def test_get_projections(scraper):
    """Test getting NBA player projections."""
    projections = scraper.get_projections()
    
    # Check if we got a DataFrame
    assert isinstance(projections, pd.DataFrame)
    
    # Check required columns
    required_columns = ['player', 'team', 'opponent', 'minutes', 'points']
    assert all(col in projections.columns for col in required_columns)


def test_get_team_rankings(scraper):
    """Test getting NBA team rankings."""
    rankings = scraper.get_team_rankings()
    
    # Check if we got a DataFrame
    assert isinstance(rankings, pd.DataFrame)
    
    # Check required columns
    required_columns = ['rank', 'team', 'record', 'net_rating']
    assert all(col in rankings.columns for col in required_columns)


def test_get_depth_charts(scraper):
    """Test getting NBA team depth charts."""
    depth_charts = scraper.get_depth_charts()
    
    # Check if we got a dictionary
    assert isinstance(depth_charts, dict)
    
    # Check first team's depth chart
    first_team = next(iter(depth_charts.values()))
    assert isinstance(first_team, pd.DataFrame)
    
    # Check required columns
    required_columns = ['position', 'starter', 'second', 'third']
    assert all(col in first_team.columns for col in required_columns)


def test_get_starting_lineups(scraper):
    """Test getting NBA starting lineups."""
    lineups = scraper.get_starting_lineups()
    
    # Check if we got a dictionary
    assert isinstance(lineups, dict)
    
    # Check first team's lineup
    first_team = next(iter(lineups.values()))
    assert isinstance(first_team, list)
    assert len(first_team) <= 5  # Should have 5 or fewer starters


def test_get_team_stats(scraper):
    """Test getting NBA team statistics."""
    team_stats = scraper.get_team_stats()
    
    # Check if we got a DataFrame
    assert isinstance(team_stats, pd.DataFrame)
    
    # Should have at least 30 teams
    assert len(team_stats) >= 30


def test_get_player_stats(scraper):
    """Test getting NBA player statistics."""
    player_stats = scraper.get_player_stats()
    
    # Check if we got a DataFrame
    assert isinstance(player_stats, pd.DataFrame)
    
    # Should have multiple players
    assert len(player_stats) > 100


def test_get_injuries(scraper):
    """Test getting NBA injury reports."""
    injuries = scraper.get_injuries()
    
    # Check if we got a DataFrame
    assert isinstance(injuries, pd.DataFrame)
    
    # Check required columns
    required_columns = ['player', 'team', 'position', 'injury', 'status']
    assert all(col in injuries.columns for col in required_columns) 