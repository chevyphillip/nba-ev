"""
Prometheus metrics server for the NBA data collector.
"""
import logging
import time
import threading
import psutil
import os
from prometheus_client import start_http_server
from src.monitoring.metrics import (
    CPU_USAGE,
    MEMORY_USAGE
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_resource_metrics():
    """Update CPU and memory usage metrics."""
    process = psutil.Process(os.getpid())
    
    while True:
        try:
            # Update memory usage (in bytes)
            memory_info = process.memory_info()
            MEMORY_USAGE.set(memory_info.rss)
            
            # Update CPU usage (percentage)
            CPU_USAGE.set(process.cpu_percent())
            
            # Log current values for debugging
            logger.debug(f"Updated metrics - CPU: {process.cpu_percent()}%, Memory: {memory_info.rss} bytes")
            
            # Update every 15 seconds
            time.sleep(15)
            
        except Exception as e:
            logger.error(f"Error updating resource metrics: {str(e)}")
            time.sleep(15)  # Wait before retrying

def start_metrics_server(port=8000):
    """Start the Prometheus metrics server."""
    try:
        # Start the metrics server
        start_http_server(port)
        logger.info(f"Started metrics server on port {port}")
        
        # Start resource metrics update thread
        metrics_thread = threading.Thread(target=update_resource_metrics, daemon=True)
        metrics_thread.start()
        logger.info("Started resource metrics update thread")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        logger.error(f"Error starting metrics server: {str(e)}")
        raise

if __name__ == "__main__":
    start_metrics_server() 