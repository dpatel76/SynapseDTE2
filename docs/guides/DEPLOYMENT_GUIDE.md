# SynapseDTE Clean Architecture Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the clean architecture version of SynapseDTE in various environments.

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- PostgreSQL 15+ (if not using Docker)
- Redis 7+ (if not using Docker)
- Python 3.11+
- Node.js 18+ and npm 9+
- Valid API keys for LLM providers (Anthropic and/or Google)

## Environment Configuration

### 1. Environment Variables

Create a `.env` file based on `.env.refactor`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://synapse:synapse123@localhost:5433/synapse_dt

# Redis
REDIS_URL=redis://localhost:6380/0

# Security
SECRET_KEY=your-secure-secret-key-here-minimum-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
FROM_EMAIL=noreply@synapse-dte.com

# Feature Flags
ENABLE_CLEAN_ARCHITECTURE=true
ENABLE_CELERY=true
ENABLE_PERFORMANCE_MONITORING=true

# Performance Settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
CACHE_TTL=300
RATE_LIMIT_REQUESTS=100

# Environment
ENVIRONMENT=production
DEBUG=false
DEBUG_SQL=false
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

#### Quick Start

```bash
# Clone repository
git clone https://github.com/deloitte/synapse-dte.git
cd synapse-dte

# Create environment file
cp .env.refactor .env
# Edit .env with your configuration

# Start all services
./scripts/start_clean_architecture.sh
```

#### Manual Docker Compose

```bash
# Build images
docker-compose -f docker-compose.clean.yml build

# Start services
docker-compose -f docker-compose.clean.yml up -d

# Check logs
docker-compose -f docker-compose.clean.yml logs -f

# Stop services
docker-compose -f docker-compose.clean.yml down
```

### Option 2: Kubernetes Deployment

Create Kubernetes manifests:

```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: synapse-postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: synapse-postgres
  template:
    metadata:
      labels:
        app: synapse-postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: synapse_dt
        - name: POSTGRES_USER
          value: synapse
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: synapse-secrets
              key: postgres-password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc
```

Apply manifests:

```bash
# Create namespace
kubectl create namespace synapse-dte

# Create secrets
kubectl create secret generic synapse-secrets \
  --from-literal=postgres-password=your-password \
  --from-literal=secret-key=your-secret-key \
  -n synapse-dte

# Apply configurations
kubectl apply -f k8s/ -n synapse-dte

# Check status
kubectl get pods -n synapse-dte
```

### Option 3: Manual Deployment

#### 1. Database Setup

```bash
# Install PostgreSQL
sudo apt-get install postgresql-15

# Create database and user
sudo -u postgres psql
CREATE DATABASE synapse_dt;
CREATE USER synapse WITH ENCRYPTED PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE synapse_dt TO synapse;
\q

# Run migrations
alembic upgrade head

# Seed initial data
python scripts/seed_rbac_data.py
```

#### 2. Redis Setup

```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: maxmemory 2gb
# Set: maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis
```

#### 3. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Create test users
python scripts/create_test_users.py

# Start backend
uvicorn app.main_clean:app --host 0.0.0.0 --port 8001 --workers 4
```

#### 4. Celery Setup

```bash
# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info --concurrency=4

# Start Celery beat (in separate terminal)
celery -A app.core.celery_app beat --loglevel=info

# Start Flower (optional, for monitoring)
celery -A app.core.celery_app flower --port=5556
```

#### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx or use npm
npm run start:prod
```

## Production Configuration

### 1. Nginx Configuration

```nginx
upstream backend {
    server localhost:8001;
}

upstream frontend {
    server localhost:3001;
}

server {
    listen 80;
    server_name synapse-dte.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name synapse-dte.yourdomain.com;

    ssl_certificate /etc/ssl/certs/synapse-dte.crt;
    ssl_certificate_key /etc/ssl/private/synapse-dte.key;

    # Security headers
    add_header X-Frame-Options "DENY";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # API
    location /api {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static {
        alias /var/www/synapse-dte/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### 2. Systemd Services

Create systemd service files:

```ini
# /etc/systemd/system/synapse-backend.service
[Unit]
Description=SynapseDTE Backend
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=synapse
Group=synapse
WorkingDirectory=/opt/synapse-dte
Environment="PATH=/opt/synapse-dte/venv/bin"
ExecStart=/opt/synapse-dte/venv/bin/uvicorn app.main_clean:app --host 0.0.0.0 --port 8001 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable synapse-backend
sudo systemctl start synapse-backend
```

### 3. Performance Tuning

#### PostgreSQL Optimization

```sql
-- postgresql.conf adjustments
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

#### Redis Optimization

```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save ""  # Disable persistence for cache-only usage
```

## Monitoring and Maintenance

### 1. Health Checks

```bash
# Check API health
curl https://synapse-dte.yourdomain.com/api/v1/health

# Check database health
curl https://synapse-dte.yourdomain.com/api/v1/health/db

# Check Celery health
celery -A app.core.celery_app inspect active
```

### 2. Monitoring Setup

#### Prometheus Configuration

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'synapse-dte'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
```

#### Grafana Dashboard

Import the provided dashboard from `monitoring/grafana-dashboard.json`

### 3. Backup Strategy

```bash
# Database backup script
#!/bin/bash
BACKUP_DIR="/backup/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="synapse_dt"

# Create backup
pg_dump -U synapse -h localhost -p 5433 $DB_NAME | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$TIMESTAMP.sql.gz s3://your-backup-bucket/postgres/
```

### 4. Log Management

```bash
# Configure log rotation
cat > /etc/logrotate.d/synapse-dte << EOF
/var/log/synapse-dte/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 synapse synapse
}
EOF
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   
   # Test connection
   psql -U synapse -h localhost -p 5433 -d synapse_dt
   ```

2. **Redis Connection Issues**
   ```bash
   # Check Redis is running
   redis-cli ping
   
   # Monitor Redis
   redis-cli monitor
   ```

3. **Celery Worker Issues**
   ```bash
   # Check worker status
   celery -A app.core.celery_app inspect active
   
   # Purge task queue
   celery -A app.core.celery_app purge
   ```

4. **Performance Issues**
   ```bash
   # Check slow queries
   psql -U synapse -d synapse_dt -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
   
   # Check connection pool
   curl http://localhost:8001/api/v1/health/pool
   ```

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable SSL/TLS for all connections
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Set up intrusion detection
- [ ] Configure backup encryption
- [ ] Implement rate limiting
- [ ] Enable CORS properly
- [ ] Rotate API keys regularly
- [ ] Monitor for security updates

## Maintenance Tasks

### Daily
- Monitor error logs
- Check system resources
- Verify backup completion

### Weekly
- Review performance metrics
- Check for security updates
- Clean up temporary files

### Monthly
- Update dependencies
- Review and optimize slow queries
- Audit user access
- Test disaster recovery

## Support

For support and issues:
- GitHub Issues: https://github.com/deloitte/synapse-dte/issues
- Documentation: https://docs.synapse-dte.com
- Email: support@synapse-dte.com