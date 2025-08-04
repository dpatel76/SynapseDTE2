# SynapseDTE Quick Start Guide

This guide helps you get SynapseDTE running quickly on a new server.

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- sudo access
- 8GB+ RAM
- 50GB+ storage

## One-Line Installation

For a quick setup, run this command:

```bash
curl -sSL https://raw.githubusercontent.com/your-repo/SynapseDTE/main/scripts/install.sh | bash
```

## Manual Quick Setup

### 1. Install Dependencies (10 minutes)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3.9 python3.9-venv python3-pip \
    postgresql postgresql-contrib \
    nodejs npm \
    nginx redis-server \
    build-essential git curl

# Install Node.js 18.x (if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Setup Database (5 minutes)

```bash
# Create database user and database
sudo -u postgres psql << EOF
CREATE USER synapse_user WITH PASSWORD 'changeme123';
ALTER USER synapse_user CREATEDB;
CREATE DATABASE synapse_dt OWNER synapse_user;
EOF
```

### 3. Clone and Setup Application (10 minutes)

```bash
# Clone repository
sudo mkdir -p /opt/synapseDTE
cd /opt/synapseDTE
git clone https://github.com/your-repo/SynapseDTE.git .

# Setup Python environment
python3.9 -m venv venv
source venv/bin/activate
pip install -r scripts/deployment/requirements.txt

# Setup database schema
cd migrations/schema
sudo -u postgres psql -d synapse_dt -f complete_schema.sql
sudo -u postgres psql -d synapse_dt -f seed_data.sql

# Configure environment
cd /opt/synapseDTE
cp .env.example .env
# Edit .env file with your settings
```

### 4. Start Services (5 minutes)

```bash
# Backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Frontend
cd frontend
npm install
npm run build
npx serve -s build -l 3000 &
```

### 5. Configure Nginx

```bash
sudo tee /etc/nginx/sites-available/synapseDTE << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api {
        rewrite ^/api(.*)\$ \$1 break;
        proxy_pass http://localhost:8000;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/synapseDTE /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Access Application

1. Open browser to `http://your-server-ip`
2. Login with:
   - Email: `admin@example.com`
   - Password: `password123`

## Docker Alternative

If you prefer Docker:

```bash
# Clone repository
git clone https://github.com/your-repo/SynapseDTE.git
cd SynapseDTE

# Run with docker-compose
docker-compose up -d
```

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U synapse_user -d synapse_dt -h localhost
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :3000

# Kill process if needed
sudo kill -9 <PID>
```

### Frontend Build Errors
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Next Steps

- Review [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for production setup
- Configure SSL/HTTPS
- Setup monitoring and backups
- Review security settings

## Support

For issues:
1. Check logs: `journalctl -xe`
2. Verify services: `systemctl status postgresql nginx`
3. Check disk space: `df -h`
4. Review application logs in `/var/log/`