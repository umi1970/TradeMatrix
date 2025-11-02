# TradeMatrix - Hetzner Deployment Instructions

## Option 1: Deploy via Git (RECOMMENDED)

Since SSH/SCP is not working from your local machine, we'll use Git to deploy the code directly on the server.

### Step 1: SSH/Firewall Troubleshooting (Optional - Run in Hetzner Web Console)

If you want to fix SSH for future use, run these commands in the web console:

```bash
# Check SSH service status
systemctl status ssh

# If not running, start it
systemctl start ssh
systemctl enable ssh

# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
ufw status

# Verify SSH is listening
ss -tlnp | grep :22
```

### Step 2: Upload Code to GitHub (Run Locally)

First, commit and push your hetzner-deploy folder to GitHub:

```powershell
# On your local machine (PowerShell)
cd C:\Users\uzobu\Documents\SaaS\TradeMatrix

# Add hetzner-deploy to git (if not already tracked)
git add hetzner-deploy/
git commit -m "feat: Add Hetzner deployment configuration"
git push origin main
```

### Step 3: Deploy on Hetzner (Run in Web Console)

Now in the Hetzner web console, run:

```bash
# Install git if not present
apt-get update && apt-get install -y git

# Create deployment directory
mkdir -p ~/tradematrix
cd ~/tradematrix

# Clone only the deployment folder using sparse checkout
git init
git remote add origin https://github.com/umi1970/TradeMatrix.git
git config core.sparseCheckout true
echo "hetzner-deploy/*" >> .git/info/sparse-checkout
git pull origin main

# Move files to correct location
mv hetzner-deploy/* .
rm -rf hetzner-deploy
```

### Step 4: Verify Files

```bash
cd ~/tradematrix
ls -la

# You should see:
# .env
# docker-compose.yml
# Dockerfile
# requirements.txt
# src/ directory
```

### Step 5: Build and Start Services

```bash
cd ~/tradematrix

# Build Docker images
docker-compose build

# Start services in background
docker-compose up -d

# Check if services are running
docker-compose ps
```

### Step 6: Verify Deployment

```bash
# Check logs
docker-compose logs -f celery_worker

# In another terminal (Ctrl+C to exit logs first), check Redis
docker-compose logs redis

# Check Celery Beat
docker-compose logs celery_beat
```

### Step 7: Monitor Services

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f celery_worker

# Check container status
docker-compose ps

# Restart services if needed
docker-compose restart

# Stop services
docker-compose down

# Start services
docker-compose up -d
```

---

## Option 2: Manual File Creation (If Git doesn't work)

If Git clone fails, you can create files manually in the web console:

### Step 1: Create Directory Structure

```bash
mkdir -p ~/tradematrix/src
mkdir -p ~/tradematrix/logs
cd ~/tradematrix
```

### Step 2: Create .env File

```bash
cat > .env << 'ENVEOF'
# TradeMatrix.ai - Production Deployment Configuration
SUPABASE_URL=https://htnlhazqzpwfyhnngfsn.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh0bmxoYXpxenB3Znlobm5nZnNuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTMzNTYyNCwiZXhwIjoyMDc2OTExNjI0fQ.zu5Y8HylwVxEae7IX8cHwkqb0iifs-74oe1tG2qArxM
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh0bmxoYXpxenB3Znlobm5nZnNuIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTMzNTYyNCwiZXhwIjoyMDc2OTExNjI0fQ.zu5Y8HylwVxEae7IX8cHwkqb0iifs-74oe1tG2qArxM
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
FINNHUB_API_KEY=d42toghr01qorlet3u2gd42toghr01qorlet3u30
ALPHA_VANTAGE_API_KEY=GPSA28ME4GMVYUUG
VAPID_PUBLIC_KEY=LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUZrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFR09CcWFLZ0s2bWlFOHFGbWxPeUZ5dWQ0cGhaNwpqdUc4ZzNONmhmczg3eVY1cHFvZzJnSUk5bDlOL3NLbXZMVzc0SXM4eHN3alNPTVhqZElrM3ZPZDdRPT0KLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0tCg
VAPID_PRIVATE_KEY=LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JR0hBZ0VBTUJNR0J5cUdTTTQ5QWdFR0NDcUdTTTQ5QXdFSEJHMHdhd0lCQVFRZ1hqYys5emROc0NWWXo2M1MKL3RlQTJMRFMzazF5bk01V2NWczBDQlFLaVBTaFJBTkNBQVFZNEdwb3FBcnFhSVR5b1dhVTdJWEs1M2ltRm51Two0YnlEYzNxRit6enZKWG1tcWlEYUFnajJYMDMrd3FhOHRidmdpenpHekNOSTR4ZU4waVRlODUzdAotLS0tLUVORCBQUklWQVRFIEtFWS0tLS0tCg
VAPID_SUBJECT=mailto:info@tradematrix.ai
ENVEOF
```

### Step 3: Create requirements.txt

```bash
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
```

### Step 4: Create Dockerfile

```bash
cat > Dockerfile << 'DOCKEREOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/logs

RUN useradd -m celeryuser && chown -R celeryuser:celeryuser /app
USER celeryuser

CMD ["celery", "-A", "src.tasks", "worker", "--loglevel=info"]
DOCKEREOF
```

### Step 5: Create docker-compose.yml

```bash
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
```

### Step 6: Upload Python Source Files

For the `src/` directory, you'll need to use Git (Option 1) or upload files via SFTP once SSH is fixed.

---

## Troubleshooting

### SSH Connection Timeout
- Check firewall: `ufw status`
- Check SSH service: `systemctl status ssh`
- Check if port 22 is open: `ss -tlnp | grep :22`
- Try from Hetzner Cloud firewall rules in web interface

### Docker Build Fails
- Check Docker version: `docker --version`
- Check available disk space: `df -h`
- Clear Docker cache: `docker system prune -a`

### Containers Not Starting
- Check logs: `docker-compose logs`
- Check environment variables: `cat .env`
- Verify Supabase connectivity from server:
  ```bash
  curl -I https://htnlhazqzpwfyhnngfsn.supabase.co
  ```

### Redis Connection Errors
- Check Redis is running: `docker-compose ps redis`
- Check Redis logs: `docker-compose logs redis`
- Verify Redis health: `docker exec tradematrix_redis redis-cli ping`

---

## Monitoring Commands

```bash
# View real-time logs
docker-compose logs -f

# Check resource usage
docker stats

# Restart specific service
docker-compose restart celery_worker

# View environment variables (inside container)
docker-compose exec celery_worker env

# Execute command in container
docker-compose exec celery_worker celery -A src.tasks inspect active

# Check Celery worker status
docker-compose exec celery_worker celery -A src.tasks status

# Check scheduled tasks
docker-compose exec celery_beat celery -A src.tasks inspect scheduled
```

---

## Next Steps After Deployment

1. Verify alerts are being generated in Supabase `liquidity_alerts` table
2. Test push notifications by triggering an alert
3. Monitor logs for any errors
4. Set up log rotation if needed
5. Configure automatic backups
6. Set up monitoring/alerting (optional)

---

## Server Information

- **IP:** 135.181.195.241
- **OS:** Ubuntu (Hetzner CX11)
- **Resources:** 2 vCores, 4GB RAM
- **Docker:** 28.5.1
- **Docker Compose:** 2.40.3

---

## Support

If you encounter issues:
1. Check Docker logs: `docker-compose logs`
2. Verify all services are running: `docker-compose ps`
3. Check Supabase connectivity
4. Verify API keys in .env are correct
