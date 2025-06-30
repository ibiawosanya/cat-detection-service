#!/bin/bash

set -e

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit/ -v --cov=src/lambdas --cov-report=html

# Run integration tests if API_URL is provided
if [ ! -z "$API_URL" ]; then
    echo "Running integration tests..."
    python -m pytest tests/integration/ -v
else
    echo "Skipping integration tests (API_URL not set)"
fi

echo "Tests completed!"