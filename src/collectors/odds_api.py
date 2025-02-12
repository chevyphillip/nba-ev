"""
Module for collecting data from The Odds API.
"""

from typing import Dict, Optional

import httpx


class OddsAPICollector:
    """Collector for The Odds API data."""
    
    def __init__(self, api_key: str):
        """
        Initialize the collector.
        
        Args:
            api_key: API key for The Odds API
        """
        self.api_key = api_key
        self.base_url = "https://api.the-odds-api.com/v4"
    
    async def get_nba_odds(
        self,
        regions: str = "us",
        markets: str = "h2h,spreads,totals",
        odds_format: str = "decimal"
    ) -> Dict:
        """
        Collect current NBA odds data.
        
        Args:
            regions: Regions to get odds for (default: "us")
            markets: Types of bets to get odds for (default: "h2h,spreads,totals")
            odds_format: Format for odds values (default: "decimal")
            
        Returns:
            Dictionary containing current betting odds
        """
        url = f"{self.base_url}/sports/basketball_nba/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            return response.json() if response.status_code == 200 else {} 