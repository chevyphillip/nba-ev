"""
Main script for NBA statistics collection and analysis.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import pandas as pd
from dotenv import load_dotenv

from src.analysis.data_cleaning import prepare_data_for_visualization
from src.analysis.efficiency import (calculate_pace_factors,
                                     calculate_player_efficiency,
                                     calculate_team_efficiency)
from src.collectors.basketball_reference import (get_player_season_stats,
                                                 get_season_stats)
from src.collectors.nba_api import (get_player_advanced_stats,
                                    get_team_advanced_stats)
from src.collectors.odds_api import OddsAPICollector
from src.visualization.plots import create_all_visualizations


def convert_timezone_aware_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert timezone-aware datetime columns to timezone-naive.
    
    Args:
        df: DataFrame that may contain timezone-aware datetime columns
        
    Returns:
        DataFrame with timezone-naive datetime columns
    """
    df = df.copy()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns
    for col in datetime_cols:
        if hasattr(df[col].dt, 'tz') and df[col].dt.tz is not None:
            df[col] = df[col].dt.tz_localize(None)
    return df


def convert_odds_to_dataframe(odds_data: Dict) -> pd.DataFrame:
    """
    Convert odds API response to a pandas DataFrame.
    
    Args:
        odds_data: Dictionary containing odds data from the API
        
    Returns:
        DataFrame with standardized odds data
    """
    # Extract relevant fields from the odds data
    records: List[Dict] = []
    
    for game in odds_data.get('games', []):
        record = {
            'game_id': game.get('id'),
            'home_team': game.get('home_team'),
            'away_team': game.get('away_team'),
            'home_odds': game.get('home_odds'),
            'away_odds': game.get('away_odds'),
            'spread': game.get('spread'),
            'total': game.get('total')
        }
        records.append(record)
    
    return pd.DataFrame(records)


async def main():
    """Main function to run the NBA statistics collection and analysis."""
    # Load environment variables
    load_dotenv()
    
    # Get API key
    odds_api_key = os.getenv("ODDS_API_KEY")
    if not odds_api_key:
        raise ValueError("ODDS_API_KEY environment variable not set")
    
    # Initialize collectors
    odds_collector = OddsAPICollector(odds_api_key)
    
    try:
        # Collect data
        print("Collecting team statistics...")
        season_year = 2024  # Current season
        
        # Get data from different sources
        bref_team_stats = get_season_stats(season_year)
        bref_player_stats = get_player_season_stats(season_year)
        nba_team_stats = get_team_advanced_stats()
        nba_player_stats = get_player_advanced_stats()
        odds_data = await odds_collector.get_nba_odds()
        
        # Debug: Print column names
        print("\nBasketball Reference Team Stats columns:")
        print(bref_team_stats.columns.tolist())
        print("\nNBA API Team Stats columns:")
        print(nba_team_stats.columns.tolist())
        
        # Convert odds data to DataFrame
        odds_df = convert_odds_to_dataframe(odds_data) if odds_data else None
        
        # Process and merge team statistics
        team_stats = pd.merge(
            bref_team_stats,
            nba_team_stats,
            left_on='home_team',  # Changed from 'team' to 'home_team' since that's what Basketball Reference provides
            right_on='TEAM_NAME',
            how='outer'
        )
        
        # Debug: Print merged and cleaned columns
        print("\nMerged Team Stats columns before cleaning:")
        print(team_stats.columns.tolist())
        
        # Process and merge player statistics
        player_stats = pd.merge(
            bref_player_stats,
            nba_player_stats,
            left_on=['name', 'team'],  # Using renamed columns
            right_on=['name', 'team'],  # Using renamed columns
            how='outer'
        )
        
        # Clean and prepare data for analysis
        print("Cleaning and preparing data...")
        cleaned_data = prepare_data_for_visualization(
            team_stats=team_stats,
            player_stats=player_stats,
            odds_data=odds_df
        )
        
        # Debug: Print cleaned columns
        print("\nCleaned Team Stats columns:")
        print(cleaned_data['team_stats'].columns.tolist())
        
        # Calculate additional metrics
        print("Calculating efficiency metrics...")
        team_efficiency = calculate_team_efficiency(cleaned_data['team_stats'])
        player_efficiency = calculate_player_efficiency(cleaned_data['player_stats'])
        pace_factors = calculate_pace_factors(cleaned_data['team_stats'])
        
        # Prepare data for saving
        current_date = datetime.now().strftime("%Y%m%d")
        data_to_save = {
            "team_stats": cleaned_data['team_stats'],
            "player_stats": cleaned_data['player_stats'],
            "team_efficiency": team_efficiency,
            "player_efficiency": player_efficiency,
            "pace_factors": pace_factors
        }
        
        if 'odds_data' in cleaned_data:
            data_to_save['odds_data'] = cleaned_data['odds_data']
        
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Save to Excel
        print("Saving data to Excel...")
        excel_path = data_dir / f"nba_stats_{current_date}.xlsx"
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for sheet_name, df in data_to_save.items():
                # Convert timezone-aware datetime columns to timezone-naive
                df = convert_timezone_aware_columns(df)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Create visualizations
        print("Creating visualizations...")
        create_all_visualizations(data_to_save, "visualizations")
        
        print("Process completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 