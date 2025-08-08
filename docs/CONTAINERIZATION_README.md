# SynapseDTE Containerization Guide

This guide provides instructions for running SynapseDTE in a fully containerized environment.

## Overview

The containerized setup includes:
- **Frontend**: React application served by Nginx
- **Backend**: FastAPI application with Uvicorn
- **PostgreSQL**: Main database (synapse_dt)
- **Redis**: Caching and task queue
- **Temporal**: Workflow orchestration with separate PostgreSQL
- **Worker**: Temporal workflow workers
- **Nginx**: Reverse proxy (optional)

## Port Configuration

All ports are incremented by 1 from the default to avoid conflicts:

| Service | Internal Port | External Port | Description |
|---------|--------------|---------------|-------------|
| Frontend | 80 | 3001 | React application |
| Backend | 8000 | 8001 | FastAPI application |
| PostgreSQL | 5432 | 5433 | Main database |
| Redis | 6379 | 6380 | Cache/queue |
| Temporal | 7233 | 7234 | Workflow server |
| Temporal UI | 8080 | 8089 | Temporal dashboard |
| Temporal PostgreSQL | 5432 | 5435 | Temporal database |
| Nginx | 80/443 | 81/444 | Reverse proxy |

## Quick Start

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd SynapseDTE2
   ```

2. **Set up environment**:
   ```bash
   cp .env.container .env
   # Edit .env file to add your API keys
   ```

3. **Start all services**:
   ```bash
   ./start-containers.sh
   ```

4. **Access the application**:
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8001/api/v1
   - Temporal UI: http://localhost:8089

5. **Default credentials**:
   - Email: `tester@example.com`
   - Password: `password123`

## Environment Configuration

### Required Configuration

Edit `.env` file and set:
```env
# LLM API Keys (required)
ANTHROPIC_API_KEY=your_actual_key_here
GOOGLE_API_KEY=your_actual_key_here

# Database passwords (change for production)
DATABASE_PASSWORD=secure_password_here
REDIS_PASSWORD=secure_redis_password_here
TEMPORAL_POSTGRES_PASSWORD=secure_temporal_password_here

# Application secret (change for production)
SECRET_KEY=generate_secure_random_string_here
```

### Optional Configuration

See `.env.container` for all available options including:
- Email/SMTP settings
- Worker scaling
- Logging configuration
- Performance tuning

## Database Initialization

The database is automatically initialized on first startup using:
- Schema: `scripts/database/08032025/01_complete_schema.sql`
- Seeds: `scripts/database/08032025/03_minimal_seeds.sql`

This includes:
- Complete table structure with all relationships
- RBAC roles and permissions
- Test users with proper authentication
- Core lookup data (LOBs, etc.)

## Common Commands

### View logs:
```bash
# All services
docker-compose -f docker-compose.container.yml logs -f

# Specific service
docker-compose -f docker-compose.container.yml logs -f backend
```

### Stop services:
```bash
./stop-containers.sh
```

### Clean everything (including data):
```bash
docker-compose -f docker-compose.container.yml down -v
```

### Rebuild after code changes:
```bash
docker-compose -f docker-compose.container.yml build
docker-compose -f docker-compose.container.yml up -d
```

### Access database:
```bash
docker-compose -f docker-compose.container.yml exec postgres psql -U synapse_user -d synapse_dt
```

### Run migrations manually:
```bash
docker-compose -f docker-compose.container.yml exec backend alembic upgrade head
```

## Troubleshooting

### Services not starting

1. Check logs:
   ```bash
   docker-compose -f docker-compose.container.yml logs [service-name]
   ```

2. Verify ports are not in use:
   ```bash
   lsof -i :3001  # Frontend
   lsof -i :8001  # Backend
   lsof -i :5433  # PostgreSQL
   ```

3. Check Docker resources:
   ```bash
   docker system df
   docker system prune -a  # Clean unused resources
   ```

### Database issues

1. Reset database:
   ```bash
   docker-compose -f docker-compose.container.yml down -v
   docker-compose -f docker-compose.container.yml up -d postgres
   ```

2. Check initialization:
   ```bash
   docker-compose -f docker-compose.container.yml exec postgres psql -U synapse_user -d synapse_dt -c "\dt"
   ```

### Permission errors

Ensure proper file permissions:
```bash
chmod +x start-containers.sh stop-containers.sh
chmod +x scripts/docker/bypass_migrations.py
```

## Development Mode

For development with hot-reload:

1. Create `docker-compose.override.yml`:
   ```yaml
   version: '3.8'
   services:
     backend:
       volumes:
         - ./app:/app/app
       environment:
         - RELOAD=true
     
     frontend:
       build:
         context: .
         dockerfile: Dockerfile.frontend.dev
       volumes:
         - ./frontend/src:/app/src
   ```

2. Start with:
   ```bash
   docker-compose -f docker-compose.container.yml up -d
   ```

## Production Deployment

For production:

1. Use proper secrets management
2. Enable SSL/TLS in Nginx
3. Set up monitoring and logging
4. Configure backups for PostgreSQL
5. Use container registry for images
6. Implement health checks and auto-scaling

## Architecture Notes

- **Database**: Uses PostgreSQL 15 with proper initialization scripts
- **Caching**: Redis configured with persistence
- **Workflows**: Temporal with separate PostgreSQL instance
- **Workers**: Scalable Temporal workers (default: 2 replicas)
- **Frontend**: Production React build served by Nginx
- **API**: FastAPI with Uvicorn workers
- **Proxy**: Optional Nginx reverse proxy with rate limiting

## Security Considerations

1. Change all default passwords in `.env`
2. Use secrets management in production
3. Enable HTTPS with proper certificates
4. Implement network policies
5. Regular security updates for base images
6. Audit container permissions

## Support

For issues or questions:
1. Check logs first
2. Review this documentation
3. Check existing GitHub issues
4. Create new issue with details