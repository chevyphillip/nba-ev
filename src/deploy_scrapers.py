import os
from typing import Dict, List

from basketball_reference_web_scraper.data import Team
from redis import Redis

from src.workers.task_queue import TaskQueue


def deploy_team_data_collection(start_season: int = 2012, end_season: int = 2024) -> List[str]:
    """
    Deploy team data collection tasks.
    Each worker gets assigned specific teams to collect data for.
    Returns list of job IDs.
    """
    task_queue = TaskQueue()
    job_ids = []
    
    # List of all NBA teams
    teams = [
        Team.ATLANTA_HAWKS, Team.BOSTON_CELTICS, Team.BROOKLYN_NETS,
        Team.CHARLOTTE_HORNETS, Team.CHICAGO_BULLS, Team.CLEVELAND_CAVALIERS,
        Team.DALLAS_MAVERICKS, Team.DENVER_NUGGETS, Team.DETROIT_PISTONS,
        Team.GOLDEN_STATE_WARRIORS, Team.HOUSTON_ROCKETS, Team.INDIANA_PACERS,
        Team.LOS_ANGELES_CLIPPERS, Team.LOS_ANGELES_LAKERS, Team.MEMPHIS_GRIZZLIES,
        Team.MIAMI_HEAT, Team.MILWAUKEE_BUCKS, Team.MINNESOTA_TIMBERWOLVES,
        Team.NEW_ORLEANS_PELICANS, Team.NEW_YORK_KNICKS, Team.OKLAHOMA_CITY_THUNDER,
        Team.ORLANDO_MAGIC, Team.PHILADELPHIA_76ERS, Team.PHOENIX_SUNS,
        Team.PORTLAND_TRAIL_BLAZERS, Team.SACRAMENTO_KINGS, Team.SAN_ANTONIO_SPURS,
        Team.TORONTO_RAPTORS, Team.UTAH_JAZZ, Team.WASHINGTON_WIZARDS
    ]
    
    print(f"Deploying team data collection tasks from {start_season} to {end_season}")
    for team in teams:
        job = task_queue.enqueue_scraping_task(
            'team_stats',
            {
                'team': team,
                'start_season': start_season,
                'end_season': end_season
            },
            timeout='24h'  # Allow 24 hours per team (lots of data to collect)
        )
        job_ids.append(job.id)
        print(f"Enqueued team {team.name} - Job ID: {job.id}")
    
    return job_ids

def deploy_live_data_collection(interval_minutes: int = 30) -> Dict[str, str]:
    """
    Deploy live data collection tasks (lineups, odds) with specified interval.
    Returns dict of task type to job ID.
    """
    task_queue = TaskQueue()
    jobs = {}
    
    # Deploy lineup scraping
    lineup_job = task_queue.enqueue_scraping_task(
        'lineups',
        {},
        timeout='24h',  # Run for 24 hours
        interval=interval_minutes * 60  # Convert to seconds
    )
    jobs['lineups'] = lineup_job.id
    print(f"Deployed lineup scraping task - Job ID: {lineup_job.id}")
    
    # Deploy odds scraping if API key is available
    if os.getenv('ODDS_API_KEY'):
        odds_job = task_queue.enqueue_scraping_task(
            'odds',
            {},
            timeout='24h',
            interval=interval_minutes * 60
        )
        jobs['odds'] = odds_job.id
        print(f"Deployed odds scraping task - Job ID: {odds_job.id}")
    else:
        print("Warning: ODDS_API_KEY not set, skipping odds scraping deployment")
    
    return jobs

def get_queue_status() -> Dict[str, int]:
    """Get current status of the task queue."""
    task_queue = TaskQueue()
    return task_queue.get_queue_status()

def main():
    """Main deployment function."""
    # Ensure Redis is available
    redis = Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        password=os.getenv('REDIS_PASSWORD')
    )
    try:
        redis.ping()
    except Exception as e:
        print(f"Error connecting to Redis: {e}")
        return
    
    print("\nStarting NBA data collection deployment...")
    
    # 1. Deploy team-based historical data collection
    print("\n1. Deploying team-based historical data collection...")
    team_jobs = deploy_team_data_collection(2012, 2024)
    print(f"Deployed {len(team_jobs)} team data collection jobs")
    
    # 2. Deploy live data collection
    print("\n2. Deploying live data collection...")
    live_jobs = deploy_live_data_collection(30)  # Every 30 minutes
    print(f"Deployed {len(live_jobs)} live data collection jobs")
    
    # 3. Print queue status
    print("\nCurrent Queue Status:")
    status = get_queue_status()
    for key, value in status.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main() 