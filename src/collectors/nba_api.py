"""
Module for collecting data from the NBA API.
"""

from typing import Dict, List, Optional

import pandas as pd
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.endpoints import (commonplayerinfo, leaguedashplayerstats,
                                     leaguedashteamstats, leaguelineupviz,
                                     playerprofilev2, teamplayerdashboard)
from nba_api.stats.library.parameters import \
    MeasureTypeDetailedDefense as MeasureType
from nba_api.stats.library.parameters import PerModeDetailed as PerMode
from nba_api.stats.library.parameters import Season, SeasonType
from nba_api.stats.static import players


def get_team_advanced_stats(season: str = Season.default) -> pd.DataFrame:
    """
    Collect advanced team statistics from NBA API.
    
    Args:
        season: NBA season in format '2023-24' (default: current season)
        
    Returns:
        DataFrame containing advanced team statistics
    """
    team_stats = leaguedashteamstats.LeagueDashTeamStats(
        season=season,
        season_type_all_star=SeasonType.regular,
        measure_type_detailed_defense='Advanced',
        per_mode_detailed='PerGame'
    ).get_data_frames()[0]
    
    return team_stats

def get_player_advanced_stats(season: str = Season.default) -> pd.DataFrame:
    """
    Collect comprehensive player statistics from NBA API.
    
    Args:
        season: NBA season in format '2023-24' (default: current season)
        
    Returns:
        DataFrame containing comprehensive player statistics
    """
    # Get basic stats
    basic_stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star=SeasonType.regular,
        measure_type_detailed_defense=MeasureType.base,
        per_mode_detailed=PerMode.per_game
    ).get_data_frames()[0]
    
    # Get advanced stats
    advanced_stats = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season,
        season_type_all_star=SeasonType.regular,
        measure_type_detailed_defense=MeasureType.advanced,
        per_mode_detailed=PerMode.per_game
    ).get_data_frames()[0]
    
    # Merge stats and select relevant columns
    player_stats = pd.merge(
        basic_stats,
        advanced_stats,
        on=['PLAYER_ID', 'PLAYER_NAME', 'TEAM_ID', 'TEAM_ABBREVIATION'],
        suffixes=('', '_ADV')
    )
    
    # Rename columns to match our standardized format
    column_mapping = {
        'PLAYER_NAME': 'name',
        'TEAM_ABBREVIATION': 'team',
        'AGE': 'age',
        'GP': 'gp',
        'MIN': 'mpg',
        'USG_PCT': 'usg%',
        'FTA': 'fta',
        'FT_PCT': 'ft%',
        'FGA': '2pa',
        'FG_PCT': '2p%',
        'FG3A': '3pa',
        'FG3_PCT': '3p%',
        'PTS': 'ppg',
        'REB': 'rpg',
        'AST': 'apg',
        'STL': 'spg',
        'BLK': 'bpg',
        'TOV': 'tpg',
        'PIE': 'pir',  # Performance Index Rating
        'PACE': 'pace',
        'OFF_RATING': 'offensive_rating',
        'DEF_RATING': 'defensive_rating',
        'NET_RATING': 'net_rating'
    }
    
    player_stats = player_stats.rename(columns=column_mapping)
    
    # Calculate Versatility Index (VI)
    player_stats['vi'] = (
        (player_stats['ppg'] * 1.0) +
        (player_stats['rpg'] * 1.2) +
        (player_stats['apg'] * 1.5) +
        (player_stats['spg'] * 2.0) +
        (player_stats['bpg'] * 2.0) -
        (player_stats['tpg'] * 1.0)
    ) / player_stats['mpg']
    
    return player_stats

def get_player_positions() -> pd.DataFrame:
    """
    Get player position information.
    
    Returns:
        DataFrame containing player positions and basic info
    """
    # Get all active players
    active_players = players.get_active_players()
    
    # Create DataFrame with player info
    positions_df = pd.DataFrame(active_players)[['id', 'full_name', 'position']]
    positions_df = positions_df.rename(columns={
        'id': 'PLAYER_ID',
        'full_name': 'name',
        'position': 'pos'
    })
    
    return positions_df 

