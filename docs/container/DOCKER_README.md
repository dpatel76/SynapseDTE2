# Docker Setup Guide for SynapseDTE

## Quick Start

### Prerequisites
- Docker Desktop 4.25+ or Docker Engine 24.0+
- Docker Compose 2.23+
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

### Development Setup

1. **Clone and prepare**:
```bash
git clone <repository>
cd SynapseDTE
cp .env.docker.example .env
```

2. **Update .env with your API keys**:
```bash
# Edit .env and add your keys:
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
```

3. **Start development environment**:
```bash
./scripts/docker/start-dev.sh
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Temporal UI: http://localhost:8088

### Production Setup

1. **Configure environment**:
```bash
cp .env.docker.example .env
# Edit .env and set all required values
# IMPORTANT: Change all default passwords and secrets!
```

2. **Start production environment**:
```bash
./scripts/docker/start-prod.sh
```

3. **Access the application**:
- Application: http://localhost
- API Docs: http://localhost/api/v1/docs
- Temporal UI: http://localhost:8088

## Architecture

### Services

1. **postgres** - Main application database
2. **redis** - Cache and Celery broker
3. **backend** - FastAPI application server
4. **frontend** - React application served by nginx
5. **temporal-postgres** - Temporal workflow database
6. **temporal** - Temporal workflow server
7. **temporal-ui** - Temporal web interface
8. **worker** - Temporal workflow workers (scalable)

### Networks

- **synapse-network** - Application services
- **temporal-network** - Temporal services

### Volumes

- **postgres_data** - Application database
- **redis_data** - Redis persistence
- **temporal_postgres_data** - Temporal database
- **uploads** - File uploads (bind mount)
- **logs** - Application logs (bind mount)

## Common Operations

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Scale workers
```bash
# Scale to 5 workers
docker-compose up -d --scale worker=5

# Check worker status
docker-compose ps worker
```

### Database operations
```bash
# Access PostgreSQL
docker-compose exec postgres psql -U synapse_user -d synapse_dt

# Run migrations manually
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "description"
```

### Restart services
```bash
# Restart single service
docker-compose restart backend

# Restart all services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build backend
```

### Backup database
```bash
# Backup
docker-compose exec postgres pg_dump -U synapse_user synapse_dt > backup.sql

# Restore
docker-compose exec -T postgres psql -U synapse_user synapse_dt < backup.sql
```

## Development Tools

### Enable development tools
```bash
# Start with pgAdmin and Redis Commander
docker-compose --profile tools -f docker-compose.yml -f docker-compose.dev.yml up -d

# Access tools
# pgAdmin: http://localhost:5050 (admin@synapse.local / admin)
# Redis Commander: http://localhost:8081 (admin / admin)
```

### Frontend development
```bash
# The dev setup runs frontend in development mode with hot reload
# Make changes in frontend/src and they'll reflect immediately
```

### Backend development
```bash
# Backend also supports hot reload in dev mode
# Changes to app/ directory will restart the server automatically
```

### Debugging

1. **Backend debugging**:
```python
# Add breakpoint in code
import ipdb; ipdb.set_trace()

# View in logs
docker-compose logs -f backend
```

2. **Worker debugging**:
```bash
# Set worker replicas to 1 for easier debugging
docker-compose up -d --scale worker=1

# View worker logs
docker-compose logs -f worker
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs <service-name>

# Check container status
docker ps -a

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Database connection issues
```bash
# Check if database is ready
docker-compose exec postgres pg_isready

# Check database logs
docker-compose logs postgres
```

### Port conflicts
```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Change port in .env
BACKEND_PORT=8001
```

### Clean up everything
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: Deletes all data)
docker-compose down -v

# Remove all images
docker rmi $(docker images -q synapse-*)

# Full cleanup
docker system prune -a --volumes
```

## Performance Tuning

### Docker Desktop settings
- Memory: 8GB minimum, 16GB recommended
- CPUs: 4 minimum, 8 recommended
- Disk: 20GB minimum

### Production optimizations
1. Use external PostgreSQL for better performance
2. Use external Redis cluster for high availability
3. Scale workers based on workload
4. Use CDN for frontend assets
5. Enable gzip compression in nginx

## Security Considerations

### Production checklist
- [ ] Change all default passwords in .env
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS with proper certificates
- [ ] Restrict database access
- [ ] Use Docker secrets for sensitive data
- [ ] Regular security updates
- [ ] Enable firewall rules
- [ ] Monitor access logs

### SSL/TLS Setup
```bash
# Add certificates to nginx
mkdir -p nginx/ssl
cp your-cert.pem nginx/ssl/
cp your-key.pem nginx/ssl/

# Update docker-compose.yml
# Add volume mount for nginx:
# - ./nginx/ssl:/etc/nginx/ssl:ro
```

## Monitoring

### Health checks
```bash
# Check all service health
docker-compose ps

# Backend health
curl http://localhost:8000/api/v1/health

# Frontend health
curl http://localhost/health
```

### Resource usage
```bash
# Overall stats
docker stats

# Specific service
docker stats backend
```

## Deployment

### Production deployment steps
1. Set up Docker on production server
2. Copy repository or use CI/CD
3. Configure .env with production values
4. Run security audit
5. Start services with `./scripts/docker/start-prod.sh`
6. Set up monitoring and backups
7. Configure reverse proxy/load balancer

### Updates and maintenance
```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose build
docker-compose up -d

# Zero-downtime update (backend)
docker-compose build backend
docker-compose up -d --no-deps backend
```

## Support

For issues:
1. Check service logs
2. Verify environment configuration
3. Ensure all dependencies are installed
4. Check Docker resource allocation
5. Review security settings

---

**Last Updated**: January 2025  
**Docker Compose Version**: 3.8  
**Tested With**: Docker 24.0+, Docker Compose 2.23+