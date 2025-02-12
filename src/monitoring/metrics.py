"""
Prometheus metrics for the NBA data collector.
"""
from prometheus_client import Counter, Gauge, Histogram, start_http_server

# Collection metrics
GAMES_COLLECTED = Counter(
    'nba_games_collected_total',
    'Total number of NBA games collected'
)

BOX_SCORES_COLLECTED = Counter(
    'nba_box_scores_collected_total',
    'Total number of NBA box scores collected'
)

# Error metrics
COLLECTION_ERRORS = Counter(
    'nba_collection_errors_total',
    'Total number of collection errors by type',
    ['error_type']
)

# Performance metrics
REQUEST_DURATION = Histogram(
    'nba_request_duration_seconds',
    'Time spent processing requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

BATCH_PROCESSING_TIME = Histogram(
    'nba_batch_processing_seconds',
    'Time spent processing batches of data',
    buckets=[30, 60, 120, 300, 600]
)

# Resource usage metrics
CPU_USAGE = Gauge(
    'nba_cpu_usage_percent',
    'Current CPU usage percentage'
)

MEMORY_USAGE = Gauge(
    'nba_memory_usage_bytes',
    'Current memory usage in bytes'
)

# Cache metrics
CACHE_HITS = Counter(
    'nba_cache_hits_total',
    'Total number of cache hits'
)

CACHE_MISSES = Counter(
    'nba_cache_misses_total',
    'Total number of cache misses'
)

# Database metrics
DB_OPERATIONS = Counter(
    'nba_db_operations_total',
    'Total number of database operations by type',
    ['operation']
)

DB_ERRORS = Counter(
    'nba_db_errors_total',
    'Total number of database errors by type',
    ['error_type']
)

def start_metrics_server(port: int = 8000):
    """Start the metrics HTTP server."""
    start_http_server(port) 