# TradeMatrix - Strato Server Deployment Guide

**Server:** Strato VC 2-4 (2 vCores, 4 GB RAM, 120 GB Storage)
**OS:** Ubuntu 22.04 LTS
**Purpose:** Celery Worker + Redis (Liquidity Alert System)

---

## 📋 Pre-Deployment Checklist

- [ ] Strato VC 2-4 Server bestellt
- [ ] Server-Zugangsdaten erhalten (IP, Root-Passwort)
- [ ] SSH-Key erstellt (empfohlen)
- [ ] Supabase URLs und Keys bereit
- [ ] API Keys bereit (Finnhub, Alpha Vantage)
- [ ] VAPID Keys bereit

---

## 🚀 Part 1: Initial Server Setup (SSH Connection)

### 1.1 Connect to Server via SSH

```bash
# Replace with your server IP
ssh root@YOUR_SERVER_IP

# You'll be prompted for password (from Strato email)
```

### 1.2 Update System

```bash
# Update package lists
apt update && apt upgrade -y

# Install essential tools
apt install -y curl git vim nano htop ufw
```

### 1.3 Setup Firewall

```bash
# Allow SSH
ufw allow 22/tcp

# Enable firewall
ufw --force enable

# Check status
ufw status
```

### 1.4 Create Non-Root User (Optional but recommended)

```bash
# Create user
adduser tradematrix

# Add to sudo group
usermod -aG sudo tradematrix

# Switch to new user
su - tradematrix
```

---

## 🐳 Part 2: Install Docker & Docker Compose

### 2.1 Install Docker

```bash
# Install Docker dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package list
sudo apt update

# Install Docker
sudo apt install -y docker-ce docker-ce-cli containerd.io

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (so you don't need sudo)
sudo usermod -aG docker $USER

# Apply group changes (or logout/login)
newgrp docker

# Verify Docker installation
docker --version
```

### 2.2 Install Docker Compose

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make executable
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

---

## 📦 Part 3: Deploy TradeMatrix Services

### 3.1 Clone Repository

```bash
# Create directory
mkdir -p ~/apps
cd ~/apps

# Clone repository (you'll need GitHub access)
git clone https://github.com/YOUR_USERNAME/TradeMatrix.git
# OR if using HTTPS with token:
# git clone https://<YOUR_GITHUB_TOKEN>@github.com/YOUR_USERNAME/TradeMatrix.git

cd TradeMatrix
```

### 3.2 Create Environment Files

```bash
# Navigate to agents directory
cd ~/apps/TradeMatrix/services/agents

# Create .env file
nano .env
```

**Paste the following content (replace with YOUR values):**

```bash
# Supabase
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_role_key_here

# Redis (Docker internal)
REDIS_URL=redis://redis:6379/0

# API Keys
FINNHUB_API_KEY=your_finnhub_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key

# VAPID Keys (Web Push)
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key_pem_format
VAPID_SUBJECT=mailto:your-email@example.com
```

**Save:** `Ctrl+O`, `Enter`, `Ctrl+X`

### 3.3 Create Docker Compose File

```bash
# Still in /services/agents directory
nano docker-compose.yml
```

**Paste the following:**

```yaml
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
```

**Save:** `Ctrl+O`, `Enter`, `Ctrl+X`

### 3.4 Create Dockerfile

```bash
nano Dockerfile
```

**Paste the following:**

```dockerfile
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
```

**Save:** `Ctrl+O`, `Enter`, `Ctrl+X`

---

## 🔨 Part 4: Build & Start Services

### 4.1 Build Docker Images

```bash
# Make sure you're in /services/agents
cd ~/apps/TradeMatrix/services/agents

# Build images
docker-compose build
```

### 4.2 Start Services

```bash
# Start all services in background
docker-compose up -d

# Check status
docker-compose ps

# Should show 3 containers running:
# - tradematrix_redis
# - tradematrix_celery_worker
# - tradematrix_celery_beat
```

### 4.3 View Logs

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
docker-compose logs -f redis

# Exit logs: Ctrl+C
```

---

## ✅ Part 5: Verify Everything Works

### 5.1 Check Celery Worker

```bash
# Check worker is connected to Redis
docker-compose logs celery_worker | grep "Connected to redis"

# Should see: [2025-01-01 00:00:00,000: INFO/MainProcess] Connected to redis://redis:6379/0
```

### 5.2 Check Celery Beat (Scheduler)

```bash
# Check beat is scheduling tasks
docker-compose logs celery_beat | grep "Scheduler"

