#!/bin/bash
# Script to run the Temporal worker

echo "Starting Temporal worker..."
export TEMPORAL_HOST=localhost:7233
export TEMPORAL_NAMESPACE=default

# Run the reconciled worker
python -m app.temporal.worker_reconciled