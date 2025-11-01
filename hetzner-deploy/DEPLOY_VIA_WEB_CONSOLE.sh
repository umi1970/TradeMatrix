#!/bin/bash
# TradeMatrix - Hetzner Deployment Script (Web Console)
# This script can be pasted directly into the Hetzner web console

set -e

echo "=================================="
echo "TradeMatrix Deployment Script"
echo "=================================="

# Create directory structure
echo "Creating directory structure..."
mkdir -p ~/tradematrix/src
mkdir -p ~/tradematrix/logs
cd ~/tradematrix

# Create .env file
echo "Creating .env file..."
cat > .env << 'ENVEOF'
# TradeMatrix.ai - Production Deployment Configuration
# Hetzner Server

# ==============================================================================
# SUPABASE CONNECTION
# ==============================================================================
SUPABASE_URL=https://htnlhazqzpwfyhnngfsn.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh0bmxoYXpxenB3Znlobm5nZnNuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTMzNTYyNCwiZXhwIjoyMDc2OTExNjI0fQ.zu5Y8HylwVxEae7IX8cHwkqb0iifs-74oe1tG2qArxM
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh0bmxoYXpxenB3Znlobm5nZnNuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTMzNTYyNCwiZXhwIjoyMDc2OTExNjI0fQ.zu5Y8HylwVxEae7IX8cHwkqb0iifs-74oe1tG2qArxM

# ==============================================================================
# REDIS / CELERY (Docker Internal)
# ==============================================================================
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ==============================================================================
# LIQUIDITY ALERT SYSTEM - API KEYS
# ==============================================================================
FINNHUB_API_KEY=d42toghr01qorlet3u2gd42toghr01qorlet3u30
ALPHA_VANTAGE_API_KEY=GPSA28ME4GMVYUUG

# ==============================================================================
# WEB PUSH NOTIFICATIONS - VAPID KEYS
# ==============================================================================
VAPID_PUBLIC_KEY=LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUZrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFR09CcWFLZ0s2bWlFOHFGbWxPeUZ5dWQ0cGhaNwpqdUc4ZzNONmhmczg3eVY1cHFvZzJnSUk5bDlOL3NLbXZMVzc0SXM4eHN3alNPTVhqZElrM3ZPZDdRPT0KLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg
VAPID_PRIVATE_KEY=LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JR0hBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJHMHdhd0lCQVFRZ1hqYys5emROc0NWWXo2M1MKL3RlQTJMRFMzazF5bk01V2NWczBDQlFLaVBTaFJBTkNBQVFZNEdwb3FBcnFhSVR5b1dhVTdJWEs1M2ltRm51Two0YnlEYzNxRit6enZKWG1tcWlEYUFnajJYMDMrd3FhOHRidmdpenpHekNOSTR4ZU4waVRlODUzdAotLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tCg
VAPID_SUBJECT=mailto:info@tradematrix.ai
ENVEOF

# Create requirements.txt
echo "Creating requirements.txt..."
cat > requirements.txt << 'REQEOF'
celery==5.4.0
redis==5.2.0
supabase==2.13.1
python-dotenv==1.0.1
finnhub-python==2.4.20
pywebpush==2.0.1
httpx==0.25.2
cryptography==44.0.0
REQEOF

# Create Dockerfile
echo "Creating Dockerfile..."
cat > Dockerfile << 'DOCKERFILE'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Run as non-root user
RUN useradd -m celeryuser && chown -R celeryuser:celeryuser /app
USER celeryuser

CMD ["celery", "-A", "src.tasks", "worker", "--loglevel=info"]
DOCKERFILE

# Create docker-compose.yml
echo "Creating docker-compose.yml..."
cat > docker-compose.yml << 'COMPOSEEOF'
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: tradematrix_redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: tradematrix_celery_worker
    restart: unless-stopped
    command: celery -A src.tasks worker --loglevel=info
    env_file:
      - .env
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs

  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: tradematrix_celery_beat
    restart: unless-stopped
    command: celery -A src.tasks beat --loglevel=info
    env_file:
      - .env
    depends_on:
      redis:
        condition: service_healthy
    volumes:
      - ./src:/app/src
      - ./logs:/app/logs

volumes:
  redis_data:
COMPOSEEOF

echo "Configuration files created successfully!"
echo ""
echo "Next steps:"
echo "1. Upload Python source files to ~/tradematrix/src/"
echo "2. Run: docker-compose build"
echo "3. Run: docker-compose up -d"
echo "4. Check logs: docker-compose logs -f"
