import os
from typing import Any, Dict, Optional

from redis import Redis
from rq import Queue
from rq.job import Job
from rq.retry import Retry


class TaskQueue:
    def __init__(self):
        self.redis_conn = Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD', None)
        )
        self.queue = Queue('nba_scraper', connection=self.redis_conn)
        
    def enqueue_scraping_task(
        self,
        task_type: str,
        params: Dict[str, Any],
        timeout: str = '10m',
        interval: Optional[int] = None
    ) -> Job:
        """
        Enqueue a scraping task with retry logic
        
        Args:
            task_type: Type of scraping task ('lineups', 'odds', 'stats', etc.)
            params: Parameters for the specific task
            timeout: Job timeout (e.g., '10m', '24h')
            interval: If set, repeat task every N seconds
            
        Returns:
            Job object representing the enqueued task
        """
        job_kwargs = {
            'kwargs': params,
            'retry': Retry(max=3, interval=[60, 120, 300]),  # Retry after 1min, 2min, 5min
            'job_timeout': timeout,
            'result_ttl': 86400  # Store results for 24 hours
        }
        
        if interval:
            job_kwargs['meta'] = {'interval': interval}
            
        return self.queue.enqueue(
            f'src.workers.scraper_worker.process_{task_type}_task',
            **job_kwargs
        )
    
    def get_queue_status(self) -> Dict[str, int]:
        """Get current queue metrics"""
        return {
            'queued': self.queue.count,
            'started': len(self.queue.started_job_registry),
            'finished': len(self.queue.finished_job_registry),
            'failed': len(self.queue.failed_job_registry)
        }
    
    def clear_queue(self):
        """Clear all jobs from queue"""
        self.queue.empty() 