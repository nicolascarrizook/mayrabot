#!/bin/bash

# Redeploy script for nutrition bot

echo "Redeploying nutrition bot..."

# Pull latest changes
echo "Pulling latest code..."
git pull

# Stop containers
echo "Stopping containers..."
docker-compose -f docker-compose.prod.yml down

# Rebuild containers with no cache
echo "Rebuilding containers..."
docker-compose -f docker-compose.prod.yml build --no-cache api telegram-bot

# Start containers
echo "Starting containers..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Show logs
echo "Showing logs..."
docker-compose -f docker-compose.prod.yml logs --tail 100

echo "Redeploy complete!"