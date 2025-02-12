"""
Historical NBA data collection script using Basketball Reference Web Scraper.
"""
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import concurrent.futures
from functools import lru_cache

import pandas as pd
from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType, Team
from tqdm import tqdm

from src.cleaning.data_cleaner import NBADataCleaner
from src.cleaning.validate_data import DataValidator
from src.database.manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Data storage paths
DATA_DIR = Path("data/historical")
DATA_DIR.mkdir(parents=True, exist_ok=True)

class DataCollector:
    """Collector for NBA data using Basketball Reference."""
    
    def __init__(self, start_season: int = 2012, end_season: int = 2025, max_workers: int = 4):
        """Initialize the collector with season range."""
        self.start_season = start_season
        self.end_season = end_season
        self.seasons = list(range(start_season, end_season + 1))
        self.max_workers = max_workers
        
        # Rate limiting parameters adjusted for parallel processing
        self.request_delay = 10   # Increased delay for parallel requests
        self.season_delay = 20   # Keep 20 seconds between seasons
        self.last_request_time = 0
        
        # Batch size for parallel processing
        self.batch_size = 250  # Process 250 games at a time
        
        # Initialize data processors
        self.cleaner = NBADataCleaner()
        self.validator = DataValidator(DATA_DIR)
        self.db_manager = DatabaseManager()
    
    @lru_cache(maxsize=128)
    def _get_team_id(self, name: str) -> Optional[str]:
        """Cached team ID lookup."""
        return super()._get_team_id(name)

    def wait_for_rate_limit(self):
        """Wait appropriate time for rate limiting."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.request_delay:
            sleep_time = self.request_delay - elapsed + random.uniform(0.5, 1.5)  # Reduced random delay
            logger.info(f"Rate limiting: sleeping for {sleep_time:.1f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def collect_season_schedule(self, season: int) -> pd.DataFrame:
        """Collect season schedule data."""
        try:
            self.wait_for_rate_limit()
            logger.info(f"Collecting schedule for season {season}")
            
            schedule = client.season_schedule(season_end_year=season)
            
            # Convert to DataFrame
            df = pd.DataFrame([
                {
                    'game_id': f"{game['start_time'].strftime('%Y%m%d')}_{game['away_team'].name}_{game['home_team'].name}",
                    'start_time': game['start_time'],
                    'away_team': game['away_team'].name.replace('_', ' '),
                    'home_team': game['home_team'].name.replace('_', ' '),
                    'away_team_score': game['away_team_score'],
                    'home_team_score': game['home_team_score'],
                    'season': season
                }
                for game in schedule
            ])
            
            if df.empty:
                logger.warning(f"No schedule data returned for season {season}")
            else:
                logger.info(f"Collected {len(df)} games for season {season}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error collecting schedule for season {season}: {str(e)}")
            return pd.DataFrame()
    
    def calculate_advanced_stats(self, player_stats: pd.DataFrame, team_stats: pd.DataFrame) -> pd.DataFrame:
        """Calculate advanced statistics for players."""
        # Add basic calculated stats first
        player_stats['field_goal_pct'] = player_stats['made_field_goals'] / player_stats['attempted_field_goals']
        player_stats['three_point_pct'] = player_stats['made_three_point_field_goals'] / player_stats['attempted_three_point_field_goals']
        player_stats['free_throw_pct'] = player_stats['made_free_throws'] / player_stats['attempted_free_throws']
        player_stats['total_rebounds'] = player_stats['offensive_rebounds'] + player_stats['defensive_rebounds']
        
        # Calculate True Shooting Percentage (TS%)
        player_stats['true_shooting_pct'] = player_stats['points'] / (2 * (player_stats['attempted_field_goals'] + 0.44 * player_stats['attempted_free_throws']))
        
        # Calculate Effective Field Goal Percentage (eFG%)
        player_stats['effective_fg_pct'] = (player_stats['made_field_goals'] + 0.5 * player_stats['made_three_point_field_goals']) / player_stats['attempted_field_goals']
        
        # Calculate Usage Rate
        player_stats['usage_rate'] = (
            (player_stats['attempted_field_goals'] + 0.44 * player_stats['attempted_free_throws'] + player_stats['turnovers']) * 
            (team_stats.groupby('team_name')['minutes_per_game'].mean().mean() / 5) / 
            player_stats['minutes_played']
        ) * 100
        
        # Calculate Assist Percentage
        player_stats['assist_pct'] = player_stats['assists'] / (player_stats['minutes_played'] / (team_stats.groupby('team_name')['minutes_per_game'].mean().mean() / 5) * team_stats.groupby('team_name')['field_goals_made'].mean())
        
        # Calculate Rebound Percentage
        player_stats['rebound_pct'] = player_stats['total_rebounds'] * (team_stats.groupby('team_name')['minutes_per_game'].mean().mean() / 5) / (player_stats['minutes_played'] * (team_stats.groupby('team_name')['total_rebounds'].mean()))
        
        # Calculate Steal and Block Percentages
        possessions = team_stats.groupby('team_name')['possessions'].mean()
        player_stats['steal_pct'] = player_stats['steals'] * 100 / (player_stats['minutes_played'] / (team_stats.groupby('team_name')['minutes_per_game'].mean().mean()) * possessions)
        player_stats['block_pct'] = player_stats['blocks'] * 100 / (player_stats['minutes_played'] / (team_stats.groupby('team_name')['minutes_per_game'].mean().mean()) * possessions)
        
        # Calculate Turnover Percentage
        player_stats['turnover_pct'] = player_stats['turnovers'] * 100 / (player_stats['attempted_field_goals'] + 0.44 * player_stats['attempted_free_throws'] + player_stats['turnovers'])
        
        # Calculate Offensive and Defensive Ratings (simplified versions)
        player_stats['offensive_rating'] = (player_stats['points'] * 100) / possessions
        player_stats['defensive_rating'] = (team_stats.groupby('team_name')['opponent_points'].mean() * 100) / possessions
        
        # Calculate Player Efficiency Rating (simplified version)
        player_stats['player_efficiency'] = (
            player_stats['points'] + player_stats['total_rebounds'] + player_stats['assists'] + 
            player_stats['steals'] + player_stats['blocks'] - player_stats['turnovers'] -
            (player_stats['attempted_field_goals'] - player_stats['made_field_goals']) -
            (player_stats['attempted_free_throws'] - player_stats['made_free_throws'])
        ) * (1 / player_stats['minutes_played'])
        
        # Calculate Box Plus/Minus (simplified version)
        league_avg_pts = team_stats['points_per_game'].mean()
        player_stats['box_plus_minus'] = (player_stats['points'] - (player_stats['minutes_played'] * (league_avg_pts / 48))) / player_stats['games_played']
        
        # Fill NaN values with 0 for cases where denominators were 0
        player_stats = player_stats.fillna(0)
        
        return player_stats
    
    def collect_player_stats(self, season: int) -> pd.DataFrame:
        """Collect player statistics for a season."""
        try:
            self.wait_for_rate_limit()
            logger.info(f"Collecting player stats for season {season}")
            
            # Get regular season totals
            regular_stats = client.players_season_totals(season_end_year=season)
            
            # Get advanced season totals
            self.wait_for_rate_limit()
            advanced_stats = client.players_advanced_season_totals(season_end_year=season)
            
            # Convert regular stats to DataFrame
            regular_df = pd.DataFrame([
                {
                    'player_id': f"{player['name']}_{season}",
                    'name': player['name'],
                    'team': player['team'].name.replace('_', ' ') if player['team'] else None,
                    'positions': [pos.name.replace('_', ' ') for pos in player['positions']],
                    'age': player['age'],
                    'games_played': player['games_played'],
                    'games_started': player['games_started'],
                    'minutes_played': player['minutes_played'],
                    'made_field_goals': player['made_field_goals'],
                    'attempted_field_goals': player['attempted_field_goals'],
                    'made_three_point_field_goals': player['made_three_point_field_goals'],
                    'attempted_three_point_field_goals': player['attempted_three_point_field_goals'],
                    'made_free_throws': player['made_free_throws'],
                    'attempted_free_throws': player['attempted_free_throws'],
                    'offensive_rebounds': player['offensive_rebounds'],
                    'defensive_rebounds': player['defensive_rebounds'],
                    'assists': player['assists'],
                    'steals': player['steals'],
                    'blocks': player['blocks'],
                    'turnovers': player['turnovers'],
                    'personal_fouls': player['personal_fouls'],
                    'points': player['points'],
                    'season': season
                }
                for player in regular_stats
            ])
            
            # Convert advanced stats to DataFrame
            advanced_df = pd.DataFrame([
                {
                    'player_id': f"{player['name']}_{season}",
                    'name': player['name'],
                    'team': player['team'].name.replace('_', ' ') if player['team'] else None,
                    'win_shares': player['win_shares'],
                    'offensive_win_shares': player['offensive_win_shares'],
                    'defensive_win_shares': player['defensive_win_shares'],
                    'value_over_replacement': player['value_over_replacement'],
                    'box_plus_minus': player['box_plus_minus'],
                    'offensive_box_plus_minus': player['offensive_box_plus_minus'],
                    'defensive_box_plus_minus': player['defensive_box_plus_minus'],
                    'player_efficiency_rating': player['player_efficiency_rating'],
                    'true_shooting_percentage': player['true_shooting_percentage'],
                    'total_rebound_percentage': player['total_rebound_percentage'],
                    'assist_percentage': player['assist_percentage'],
                    'steal_percentage': player['steal_percentage'],
                    'block_percentage': player['block_percentage'],
                    'turnover_percentage': player['turnover_percentage'],
                    'usage_percentage': player['usage_percentage']
                }
                for player in advanced_stats
            ])
            
            if regular_df.empty:
                logger.warning(f"No regular player stats returned for season {season}")
                return pd.DataFrame()
                
            if advanced_df.empty:
                logger.warning(f"No advanced player stats returned for season {season}")
                return regular_df
            
            # Merge regular and advanced stats
            df = pd.merge(
                regular_df,
                advanced_df,
                on=['player_id', 'name', 'team'],
                how='left'
            )
            
            # Calculate additional advanced statistics
            team_stats = self.derive_team_stats(self.collect_season_schedule(season))
            df = self.calculate_advanced_stats(df, team_stats)
            
            logger.info(f"Collected and calculated stats for {len(df)} players in season {season}")
            return df
            
        except Exception as e:
            logger.error(f"Error collecting player stats for season {season}: {str(e)}")
            return pd.DataFrame()
    
    def collect_game_box_scores(self, game_date: datetime, home_team: str, away_team: str) -> pd.DataFrame:
        """Collect box scores for a specific game."""
        try:
            self.wait_for_rate_limit()
            logger.info(f"Collecting box scores for game: {home_team} vs {away_team} on {game_date.strftime('%Y-%m-%d')}")
            
            # Get box scores from Basketball Reference
            box_scores = client.player_box_scores(
                day=game_date.day,
                month=game_date.month,
                year=game_date.year
            )
            
            # Convert box scores to DataFrame with type-safe operations
            df = pd.DataFrame([
                {
                    'game_id': f"{game_date.strftime('%Y%m%d')}_{away_team}_{home_team}",
                    'player_id': f"{box_score['name']}_{game_date.year}",
                    'name': box_score['name'],
                    'team': box_score['team'].name.replace('_', ' ') if box_score['team'] else None,
                    'is_starter': box_score.get('is_starter', False),
                    'minutes_played': float(box_score.get('minutes_played', 0)),  # Default to 0 if missing
                    
                    # Basic stats with safe type conversion
                    'field_goals_made': int(box_score.get('made_field_goals', 0)),
                    'field_goals_attempted': int(box_score.get('attempted_field_goals', 0)),
                    'three_points_made': int(box_score.get('made_three_point_field_goals', 0)),
                    'three_points_attempted': int(box_score.get('attempted_three_point_field_goals', 0)),
                    'free_throws_made': int(box_score.get('made_free_throws', 0)),
                    'free_throws_attempted': int(box_score.get('attempted_free_throws', 0)),
                    'offensive_rebounds': int(box_score.get('offensive_rebounds', 0)),
                    'defensive_rebounds': int(box_score.get('defensive_rebounds', 0)),
                    'total_rebounds': int(box_score.get('offensive_rebounds', 0)) + int(box_score.get('defensive_rebounds', 0)),
                    'assists': int(box_score.get('assists', 0)),
                    'steals': int(box_score.get('steals', 0)),
                    'blocks': int(box_score.get('blocks', 0)),
                    'turnovers': int(box_score.get('turnovers', 0)),
                    'personal_fouls': int(box_score.get('personal_fouls', 0)),
                    'points': int(box_score.get('points', 0)),
                    'game_date': game_date
                }
                for box_score in box_scores
                if box_score['team'] and box_score['team'].name.replace('_', ' ') in [home_team, away_team]
            ])
            
            if df.empty:
                logger.warning(f"No box scores found for game: {home_team} vs {away_team}")
                return pd.DataFrame()
            
            # Calculate shooting percentages and advanced stats
            df = self.calculate_game_advanced_stats(df)
            
            logger.info(f"Collected {len(df)} player box scores for game: {home_team} vs {away_team}")
            return df
            
        except Exception as e:
            logger.error(f"Error collecting box scores for game {home_team} vs {away_team}: {str(e)}")
            return pd.DataFrame()

    def calculate_game_advanced_stats(self, box_scores: pd.DataFrame) -> pd.DataFrame:
        """Calculate advanced statistics for a single game's box scores."""
        # Calculate basic percentages
        box_scores['field_goal_pct'] = box_scores['field_goals_made'] / box_scores['field_goals_attempted']
        box_scores['three_point_pct'] = box_scores['three_points_made'] / box_scores['three_points_attempted']
        box_scores['free_throw_pct'] = box_scores['free_throws_made'] / box_scores['free_throws_attempted']
        
        # Calculate True Shooting Percentage (TS%)
        box_scores['true_shooting_pct'] = box_scores['points'] / (2 * (box_scores['field_goals_attempted'] + 0.44 * box_scores['free_throws_attempted']))
        
        # Calculate Effective Field Goal Percentage (eFG%)
        box_scores['effective_fg_pct'] = (box_scores['field_goals_made'] + 0.5 * box_scores['three_points_made']) / box_scores['field_goals_attempted']
        
        # Calculate Usage Rate (simplified for single game)
        team_stats = box_scores.groupby('team').agg({
            'field_goals_attempted': 'sum',
            'free_throws_attempted': 'sum',
            'turnovers': 'sum',
            'minutes_played': 'sum'
        }).astype(float)  # Ensure numeric types
        
        for team in box_scores['team'].unique():
            team_mask = box_scores['team'] == team
            team_data = team_stats.loc[team]
            
            # Calculate individual usage rates with explicit numeric conversion
            fga = pd.to_numeric(box_scores.loc[team_mask, 'field_goals_attempted'], errors='coerce')
            fta = pd.to_numeric(box_scores.loc[team_mask, 'free_throws_attempted'], errors='coerce')
            tov = pd.to_numeric(box_scores.loc[team_mask, 'turnovers'], errors='coerce')
            min_played = pd.to_numeric(box_scores.loc[team_mask, 'minutes_played'], errors='coerce')
            
            box_scores.loc[team_mask, 'usage_rate'] = (
                (fga + 0.44 * fta + tov) * 
                (float(team_data['minutes_played']) / 5) / 
                min_played
            ) * 100
        
        # Calculate Game Score (John Hollinger's metric)
        box_scores['game_score'] = (
            box_scores['points'] + 
            0.4 * box_scores['field_goals_made'] - 
            0.7 * box_scores['field_goals_attempted'] - 
            0.4 * (box_scores['free_throws_attempted'] - box_scores['free_throws_made']) +
            0.7 * box_scores['offensive_rebounds'] +
            0.3 * box_scores['defensive_rebounds'] +
            box_scores['steals'] +
            0.7 * box_scores['assists'] +
            0.7 * box_scores['blocks'] -
            0.4 * box_scores['personal_fouls'] -
            box_scores['turnovers']
        )
        
        # Fill NaN values with 0
        box_scores = box_scores.fillna(0)
        
        return box_scores
    
    def collect_game_box_scores_parallel(self, games: List[Dict]) -> List[pd.DataFrame]:
        """Collect box scores for multiple games in parallel."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for game in games:
                futures.append(
                    executor.submit(
                        self.collect_game_box_scores,
                        game_date=game['start_time'],
                        home_team=game['home_team'],
                        away_team=game['away_team']
                    )
                )
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    box_scores = future.result()
                    if not box_scores.empty:
                        results.append(box_scores)
                except Exception as e:
                    logger.error(f"Error collecting box scores: {str(e)}")
            
            return results

    def collect_season_data(self, season: int) -> Dict[str, pd.DataFrame]:
        """Collect all data for a specific season using parallel processing."""
        season_data = {}
        
        # Collect schedule data
        schedule_df = self.collect_season_schedule(season)
        if not schedule_df.empty:
            season_data['schedule'] = schedule_df
            
            # Process games in parallel batches
            all_box_scores = []
            games = schedule_df.to_dict('records')
            total_games = len(games)
            total_batches = (total_games + self.batch_size - 1) // self.batch_size
            
            logger.info(f"\nProcessing {total_games} games in {total_batches} batches of {self.batch_size} games each")
            logger.info(f"Using {self.max_workers} parallel workers")
            
            for batch_num, i in enumerate(range(0, total_games, self.batch_size), 1):
                batch = games[i:i + self.batch_size]
                logger.info(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} games)")
                
                # Collect box scores in parallel
                batch_scores = self.collect_game_box_scores_parallel(batch)
                
                if batch_scores:
                    all_box_scores.extend(batch_scores)
                    logger.info(f"Batch {batch_num} complete: collected {sum(len(df) for df in batch_scores)} box scores")
                
                # Add longer delay between batches
                if batch_num < total_batches:
                    logger.info(f"Waiting {self.request_delay} seconds before next batch...")
                    time.sleep(self.request_delay)
                
                # Log overall progress
                games_processed = min(i + self.batch_size, total_games)
                progress = (games_processed / total_games) * 100
                total_box_scores = sum(len(df) for df in all_box_scores)
                logger.info(f"Overall Progress: {progress:.1f}% - {games_processed}/{total_games} games processed - {total_box_scores} total box scores collected")
            
            if all_box_scores:
                season_data['box_scores'] = pd.concat(all_box_scores, ignore_index=True)
                logger.info(f"\nBox score collection complete: {len(season_data['box_scores'])} total box scores collected")
        
        # Collect player and team stats (these are relatively quick)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            player_future = executor.submit(self.collect_player_stats, season)
            team_future = executor.submit(self.derive_team_stats, schedule_df)
            
            player_df = player_future.result()
            if not player_df.empty:
                season_data['player_stats'] = player_df
            
            team_stats = team_future.result()
            if not team_stats.empty:
                season_data['team_stats'] = team_stats
        
        return season_data
    
    def derive_team_stats(self, schedule_df: pd.DataFrame) -> pd.DataFrame:
        """Derive team statistics from schedule data."""
        # Get unique teams and initialize stats
        all_teams = pd.concat([
            schedule_df['home_team'],
            schedule_df['away_team']
        ]).unique()
        
        team_stats = []
        
        for team in all_teams:
            # Home games
            home_games = schedule_df[schedule_df['home_team'] == team]
            home_wins = home_games[home_games['home_team_score'] > home_games['away_team_score']]
            
            # Away games
            away_games = schedule_df[schedule_df['away_team'] == team]
            away_wins = away_games[away_games['away_team_score'] > away_games['home_team_score']]
            
            # Basic stats
            games_played = len(home_games) + len(away_games)
            wins = len(home_wins) + len(away_wins)
            losses = games_played - wins
            
            # Scoring
            points_scored = (
                home_games['home_team_score'].sum() +
                away_games['away_team_score'].sum()
            )
            points_allowed = (
                home_games['away_team_score'].sum() +
                away_games['home_team_score'].sum()
            )
            
            # Per game averages
            points_per_game = points_scored / games_played if games_played > 0 else 0
            points_allowed_per_game = points_allowed / games_played if games_played > 0 else 0
            
            # Advanced stats
            possessions = games_played * 100  # Average possessions per game
            pace = possessions / games_played if games_played > 0 else 0
            offensive_rating = (points_scored / possessions) * 100 if possessions > 0 else 0
            defensive_rating = (points_allowed / possessions) * 100 if possessions > 0 else 0
            net_rating = offensive_rating - defensive_rating
            
            # Four Factors (using league averages as estimates)
            shooting_pct = 0.47  # League average eFG%
            turnover_rate = 0.13  # League average TOV%
            offensive_rebound_rate = 0.28  # League average ORB%
            free_throw_rate = 0.19  # League average FT/FGA
            
            # Strength of Schedule
            opponent_win_pct = 0.5  # Will be calculated based on opponents' records
            home_games_remaining = 41 - len(home_games)  # Standard 82-game season
            away_games_remaining = 41 - len(away_games)
            
            # Advanced shooting stats
            true_shooting_pct = points_scored / (2 * (shooting_pct * points_scored + 0.44 * free_throw_rate * points_scored))
            effective_fg_pct = shooting_pct + (0.5 * 0.35)  # Adding bonus for three-pointers
            
            # Per game stats
            minutes_per_game = 240  # 5 players * 48 minutes
            rebounds_per_game = 42  # League average
            assists_per_game = 24   # League average
            steals_per_game = 8     # League average
            blocks_per_game = 5     # League average
            turnovers_per_game = 14 # League average
            fouls_per_game = 20     # League average
            
            team_stats.append({
                'team_name': team,
                'games_played': games_played,
                'wins': wins,
                'losses': losses,
                'win_pct': wins / games_played if games_played > 0 else 0,
                
                # Basic stats
                'points_scored': points_scored,
                'points_allowed': points_allowed,
                'points_per_game': points_per_game,
                'points_allowed_per_game': points_allowed_per_game,
                
                # Advanced stats
                'possessions': possessions,
                'pace': pace,
                'offensive_rating': offensive_rating,
                'defensive_rating': defensive_rating,
                'net_rating': net_rating,
                
                # Four Factors
                'effective_fg_pct': effective_fg_pct,
                'turnover_pct': turnover_rate,
                'offensive_rebound_pct': offensive_rebound_rate,
                'free_throw_rate': free_throw_rate,
                
                # Strength of Schedule
                'strength_of_schedule': opponent_win_pct,
                'home_games_remaining': home_games_remaining,
                'away_games_remaining': away_games_remaining,
                
                # Advanced shooting
                'true_shooting_pct': true_shooting_pct,
                
                # Per game stats
                'minutes_per_game': minutes_per_game,
                'rebounds_per_game': rebounds_per_game,
                'assists_per_game': assists_per_game,
                'steals_per_game': steals_per_game,
                'blocks_per_game': blocks_per_game,
                'turnovers_per_game': turnovers_per_game,
                'fouls_per_game': fouls_per_game,
                
                # Season identifier
                'season': schedule_df['season'].iloc[0]
            })
        
        return pd.DataFrame(team_stats)
    
    def save_season_data(self, season: int, data: Dict[str, pd.DataFrame], is_cleaned: bool = False):
        """Save collected or cleaned data for a season."""
        # Determine the correct directory based on whether the data is cleaned
        base_dir = "season_" + str(season)
        if is_cleaned:
            base_dir += "_cleaned"
        season_dir = DATA_DIR / base_dir
        season_dir.mkdir(exist_ok=True)
        
        for name, df in data.items():
            if not df.empty:
                file_path = season_dir / f"{name}.parquet"
                df.to_parquet(file_path)
                logger.info(f"Saved {name} data to {file_path}")
            else:
                logger.warning(f"Skipping empty dataset: {name} for season {season}")
    
    def process_season(self, season: int) -> bool:
        """Process a single season: collect, validate, clean, and load to database."""
        try:
            # Step 1: Collect Data
            logger.info(f"\nCollecting data for season {season}")
            season_data = self.collect_season_data(season)
            if not season_data:
                logger.error(f"Failed to collect data for season {season}")
                return False
            
            # Save raw data
            self.save_season_data(season, season_data, is_cleaned=False)
            
            # Step 2: Clean Data
            logger.info(f"\nCleaning data for season {season}")
            cleaned_data = self.cleaner.clean_season_data(DATA_DIR / f"season_{season}")
            if not cleaned_data:
                logger.error(f"Failed to clean data for season {season}")
                return False
            
            # Save cleaned data
            self.save_season_data(season, cleaned_data, is_cleaned=True)
            
            # Step 3: Validate Data
            logger.info(f"\nValidating data for season {season}")
            validation_results = self.validator.run_validation()
            if any(validation_results.get('errors', [])):
                logger.error(f"Data validation failed for season {season}")
                return False
            
            # Step 4: Load to Database
            logger.info(f"\nLoading season {season} to database")
            self.db_manager.load_season_data(DATA_DIR / f"season_{season}_cleaned")
            logger.info(f"Successfully processed season {season}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing season {season}: {str(e)}")
            return False
    
    def collect_all_seasons(self):
        """Collect and process data for all specified seasons in parallel."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_season, season): season for season in self.seasons}
            
            for future in concurrent.futures.as_completed(futures):
                season = futures[future]
                try:
                    success = future.result()
                    if success:
                        logger.info(f"Successfully processed season {season}")
                        time.sleep(self.season_delay)
                    else:
                        logger.error(f"Failed to process season {season}")
                except Exception as e:
                    logger.error(f"Error processing season {season}: {str(e)}")

def main():
    """Main function to run the data collection process."""
    collector = DataCollector()
    collector.collect_all_seasons()

if __name__ == "__main__":
    main() 