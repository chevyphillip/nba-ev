"""
Module for collecting data from Basketball Reference.
"""

import pandas as pd
from basketball_reference_web_scraper import client as bref_client
from basketball_reference_web_scraper.data import Team


def get_season_stats(season_year: int) -> pd.DataFrame:
    """
    Collect season statistics from Basketball Reference.
    
    Args:
        season_year: The year the season ends in (e.g., 2024 for 2023-24 season)
        
    Returns:
        DataFrame containing season statistics
    """
    # Get regular season schedule
    regular_season_games = bref_client.season_schedule(season_end_year=season_year)
    
    # Convert to DataFrame
    bref_stats = pd.DataFrame(regular_season_games)
    
    # Convert Team enums to strings
    bref_stats['home_team'] = bref_stats['home_team'].apply(lambda x: x.value)
    bref_stats['away_team'] = bref_stats['away_team'].apply(lambda x: x.value)
    
    # Convert timezone-aware datetime columns to timezone-naive
    if 'start_time' in bref_stats.columns:
        bref_stats['start_time'] = bref_stats['start_time'].dt.tz_localize(None)
    
    return bref_stats

def get_player_season_stats(season_year: int) -> pd.DataFrame:
    """
    Collect player season statistics from Basketball Reference.
    
    Args:
        season_year: The year the season ends in (e.g., 2024 for 2023-24 season)
        
    Returns:
        DataFrame containing player statistics
    """
    # Get player season totals
    player_stats = pd.DataFrame(
        bref_client.players_season_totals(season_end_year=season_year)
    )
    
    # Convert team enum to string
    player_stats['team'] = player_stats['team'].apply(lambda x: x.value if x else None)
    
    # Rename columns to match standardized format
    column_mapping = {
        'name': 'name',  # Already correct
        'team': 'team',  # Already correct
        'games_played': 'gp',
        'minutes_played': 'mpg',
        'made_field_goals': 'fg',
        'attempted_field_goals': 'fga',
        'made_three_point_field_goals': '3p',
        'attempted_three_point_field_goals': '3pa',
        'made_free_throws': 'ft',
        'attempted_free_throws': 'fta',
        'offensive_rebounds': 'oreb',
        'defensive_rebounds': 'dreb',
        'assists': 'apg',
        'steals': 'spg',
        'blocks': 'bpg',
        'turnovers': 'tpg',
        'personal_fouls': 'pf',
        'points': 'ppg'
    }
    
    player_stats = player_stats.rename(columns=column_mapping)
    
    # Convert counting stats to per game
    per_game_cols = ['mpg', 'fg', 'fga', '3p', '3pa', 'ft', 'fta', 
                     'oreb', 'dreb', 'apg', 'spg', 'bpg', 'tpg', 'ppg']
    
    for col in per_game_cols:
        if col in player_stats.columns:
            player_stats[col] = player_stats[col] / player_stats['gp']
    
    # Calculate percentages
    player_stats['fg%'] = player_stats['fg'] / player_stats['fga']
    player_stats['3p%'] = player_stats['3p'] / player_stats['3pa']
    player_stats['ft%'] = player_stats['ft'] / player_stats['fta']
    
    return player_stats 