# Should see periodic task scheduling
```

### 5.3 Check Tasks are Running

```bash
# Monitor logs for task execution
docker-compose logs -f celery_worker

# You should see tasks like:
# - fetch_prices
# - check_liquidity_levels
# Every 1 minute
```

### 5.4 Test Manually (Optional)

```bash
# Access worker container
docker-compose exec celery_worker bash

# Inside container, test Supabase connection:
python3 -c "
from src.config.supabase_client import get_supabase_client
supabase = get_supabase_client()
result = supabase.table('symbols').select('*').execute()
print(f'Symbols found: {len(result.data)}')
"

# Exit container
exit
```

---

## 🔄 Part 6: Management Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### View Logs
```bash
docker-compose logs -f
```

### Update Code (After Git Push)
```bash
cd ~/apps/TradeMatrix/services/agents
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Check Resource Usage
```bash
# CPU, RAM usage
docker stats

# Disk usage
docker system df
```

---

## 📊 Part 7: Monitoring & Maintenance

### 7.1 Setup Automated Restarts

Docker Compose already has `restart: unless-stopped`, so services will auto-restart on:
- Container crash
- Server reboot

### 7.2 Setup Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/docker-containers
```

**Paste:**

```
/var/lib/docker/containers/*/*.log {
  rotate 7
  daily
  compress
  missingok
  delaycompress
  copytruncate
}
```

**Save and test:**

```bash
sudo logrotate -d /etc/logrotate.d/docker-containers
```

### 7.3 Setup Health Check Script

```bash
# Create monitoring script
nano ~/monitor_tradematrix.sh
```

**Paste:**

```bash
#!/bin/bash

cd ~/apps/TradeMatrix/services/agents

# Check if all containers are running
RUNNING=$(docker-compose ps -q | wc -l)
EXPECTED=3

if [ "$RUNNING" -ne "$EXPECTED" ]; then
    echo "[$(date)] WARNING: Only $RUNNING/$EXPECTED containers running!"
    docker-compose ps
    # Optionally: send alert email or restart
    docker-compose up -d
fi
```

**Make executable:**

```bash
chmod +x ~/monitor_tradematrix.sh
```

**Add to crontab (runs every 5 minutes):**

```bash
crontab -e

# Add this line:
*/5 * * * * ~/monitor_tradematrix.sh >> ~/monitor.log 2>&1
```

---

## 🔐 Part 8: Security Hardening (Recommended)

### 8.1 Change SSH Port (Optional)

```bash
sudo nano /etc/ssh/sshd_config

# Change:
# Port 22
# To:
# Port 2222

sudo systemctl restart sshd

# Update firewall:
sudo ufw allow 2222/tcp
sudo ufw delete allow 22/tcp
```

### 8.2 Disable Root Login

```bash
sudo nano /etc/ssh/sshd_config

# Change:
# PermitRootLogin yes
# To:
# PermitRootLogin no

sudo systemctl restart sshd
```

### 8.3 Setup Fail2Ban (Brute Force Protection)

```bash
sudo apt install -y fail2ban
sudo systemctl start fail2ban
sudo systemctl enable fail2ban
```

---

## 🎯 Quick Reference

### Service URLs
- **Frontend:** https://tradematrix.netlify.app
- **Supabase:** Your Supabase Dashboard URL
- **Server:** Your Strato Server IP

### Important Directories
- **Code:** `~/apps/TradeMatrix/services/agents`
- **Logs:** `~/apps/TradeMatrix/services/agents/logs`
- **Docker Volumes:** `/var/lib/docker/volumes`

### Common Issues

**1. Container won't start:**
```bash
docker-compose logs <service_name>
# Check .env file has correct values
```

**2. Redis connection failed:**
```bash
docker-compose restart redis
# Check: docker-compose logs redis
```

**3. Out of disk space:**
```bash
docker system prune -a
# Removes unused images/containers
```

**4. High CPU usage:**
```bash
docker stats
# Check which container is using resources
# Adjust Celery worker concurrency if needed
```

---

## 📞 Support Checklist

If something doesn't work:

1. Check logs: `docker-compose logs -f`
2. Check .env file has correct values
3. Check Redis is running: `docker-compose ps`
4. Check disk space: `df -h`
5. Check memory: `free -h`
6. Restart services: `docker-compose restart`

---

**Made with 🧠 by Claude + umi1970**