def get_real_time_lineups() -> pd.DataFrame:
    """
    Collect real-time lineup data from NBA API.
    
    Returns:
        DataFrame containing current lineup information
    """
    # Get current games
    games = scoreboard.ScoreBoard().get_data_frames()[0]
    
    lineups = []
    for _, game in games.iterrows():
        # Get lineup data for home team
        home_lineup = teamplayerdashboard.TeamPlayerDashboard(
            team_id=game['HOME_TEAM_ID'],
            season_type_all_star='Regular Season'
        ).get_data_frames()[0]
        
        # Get lineup data for away team
        away_lineup = teamplayerdashboard.TeamPlayerDashboard(
            team_id=game['AWAY_TEAM_ID'],
            season_type_all_star='Regular Season'
        ).get_data_frames()[0]
        
        # Add game context
        home_lineup['GAME_ID'] = game['GAME_ID']
        home_lineup['IS_HOME'] = True
        away_lineup['GAME_ID'] = game['GAME_ID']
        away_lineup['IS_HOME'] = False
        
        lineups.extend([home_lineup, away_lineup])
    
    return pd.concat(lineups, ignore_index=True)

def get_injury_report() -> pd.DataFrame:
    """
    Collect current injury information from NBA API.
    
    Returns:
        DataFrame containing injury report
    """
    # Get all active players
    players = leaguedashplayerstats.LeagueDashPlayerStats().get_data_frames()[0]
    
    injury_list = []
    for _, player in players.iterrows():
        # Get detailed player info including injury status
        player_info = commonplayerinfo.CommonPlayerInfo(
            player_id=player['PLAYER_ID']
        ).get_data_frames()[0]
        
        if 'ROSTERSTATUS' in player_info.columns and player_info['ROSTERSTATUS'].iloc[0] != 'Active':
            injury_list.append({
                'PLAYER_ID': player['PLAYER_ID'],
                'PLAYER_NAME': player['PLAYER_NAME'],
                'TEAM_ID': player['TEAM_ID'],
                'TEAM_ABBREVIATION': player['TEAM_ABBREVIATION'],
                'INJURY_STATUS': player_info['ROSTERSTATUS'].iloc[0]
            })
    
    return pd.DataFrame(injury_list)

def get_depth_charts() -> pd.DataFrame:
    """
    Collect team depth chart information from NBA API.
    
    Returns:
        DataFrame containing depth chart information
    """
    # Get lineup data for all teams
    lineup_data = leaguelineupviz.LeagueLineupViz(
        season_type_all_star='Regular Season'
    ).get_data_frames()[0]
    
    # Process lineup data to create depth charts
    depth_charts = []
    for team_id in lineup_data['TEAM_ID'].unique():
        team_lineups = lineup_data[lineup_data['TEAM_ID'] == team_id]
        
        # Get most used lineups
        top_lineups = team_lineups.nlargest(5, 'MIN')
        
        # Extract player roles from lineups
        for _, lineup in top_lineups.iterrows():
            players = [
                lineup[f'PLAYER_{i}_NAME'] for i in range(1, 6)
            ]
            minutes = lineup['MIN']
            
            depth_charts.append({
                'TEAM_ID': team_id,
                'LINEUP_PLAYERS': players,
                'MINUTES_PLAYED': minutes
            })
    
    return pd.DataFrame(depth_charts)

def get_real_time_data() -> Dict[str, pd.DataFrame]:
    """
    Collect all real-time data from NBA API.
    
    Returns:
        Dictionary containing DataFrames with real-time data
    """
    return {
        'lineups': get_real_time_lineups(),
        'injuries': get_injury_report(),
        'depth_charts': get_depth_charts()
    } 