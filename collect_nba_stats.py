"""
NBA Stats Collection and Analysis Tool
This script collects real-time NBA data from various sources and performs analysis for betting purposes.
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np
import pandas as pd
import requests
from basketball_reference_web_scraper import client as bref_client
from basketball_reference_web_scraper.data import (OutputType,
                                                   OutputWriteOption, Team)
from dotenv import load_dotenv
from nba_api.stats.endpoints import leaguedashplayerstats, leaguedashteamstats
from nba_api.stats.library.parameters import Season, SeasonType


class NBADataCollector:
    """Handles data collection from various sources including Basketball Reference and The Odds API."""
    
    def __init__(self, odds_api_key: str):
        self.odds_api_key = odds_api_key
        self.base_url_odds = "https://api.the-odds-api.com/v4"
        self.current_season = "2023-24"  # NBA season format
        self.season_year = 2024  # Basketball Reference format
        
    def get_team_stats(self) -> pd.DataFrame:
        """Collect team statistics from Basketball Reference and NBA API."""
        # Get advanced team stats from NBA API
        nba_stats = leaguedashteamstats.LeagueDashTeamStats(
            season=Season.default,
            season_type_all_star=SeasonType.regular,
            measure_type_detailed_defense='Advanced',
            per_mode_detailed='PerGame'
        ).get_data_frames()[0]
        
        # Get season stats from Basketball Reference
        # First get regular season schedule
        regular_season_games = bref_client.season_schedule(season_end_year=self.season_year)
        
        # Convert to DataFrame
        bref_stats = pd.DataFrame(regular_season_games)
        
        # Convert Team enums to strings
        bref_stats['home_team'] = bref_stats['home_team'].apply(lambda x: x.value)
        bref_stats['away_team'] = bref_stats['away_team'].apply(lambda x: x.value)
        
        # Print column names for debugging
        print("Basketball Reference columns:", bref_stats.columns.tolist())
        print("NBA API columns:", nba_stats.columns.tolist())
        
        # Process and merge the data
        team_stats = self._process_team_stats(nba_stats, bref_stats)
        return team_stats
    
    def _process_team_stats(self, nba_stats: pd.DataFrame, bref_stats: pd.DataFrame) -> pd.DataFrame:
        """Process and merge team statistics from different sources."""
        # Calculate team statistics from game results
        home_team_stats = bref_stats.groupby('home_team').agg({
            'home_team_score': ['mean', 'count'],
            'away_team_score': 'mean',
        }).reset_index()
        
        away_team_stats = bref_stats.groupby('away_team').agg({
            'away_team_score': ['mean', 'count'],
            'home_team_score': 'mean',
        }).reset_index()
        
        # Rename columns for clarity
        home_team_stats.columns = ['team', 'points_for', 'games_played', 'points_against']
        away_team_stats.columns = ['team', 'points_for', 'games_played', 'points_against']
        
        # Combine home and away stats
        team_stats = pd.concat([home_team_stats, away_team_stats])
        team_stats = team_stats.groupby('team').agg({
            'points_for': 'mean',
            'points_against': 'mean',
            'games_played': 'sum'
        }).reset_index()
        
        # Add additional stats
        team_stats['net_rating'] = team_stats['points_for'] - team_stats['points_against']
        team_stats['win_pct'] = team_stats.apply(
            lambda x: bref_stats[
                ((bref_stats['home_team'] == x['team']) & (bref_stats['home_team_score'] > bref_stats['away_team_score'])) |
                ((bref_stats['away_team'] == x['team']) & (bref_stats['away_team_score'] > bref_stats['home_team_score']))
            ].shape[0] / x['games_played'],
            axis=1
        )
        
        # Merge with NBA API stats
        team_stats = pd.merge(
            team_stats,
            nba_stats,
            left_on='team',
            right_on='TEAM_NAME',
            how='outer'
        )
        
        return team_stats
    
    def get_player_stats(self) -> pd.DataFrame:
        """Collect player statistics from NBA API and Basketball Reference."""
        # Get advanced player stats from NBA API
        nba_stats = leaguedashplayerstats.LeagueDashPlayerStats(
            season=Season.default,
            season_type_all_star=SeasonType.regular,
            measure_type_detailed_defense='Advanced',
            per_mode_detailed='PerGame'
        ).get_data_frames()[0]
        
        # Get player season totals from Basketball Reference
        bref_stats = pd.DataFrame(
            bref_client.players_season_totals(season_end_year=self.season_year)
        )
        
        # Convert team enum to string
        bref_stats['team'] = bref_stats['team'].apply(lambda x: x.value if x else None)
        
        # Print column names for debugging
        print("Basketball Reference player columns:", bref_stats.columns.tolist())
        print("NBA API player columns:", nba_stats.columns.tolist())
        
        # Merge the data
        player_stats = pd.merge(
            bref_stats,
            nba_stats,
            left_on=['name', 'team'],
            right_on=['PLAYER_NAME', 'TEAM_ABBREVIATION'],
            how='outer'
        )
        
        return player_stats
    
    async def get_odds_data(self) -> Dict:
        """Collect current odds data from The Odds API using httpx."""
        url = f"{self.base_url_odds}/sports/basketball_nba/odds"
        params = {
            "apiKey": self.odds_api_key,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "decimal"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json() if response.status_code == 200 else {}
    
    def get_injuries_and_lineups(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Collect current injuries and lineup data from NBA API."""
        # This would typically use additional NBA API endpoints
        # For now, returning empty DataFrames
        return pd.DataFrame(), pd.DataFrame()

