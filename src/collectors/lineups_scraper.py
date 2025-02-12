"""
Module for collecting NBA lineup data from rotowire.com.
"""

import logging
from typing import Dict, List, Optional, Union

import pandas as pd
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NBALineupScraper:
    """Scraper for NBA lineup data from rotowire.com."""
    
    BASE_URL = "https://www.rotowire.com/basketball/nba-lineups.php"
    TIMEOUT = 20  # seconds
    
    def __init__(self):
        """Initialize the scraper with a configured Chrome WebDriver."""
        logger.info("Initializing NBALineupScraper...")
        self.driver = self._setup_driver()
    
    def _setup_driver(self) -> webdriver.Chrome:
        """Set up and configure Chrome WebDriver with appropriate options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.implicitly_wait(10)
            logger.info("Chrome WebDriver initialized successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def __del__(self):
        """Clean up resources when the scraper is destroyed."""
        if hasattr(self, 'driver'):
            logger.info("Closing Chrome WebDriver...")
            self.driver.quit()
    
    def _get_page_content(self) -> Optional[str]:
        """
        Get the page content and wait for dynamic content to load.
        
        Returns:
            The page HTML content if successful, None otherwise
        """
        try:
            logger.info(f"Fetching content from {self.BASE_URL}")
            self.driver.get(self.BASE_URL)
            
            # Wait for the lineup content to load
            WebDriverWait(self.driver, self.TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "lineup"))
            )
            
            content = self.driver.page_source
            logger.info(f"Successfully retrieved content ({len(content)} bytes)")
            return content
            
        except Exception as e:
            logger.error(f"Error fetching page content: {e}")
            return None
    
    def _extract_team_name(self, team_elem: Tag) -> Optional[str]:
        """Extract team name from team element."""
        try:
            # Try to get team name from the logo alt text
            logo = team_elem.select_one('img.lineup__logo')
            if logo and 'alt' in logo.attrs:
                return str(logo['alt'])
            
            # Fallback to team abbreviation from depth chart link
            href = team_elem.get('href', '')
            if href and 'depth-charts' in href:
                parts = href.split('/')
                if len(parts) >= 2:
                    return parts[-2].split('-')[0].upper()
            
            return None
        except Exception as e:
            logger.warning(f"Error extracting team name: {e}")
            return None
    
    def _parse_lineup_section(self, section: Union[BeautifulSoup, Tag]) -> Optional[Dict[str, pd.DataFrame]]:
        """
        Parse a lineup section for a single game.
        
        Args:
            section: BeautifulSoup object or Tag containing the lineup section
            
        Returns:
            Dictionary with 'away' and 'home' DataFrames containing lineup information
        """
        try:
            # Get team names
            teams = section.select('.lineup__team')
            if len(teams) != 2:
                logger.warning("Could not find both teams in section")
                return None
                
            away_team = self._extract_team_name(teams[0])
            home_team = self._extract_team_name(teams[1])
            
            if not away_team or not home_team:
                logger.warning("Could not extract team names")
                return None
            
            # Get lineup box
            lineup_box = section.select_one('.lineup__box')
            if not lineup_box:
                logger.warning("Could not find lineup box")
                return None
            
            # Find player lists
            player_lists = lineup_box.select('.lineup__list')
            if len(player_lists) != 2:
                logger.warning("Could not find player lists for both teams")
                return None
                
            lineups = {}
            
            # Parse each team's lineup
            for team_name, player_list in zip([away_team, home_team], player_lists):
                players = []
                player_rows = player_list.select('.lineup__player')
                
                for player_row in player_rows:
                    try:
                        # Extract player info
                        pos_elem = player_row.select_one('.lineup__pos')
                        name_elem = player_row.select_one('a')
                        injury_elem = player_row.select_one('.lineup__inj')
                        
                        if name_elem and pos_elem:
                            name = name_elem.get('title', '').strip()
                            position = pos_elem.get_text(strip=True)
                            status = injury_elem.get_text(strip=True) if injury_elem else 'Active'
                            
                            # Get play probability from class
                            prob_class = [c for c in player_row.get('class', []) if 'is-pct-play-' in c]
                            probability = int(prob_class[0].split('-')[-1]) if prob_class else 100
                            
                            players.append({
                                'name': name,
                                'position': position,
                                'status': status,
                                'probability': probability,
                                'team': team_name
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error parsing player in {team_name} lineup: {e}")
                        continue
                
                if players:
                    lineups[team_name] = pd.DataFrame(players)
                else:
                    logger.warning(f"No players found for {team_name}")
            
            return lineups if len(lineups) == 2 else None
            
        except Exception as e:
            logger.error(f"Error parsing lineup section: {e}")
            return None
    
    def get_lineups(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Get current NBA lineups for all games.
        
        Returns:
            Dictionary mapping game identifiers to dictionaries containing
            'away' and 'home' lineup DataFrames
        """
        content = self._get_page_content()
        if not content:
            return {}
        
        lineups = {}
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all game sections
        game_sections = soup.select('.lineup.is-nba:not(.lineup--postponed)')
        logger.info(f"Found {len(game_sections)} game sections")
        
        for section in game_sections:
            try:
                # Get game time
                time_elem = section.select_one('.lineup__time')
                game_time = time_elem.get_text(strip=True) if time_elem else 'TBD'
                
                # Get teams
                teams = section.select('.lineup__team')
                if len(teams) != 2:
                    continue
                    
                away_team = self._extract_team_name(teams[0])
                home_team = self._extract_team_name(teams[1])
                
                if not away_team or not home_team:
                    continue
                
                game_id = f"{away_team}@{home_team} ({game_time})"
                
                # Parse lineups
                game_lineups = self._parse_lineup_section(section)
                if game_lineups:
                    lineups[game_id] = game_lineups
                
            except Exception as e:
                logger.error(f"Error processing game section: {e}")
                continue
        
        logger.info(f"Successfully scraped lineups for {len(lineups)} games")
        return lineups 