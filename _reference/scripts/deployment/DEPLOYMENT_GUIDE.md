# SynapseDTE Complete Deployment Guide

This guide provides step-by-step instructions for deploying the complete SynapseDTE application on a new server.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Database Setup](#database-setup)
4. [Backend Setup](#backend-setup)
5. [Frontend Setup](#frontend-setup)
6. [Temporal Setup](#temporal-setup)
7. [Nginx Configuration](#nginx-configuration)
8. [Process Management](#process-management)
9. [Verification](#verification)
10. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Server Requirements
- **OS**: Ubuntu 20.04 LTS or later (or equivalent)
- **RAM**: 8GB minimum (16GB recommended)
- **CPU**: 4 cores minimum
- **Storage**: 50GB minimum
- **Network**: Static IP with ports 80, 443 open

### Required Software
- Python 3.9+
- Node.js 16+ and npm
- PostgreSQL 12+
- Redis (for caching)
- Nginx (reverse proxy)
- Supervisor or systemd (process management)

## Prerequisites Installation

### 1. Update System

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    build-essential \
    curl \
    wget \
    git \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release
```

### 2. Install Python 3.9+

```bash
# Add deadsnakes PPA for latest Python
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python and dependencies
sudo apt install -y \
    python3.9 \
    python3.9-dev \
    python3.9-venv \
    python3-pip

# Set Python 3.9 as default
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
```

### 3. Install Node.js 18.x

```bash
# Install NodeSource repository
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Install Node.js
sudo apt install -y nodejs

# Verify installation
node --version  # Should show v18.x.x
npm --version   # Should show 9.x.x
```

### 4. Install PostgreSQL 14

```bash
# Add PostgreSQL repository
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
echo "deb http://apt.postgresql.org/pub/repos/apt/ $(lsb_release -cs)-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list

# Install PostgreSQL
sudo apt update
sudo apt install -y postgresql-14 postgresql-client-14 postgresql-contrib-14

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 5. Install Redis

```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis
sudo sed -i 's/supervised no/supervised systemd/g' /etc/redis/redis.conf

# Start and enable Redis
sudo systemctl restart redis
sudo systemctl enable redis
```

### 6. Install Nginx

```bash
# Install Nginx
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Database Setup

### 1. Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

-- Create database user
CREATE USER synapse_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
ALTER USER synapse_user CREATEDB;

-- Exit psql
\q
```

### 2. Create Database

```bash
# Create application directory
sudo mkdir -p /opt/synapseDTE
cd /opt/synapseDTE

# Clone repository (or copy files)
git clone https://github.com/your-repo/SynapseDTE.git .

# Create database using schema files
cd migrations/schema

# Create database
sudo -u postgres createdb synapse_dt

# Load schema and seed data
sudo -u postgres psql -d synapse_dt -f complete_schema.sql
sudo -u postgres psql -d synapse_dt -f seed_data.sql

# Grant permissions
sudo -u postgres psql -d synapse_dt -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO synapse_user;"
sudo -u postgres psql -d synapse_dt -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO synapse_user;"
```

## Backend Setup

### 1. Create Python Virtual Environment

```bash
cd /opt/synapseDTE

# Create virtual environment
python3.9 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 2. Install Python Dependencies

```bash
# Install dependencies
pip install -r scripts/deployment/requirements.txt

# If requirements.txt doesn't exist, install manually:
pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    sqlalchemy==2.0.23 \
    asyncpg==0.29.0 \
    alembic==1.12.1 \
    pydantic==2.5.0 \
    pydantic-settings==2.1.0 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    python-multipart==0.0.6 \
    httpx==0.25.2 \
    anthropic==0.18.1 \
    google-generativeai==0.3.0 \
    redis==5.0.1 \
    celery==5.3.4 \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    python-dotenv==1.0.0
```

### 3. Configure Environment

```bash
# Create .env file
cat > .env << EOF
# Database
DATABASE_URL=postgresql+asyncpg://synapse_user:your_secure_password@localhost:5432/synapse_dt

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# LLM APIs (add your keys)
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Frontend URL
FRONTEND_URL=http://your-domain.com

# Backend URL
BACKEND_URL=http://your-domain.com/api
EOF

# Set permissions
chmod 600 .env
```

### 4. Test Backend

```bash
# Run migrations
alembic upgrade head

# Test run
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Frontend Setup

### 1. Install Frontend Dependencies

```bash
cd /opt/synapseDTE/frontend

# Install dependencies
npm install

# Install global packages
sudo npm install -g serve
```

### 2. Configure Frontend

```bash
# Create production environment file
cat > .env.production << EOF
REACT_APP_API_URL=http://your-domain.com/api
REACT_APP_VERSION=2.0.0
EOF
```

### 3. Build Frontend

```bash
# Build production bundle
npm run build

# Test serving
serve -s build -l 3000
```

## Temporal Setup (Optional)

If using Temporal for workflow orchestration:

### 1. Install Temporal

```bash
# Download Temporal
cd /opt
wget https://github.com/temporalio/temporal/releases/download/v1.22.0/temporal_1.22.0_linux_amd64.tar.gz
tar -xzf temporal_1.22.0_linux_amd64.tar.gz

# Install Temporal CLI
curl -sSf https://temporal.download/cli.sh | sh
```

### 2. Configure Temporal

```bash
# Create Temporal config
mkdir -p /etc/temporal
cat > /etc/temporal/config.yaml << EOF
persistence:
  defaultStore: postgres
  visibilityStore: postgres
  datastores:
    postgres:
      sql:
        driver: "postgres"
        host: "localhost"
        port: 5432
        database: "temporal"
        user: "temporal_user"
        password: "temporal_password"
EOF
```

### 3. Create Temporal Database

```bash
sudo -u postgres psql << EOF
CREATE USER temporal_user WITH PASSWORD 'temporal_password';
CREATE DATABASE temporal;
GRANT ALL PRIVILEGES ON DATABASE temporal TO temporal_user;
EOF
```

## Nginx Configuration

### 1. Create Nginx Configuration

```bash
sudo tee /etc/nginx/sites-available/synapseDTE << EOF
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api {
        rewrite ^/api(.*)\$ \$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # File upload size
    client_max_body_size 100M;
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/synapseDTE /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Setup SSL (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

## Process Management

### 1. Create Systemd Services

#### Backend Service

```bash
sudo tee /etc/systemd/system/synapseDTE-backend.service << EOF
[Unit]
Description=SynapseDTE Backend
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/synapseDTE
Environment="PATH=/opt/synapseDTE/venv/bin"
ExecStart=/opt/synapseDTE/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

#### Frontend Service

```bash
sudo tee /etc/systemd/system/synapseDTE-frontend.service << EOF
[Unit]
Description=SynapseDTE Frontend
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/synapseDTE/frontend
ExecStart=/usr/bin/serve -s build -l 3000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Start Services

```bash
# Set permissions
sudo chown -R www-data:www-data /opt/synapseDTE

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable synapseDTE-backend
sudo systemctl start synapseDTE-backend

sudo systemctl enable synapseDTE-frontend
sudo systemctl start synapseDTE-frontend

# Check status
sudo systemctl status synapseDTE-backend
sudo systemctl status synapseDTE-frontend
```

## Verification

### 1. Check Services

```bash
# Check all services are running
sudo systemctl status postgresql
sudo systemctl status redis
sudo systemctl status nginx
sudo systemctl status synapseDTE-backend
sudo systemctl status synapseDTE-frontend

# Check ports
sudo netstat -tlnp | grep -E '(5432|6379|8000|3000|80)'
```

### 2. Test Application

```bash
# Test backend health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# Test through Nginx
curl http://your-domain.com
curl http://your-domain.com/api/health
```

### 3. Login Test

1. Open browser to `http://your-domain.com`
2. Login with test user:
   - Email: `admin@example.com`
   - Password: `password123`

## Monitoring

### 1. Setup Logging

```bash
# Create log directory
sudo mkdir -p /var/log/synapseDTE
sudo chown www-data:www-data /var/log/synapseDTE

# Configure log rotation
sudo tee /etc/logrotate.d/synapseDTE << EOF
/var/log/synapseDTE/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
}
EOF
```

### 2. View Logs

```bash
# View backend logs
sudo journalctl -u synapseDTE-backend -f

# View frontend logs
sudo journalctl -u synapseDTE-frontend -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Backup Strategy

### 1. Database Backup Script

```bash
sudo tee /usr/local/bin/backup-synapseDTE.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/synapseDTE"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U synapse_user synapse_dt | gzip > $BACKUP_DIR/synapse_dt_$DATE.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/backup-synapseDTE.sh

# Add to crontab
echo "0 2 * * * /usr/local/bin/backup-synapseDTE.sh" | sudo crontab -
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL is running
   sudo systemctl status postgresql
   
   # Check connection
   psql -U synapse_user -d synapse_dt -h localhost
   ```

2. **Backend Won't Start**
   ```bash
   # Check logs
   sudo journalctl -u synapseDTE-backend -n 100
   
   # Test manually
   cd /opt/synapseDTE
   source venv/bin/activate
   python -c "from app.main import app"
   ```

3. **Frontend Build Errors**
   ```bash
   # Clear cache and rebuild
   cd /opt/synapseDTE/frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

4. **Nginx 502 Bad Gateway**
   ```bash
   # Check backend is running
   curl http://localhost:8000/health
   
   # Check Nginx error log
   sudo tail -f /var/log/nginx/error.log
   ```

## Security Hardening

### 1. Firewall Setup

```bash
# Install ufw
sudo apt install -y ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw --force enable
```

### 2. Fail2ban Setup

```bash
# Install fail2ban
sudo apt install -y fail2ban

# Configure for Nginx
sudo tee /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-limit-req]
enabled = true
EOF

sudo systemctl restart fail2ban
```

## Maintenance

### Regular Tasks

1. **Weekly**: Check logs for errors
2. **Monthly**: Update system packages
3. **Quarterly**: Review and update dependencies
4. **Yearly**: Review security settings

### Update Procedure

```bash
# Backup first
/usr/local/bin/backup-synapseDTE.sh

# Update code
cd /opt/synapseDTE
git pull origin main

# Update backend
source venv/bin/activate
pip install -r scripts/deployment/requirements.txt
alembic upgrade head

# Update frontend
cd frontend
npm install
npm run build

# Restart services
sudo systemctl restart synapseDTE-backend
sudo systemctl restart synapseDTE-frontend
```

## Support

For issues:
1. Check application logs
2. Verify all services are running
3. Ensure database connectivity
4. Check disk space and memory usage
5. Review Nginx error logs