class NBAAnalyzer:
    """Analyzes collected NBA data and generates predictions."""
    
    def __init__(self, data_collector: NBADataCollector):
        self.data_collector = data_collector
        self.team_stats: Optional[pd.DataFrame] = None
        self.player_stats: Optional[pd.DataFrame] = None
        self.odds_data: Optional[Dict] = None
        self.injuries: Optional[pd.DataFrame] = None
        self.lineups: Optional[pd.DataFrame] = None
    
    async def update_data(self):
        """Update all data from sources."""
        self.team_stats = self.data_collector.get_team_stats()
        self.player_stats = self.data_collector.get_player_stats()
        self.odds_data = await self.data_collector.get_odds_data()
        self.injuries, self.lineups = self.data_collector.get_injuries_and_lineups()
    
    def calculate_pace_factors(self) -> pd.DataFrame:
        """Calculate pace factors for each team."""
        if self.team_stats is None:
            raise ValueError("Team stats not loaded. Call update_data() first.")
        
        pace_factors = self.team_stats[['team', 'PACE', 'POSS']].copy()
        return pace_factors
    
    def calculate_efficiency_metrics(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Calculate efficiency metrics for teams and players."""
        if self.team_stats is None or self.player_stats is None:
            raise ValueError("Stats not loaded. Call update_data() first.")
        
        # Team efficiency metrics
        team_efficiency = self.team_stats[[
            'team', 'OFF_RATING', 'DEF_RATING', 'NET_RATING',
            'AST_PCT', 'AST_TO', 'AST_RATIO'
        ]].copy()
        
        # Player efficiency metrics
        player_efficiency = self.player_stats[[
            'name', 'team', 'PIE', 'USG_PCT',
            'OFF_RATING', 'DEF_RATING', 'NET_RATING'
        ]].copy()
        
        return team_efficiency, player_efficiency
    
    def simulate_game(self, team1: str, team2: str, n_simulations: int = 10000) -> Dict[str, Any]:
        """
        Simulate a game between two teams n times.
        
        Args:
            team1: Name of first team
            team2: Name of second team
            n_simulations: Number of simulations to run (default: 10000)
            
        Returns:
            Dictionary containing simulation results and probabilities
        """
        if self.team_stats is None:
            raise ValueError("Team stats not loaded. Call update_data() first.")
        
        # Get team stats for simulation
        team1_stats = self.team_stats[self.team_stats['team'] == team1].iloc[0]
        team2_stats = self.team_stats[self.team_stats['team'] == team2].iloc[0]
        
        # Run Monte Carlo simulation
        team1_scores = []
        team2_scores = []
        
        for _ in range(n_simulations):
            # Simulate game based on team offensive and defensive ratings
            pace = np.mean([team1_stats['PACE'], team2_stats['PACE']])
            team1_score = np.random.normal(
                team1_stats['OFF_RATING'] * pace / 100,
                team1_stats['NET_RATING'].std()
            )
            team2_score = np.random.normal(
                team2_stats['OFF_RATING'] * pace / 100,
                team2_stats['NET_RATING'].std()
            )
            
            team1_scores.append(team1_score)
            team2_scores.append(team2_score)
        
        # Calculate probabilities and average scores
        team1_wins = sum(t1 > t2 for t1, t2 in zip(team1_scores, team2_scores))
        
        return {
            "team1_win_prob": team1_wins / n_simulations,
            "team2_win_prob": 1 - (team1_wins / n_simulations),
            "average_score": {
                "team1": np.mean(team1_scores),
                "team2": np.mean(team2_scores)
            }
        }

def save_to_excel(data: Dict[str, Optional[pd.DataFrame]], filename: str):
    """Save collected data to Excel file."""
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for sheet_name, df in data.items():
            if df is not None:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

async def main():
    # Load environment variables
    load_dotenv()
    
    # Load environment variables (API keys, etc.)
    odds_api_key = os.getenv("ODDS_API_KEY")
    if not odds_api_key:
        raise ValueError("ODDS_API_KEY environment variable not set")
    
    # Initialize collector and analyzer
    collector = NBADataCollector(odds_api_key)
    analyzer = NBAAnalyzer(collector)
    
    # Update data
    await analyzer.update_data()
    
    # Calculate additional metrics
    pace_factors = analyzer.calculate_pace_factors()
    team_efficiency, player_efficiency = analyzer.calculate_efficiency_metrics()
    
    # Prepare data for Excel
    current_date = datetime.now().strftime("%Y%m%d")
    data_to_save: Dict[str, Optional[pd.DataFrame]] = {
        "team_stats": analyzer.team_stats,
        "player_stats": analyzer.player_stats,
        "pace_factors": pace_factors,
        "team_efficiency": team_efficiency,
        "player_efficiency": player_efficiency
    }
    
    # Save to Excel
    save_to_excel(data_to_save, f"nba_stats_{current_date}.xlsx")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
