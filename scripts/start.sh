#!/bin/bash

# Start the metrics server in the background
python -u src/collectors/metrics_server.py &
METRICS_PID=$!

# Wait for metrics server to start
echo "Waiting for metrics server to start..."
sleep 5

# Check if metrics server is running
if ! curl -s http://localhost:8000/metrics > /dev/null; then
    echo "Failed to start metrics server"
    kill $METRICS_PID
    exit 1
fi

echo "Metrics server started successfully"

# Start the collection script
python -u src/collectors/test_collection.py

# Keep the container running
tail -f /dev/null 