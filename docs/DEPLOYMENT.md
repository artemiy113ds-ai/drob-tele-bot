# Deployment Guide

## Prerequisites
- Docker & Docker Compose installed
- Ubuntu/Debian server (18+)
- Domain name (optional but recommended)
- SSL certificate (Let's Encrypt)

## Local Development

### 1. Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### 2. Initialize Database
```bash
python database.py
python -c "from gamification import init_gamification_db; init_gamification_db()"
```

### 3. Run Locally
```bash
# Terminal 1: FastAPI
uvicorn main_v3:app --reload --port 8000

# Terminal 2: Bot
python bot_v3.py

# Terminal 3: Telegram WebApp
# Access at http://localhost:8000
```

## Docker Deployment

### 1. Build Image
```bash
docker-compose build
```

### 2. Run Services
```bash
docker-compose up -d
```

### 3. Check Status
```bash
docker-compose ps
docker-compose logs -f api
```

## Production Deployment (Ubuntu/DigitalOcean)

### 1. SSH into Server
```bash
ssh root@your_server_ip
```

### 2. Install Dependencies
```bash
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv git docker.io docker-compose nginx certbot python3-certbot-nginx
```

### Clone Project
```bash
cd /opt
git clone <your-repo> minishop
cd minishop
```

### 4. Setup Environment
```bash
cp .env.example .env
nano .env  # Edit configuration
```

### 5. Configure Nginx
```bash
cp nginx.conf /etc/nginx/sites-available/minishop
ln -s /etc/nginx/sites-available/minishop /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### 6. SSL Certificate
```bash
certbot certonly --nginx -d your_domain.com
# Update nginx.conf with certificate paths
```

### 7. Docker Start
```bash
docker-compose build
docker-compose up -d
```

### 8. Verify Deployment
```bash
curl https://your_domain.com
docker-compose logs api
docker-compose logs bot
```

## Database Backup

### Automated Backup (Daily at 2 AM)
```bash
# Create backup script
cat > /opt/minishop/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/minishop/backups"
mkdir -p $BACKUP_DIR
cp /opt/minishop/shop.db $BACKUP_DIR/shop_$(date +%Y%m%d_%H%M%S).db
find $BACKUP_DIR -name "shop_*.db" -mtime +30 -delete
EOF

chmod +x /opt/minishop/backup.sh

# Add to crontab
crontab -e
# 0 2 * * * /opt/minishop/backup.sh
```

### Manual Backup
```bash
docker-compose exec api cp shop.db shop_backup_$(date +%Y%m%d).db
docker cp minishop_api_1:/app/shop_backup_*.db ./
```

## Monitoring

### Check Logs
```bash
docker-compose logs api loguru.log
docker-compose logs bot loguru.log
```

### Docker Health Check
```bash
docker ps --filter "health=unhealthy"
```

### Performance
```bash
docker stats minishop_api_1
```

## Troubleshooting

### Port Already in Use
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

### Database Lock
```bash
docker-compose down
docker volume prune
docker-compose up -d
```

### Bot Not Responding
```bash
docker-compose logs bot | tail -50
# Check TELEGRAM_BOT_TOKEN in .env
```

### API Errors
```bash
docker-compose logs api | grep ERROR
```

## Scaling

### Horizontal Scaling (Multiple API Instances)
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      replicas: 3
  api_2:
    # ...
  api_3:
    # ...
```

### Load Balancing
Update `nginx.conf`:
```nginx
upstream api {
    server api:8000;
    server api_2:8000;
    server api_3:8000;
}
```

## AWS Deployment

### 1. Create EC2 Instance
- AMI: Ubuntu 20.04 LTS
- Instance: t3.medium (2GB RAM, 2vCPU)
- Security Group: Allow ports 22, 80, 443

### 2. Elastic IP
```bash
aws ec2 allocate-address --domain vpc
aws ec2 associate-address --instance-id <instance-id> --allocation-id <allocation-id>
```

### 3. RDS Database (Optional)
- Engine: PostgreSQL 12+
- Instance: db.t3.micro
- Update DATABASE_URL in .env

### 4. S3 for Uploads
```bash
aws s3 mb s3://minishop-uploads
# Update boto3 config in .env
```

## PostgreSQL Migration

### 1. Export SQLite Data
```bash
sqlite3 shop.db ".mode csv" "SELECT * FROM products;" > products.csv
```

### 2. Setup PostgreSQL
```bash
docker run -d --name postgres -e POSTGRES_PASSWORD=password -v pgdata:/var/lib/postgresql/data postgres:14
```

### 3. Import Data
```python
# migration.py
import psycopg2
# ... migration script
```

## Monitoring & Analytics

### Sentry Integration
```python
# In main_v3.py
import sentry_sdk
sentry_sdk.init("https://key@sentry.io/project")
```

### Prometheus Metrics
```bash
pip install prometheus-client
# Add metrics to endpoints
```
