import os
import time
from pathlib import Path
from typing import Any, Dict

from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import Team
from prometheus_client import Counter, Gauge
from redis import Redis
from rq import Connection, Worker

from src.monitoring.metrics import (
    BATCH_PROCESSING_TIME,
    BOX_SCORES_COLLECTED,
    COLLECTION_ERRORS,
    GAMES_COLLECTED,
)

# Prometheus metrics
SCRAPE_COUNTER = Counter('nba_scrapes_total', 'Total number of scraping operations', ['task_type'])
SCRAPE_DURATION = Gauge('nba_scrape_duration_seconds', 'Time spent scraping', ['task_type'])
ERROR_COUNTER = Counter('nba_scrape_errors_total', 'Total number of scraping errors', ['task_type', 'error_type'])

class ScraperWorker:
    def __init__(self):
        self.redis_conn = Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', None)
        )
        self.data_dir = Path("data/historical")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def process_team_stats_task(self, team: Team, start_season: int, end_season: int) -> Dict[str, Any]:
        """Process historical stats collection for a single team"""
        try:
            start_time = time.time()
            SCRAPE_COUNTER.labels(task_type='team_stats').inc()
            
            team_data = {
                'team': team.name,
                'seasons': {}
            }
            
            for season in range(start_season, end_season + 1):
                print(f"Processing {team.name} for season {season}")
                season_data = {}
                
                # Get team schedule for the season
                schedule = client.season_schedule(season_end_year=season)
                team_games = [
                    game for game in schedule 
                    if game['home_team'] == team or game['away_team'] == team
                ]
                season_data['schedule'] = team_games
                
                # Get box scores for each game
                season_box_scores = []
                for game in team_games:
                    try:
                        box_score = client.regular_season_player_box_scores(
                            game['start_time'].date(),
                            game['home_team'],
                            game['away_team']
                        )
                        season_box_scores.append(box_score)
                        time.sleep(1)  # Be nice to the API
                    except Exception as e:
                        ERROR_COUNTER.labels(
                            task_type='box_score',
                            error_type=type(e).__name__
                        ).inc()
                season_data['box_scores'] = season_box_scores
                
                # Get player season stats
                try:
                    # Core player stats
                    player_stats = client.players_season_totals(season_end_year=season)
                    team_player_stats = [
                        stats for stats in player_stats 
                        if stats['team'] == team
                    ]
                    season_data['player_stats'] = team_player_stats
                    
                    # Advanced player stats using nba_api
                    from nba_api.stats.endpoints import playerestimatedmetrics
                    from nba_api.stats.library.parameters import SeasonType
                    
                    season_str = f"{season}-{str(season + 1)[-2:]}"
                    advanced_stats = playerestimatedmetrics.PlayerEstimatedMetrics(
                        season=season_str,
                        season_type=SeasonType.regular
                    ).get_normalized_dict()
                    
                    # Filter for team's players and combine with core stats
                    team_advanced_stats = []
                    for player in team_player_stats:
                        player_name = f"{player['name']}"
                        for adv_stat in advanced_stats['PlayerEstimatedMetrics']:
                            if player_name.lower() in adv_stat['PLAYER_NAME'].lower():
                                team_advanced_stats.append({
                                    'player_name': player_name,
                                    'e_off_rating': adv_stat['E_OFF_RATING'],
                                    'e_def_rating': adv_stat['E_DEF_RATING'],
                                    'e_net_rating': adv_stat['E_NET_RATING'],
                                    'e_ast_ratio': adv_stat['E_AST_RATIO'],
                                    'e_oreb_pct': adv_stat['E_OREB_PCT'],
                                    'e_dreb_pct': adv_stat['E_DREB_PCT'],
                                    'e_reb_pct': adv_stat['E_REB_PCT'],
                                    'e_tm_tov_pct': adv_stat['E_TM_TOV_PCT'],
                                    'e_usg_pct': adv_stat['E_USG_PCT'],
                                    'e_pace': adv_stat['E_PACE'],
                                })
                                break
                    
                    season_data['player_advanced_stats'] = team_advanced_stats
                    time.sleep(1)  # Be nice to the API
                    
                except Exception as e:
                    ERROR_COUNTER.labels(
                        task_type='player_stats',
                        error_type=type(e).__name__
                    ).inc()
                    print(f"Error collecting player stats for {team.name} {season}: {e}")
                
                team_data['seasons'][season] = season_data
                
                # Save data after each season
                season_file = self.data_dir / f"{team.name.lower()}_{season}.json"
                import json
                with open(season_file, 'w') as f:
                    json.dump(season_data, f)
                
                print(f"Completed {team.name} for season {season}")
            
            SCRAPE_DURATION.labels(task_type='team_stats').set(time.time() - start_time)
            
            return {
                'team': team.name,
                'seasons_processed': end_season - start_season + 1,
                'games_collected': sum(len(s['schedule']) for s in team_data['seasons'].values()),
                'box_scores_collected': sum(len(s['box_scores']) for s in team_data['seasons'].values()),
                'players_collected': sum(len(s.get('player_stats', [])) for s in team_data['seasons'].values()),
                'advanced_stats_collected': sum(len(s.get('player_advanced_stats', [])) for s in team_data['seasons'].values()),
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            ERROR_COUNTER.labels(task_type='team_stats', error_type=type(e).__name__).inc()
            raise

    def process_season_task(self, season: int) -> Dict[str, Any]:
        """Process a single season's data collection"""
        try:
            start_time = time.time()
            
            # Collect season data
            season_data = self.collector.collect_season_data(season)
            
            # Update metrics
            if 'schedule' in season_data:
                GAMES_COLLECTED.inc(len(season_data['schedule']))
            if 'box_scores' in season_data:
                BOX_SCORES_COLLECTED.inc(len(season_data['box_scores']))
            
            # Save the data
            self.collector.save_season_data(season, season_data)
            
            # Clean and validate the data
            cleaned_data = self.collector.cleaner.clean_season_data(
                self.data_dir / f"season_{season}"
            )
            self.collector.save_season_data(season, cleaned_data, is_cleaned=True)
            
            # Record processing time
            BATCH_PROCESSING_TIME.observe(time.time() - start_time)
            
            return {
                'season': season,
                'games_collected': len(season_data.get('schedule', [])),
                'box_scores_collected': len(season_data.get('box_scores', [])),
                'players_collected': len(season_data.get('player_stats', [])),
                'teams_collected': len(season_data.get('team_stats', [])),
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            COLLECTION_ERRORS.labels(error_type=type(e).__name__).inc()
            raise

    def process_box_scores_task(self, date_str: str) -> Dict[str, Any]:
        """Process box scores for a specific date"""
        try:
            start_time = time.time()
            
            # Parse date string to datetime
            from datetime import datetime
            game_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Get schedule for the date
            schedule = self.collector.collect_season_schedule(game_date.year)
            games = schedule[schedule['start_time'].dt.date == game_date.date()]
            
            # Collect box scores
            all_box_scores = []
            for _, game in games.iterrows():
                box_scores = self.collector.collect_game_box_scores(
                    game['start_time'],
                    game['home_team'],
                    game['away_team']
                )
                if not box_scores.empty:
                    all_box_scores.append(box_scores)
            
            # Update metrics
            if all_box_scores:
                total_box_scores = sum(len(df) for df in all_box_scores)
                BOX_SCORES_COLLECTED.inc(total_box_scores)
            
            BATCH_PROCESSING_TIME.observe(time.time() - start_time)
            
            return {
                'date': date_str,
                'games_processed': len(games),
                'box_scores_collected': sum(len(df) for df in all_box_scores),
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            COLLECTION_ERRORS.labels(error_type=type(e).__name__).inc()
            raise

    def process_lineups_task(self, **params):
        """Process lineup scraping task"""
        try:
            start_time = time.time()
            SCRAPE_COUNTER.labels(task_type='lineups').inc()
            
            from src.collectors.lineups_scraper import LineupsCollector
            collector = LineupsCollector()
            result = collector.get_lineups()
            
            SCRAPE_DURATION.labels(task_type='lineups').set(time.time() - start_time)
            return result
            
        except Exception as e:
            ERROR_COUNTER.labels(task_type='lineups', error_type=type(e).__name__).inc()
            raise

    def process_odds_task(self, **params):
        """Process odds scraping task"""
        try:
            start_time = time.time()
            SCRAPE_COUNTER.labels(task_type='odds').inc()
            
            from src.collectors.odds_api import OddsAPICollector
            api_key = os.getenv('ODDS_API_KEY')
            if not api_key:
                raise ValueError("ODDS_API_KEY environment variable is required")
            collector = OddsAPICollector(api_key=api_key)
            result = collector.get_nba_odds()
            
            SCRAPE_DURATION.labels(task_type='odds').set(time.time() - start_time)
            return result
            
        except Exception as e:
            ERROR_COUNTER.labels(task_type='odds', error_type=type(e).__name__).inc()
            raise

    def process_stats_task(self, **params):
        """Process NBA stats scraping task"""
        try:
            start_time = time.time()
            SCRAPE_COUNTER.labels(task_type='stats').inc()
            
            from src.collectors.nba_api import (
                get_player_advanced_stats,
                get_team_advanced_stats,
            )
            result = {
                'team_stats': get_team_advanced_stats(),
                'player_stats': get_player_advanced_stats()
            }
            
            SCRAPE_DURATION.labels(task_type='stats').set(time.time() - start_time)
            return result
            
        except Exception as e:
            ERROR_COUNTER.labels(task_type='stats', error_type=type(e).__name__).inc()
            raise

def main():
    """Main worker function."""
    with Connection():
        worker = Worker(['default'])
        worker.work()

if __name__ == '__main__':
    main() 