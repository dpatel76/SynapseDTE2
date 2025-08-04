# Container Alembic Integration

## Overview

Alembic migrations are fully integrated into the containerized SynapseDTE2 application. The backend container automatically runs migrations on startup, ensuring the database schema is always up-to-date.

## How It Works

### 1. Container Startup Flow

```
Backend Container Start
    ↓
Wait for PostgreSQL
    ↓
Run Alembic Migrations (run_migrations.py)
    ↓
Start FastAPI Application
```

### 2. Migration Script (`scripts/docker/run_migrations.py`)

The migration script handles:
- **Fresh Database**: Detects if this is a new installation and stamps the database with the current version
- **Existing Database**: Runs any pending migrations to bring schema up-to-date
- **Error Handling**: Continues application startup even if migrations fail (with warnings)

### 3. Key Files

- `/scripts/docker/run_migrations.py` - Smart migration runner
- `/scripts/docker/backend-entrypoint.sh` - Backend startup script
- `/Dockerfile.backend` - Includes Alembic and migration scripts
- `/docker-compose.container.yml` - Main container configuration
- `/docker-compose.alembic.yml` - Optional override for migration testing

## Usage Scenarios

### Standard Container Startup

```bash
# Migrations run automatically
docker-compose -f docker-compose.container.yml up -d
```

### Run Migrations Only

```bash
# Using the migrate service
docker-compose -f docker-compose.container.yml -f docker-compose.alembic.yml run migrate
```

### Manual Migration in Running Container

```bash
# Execute in backend container
docker-compose -f docker-compose.container.yml exec backend alembic upgrade head

# Check current version
docker-compose -f docker-compose.container.yml exec backend alembic current
```

### Skip Migrations (Development)

```bash
# Set environment variable
docker-compose -f docker-compose.container.yml up -d -e SKIP_MIGRATIONS=true
```

## Adding New Migrations

### 1. Create Migration

```bash
# On local machine
export DATABASE_URL="postgresql://synapse_user:synapse_password@localhost:5433/synapse_dt"
alembic revision --autogenerate -m "add_new_feature"
```

### 2. Test Migration

```bash
# Test in container
docker-compose -f docker-compose.container.yml exec backend alembic upgrade head
```

### 3. Commit Changes

```bash
git add alembic/versions/
git commit -m "Add migration for new feature"
```

## Deployment Workflow

### Development

1. Containers start with existing database
2. Migrations run automatically
3. Application starts normally

### Production

1. Run migrations in separate step:
   ```bash
   docker-compose run migrate
   ```
2. Verify success
3. Deploy new application containers

### CI/CD Pipeline

```yaml
# Example GitHub Actions
- name: Run Migrations
  run: |
    docker-compose -f docker-compose.container.yml run migrate
    
- name: Deploy Application
  run: |
    docker-compose -f docker-compose.container.yml up -d
```

## Troubleshooting

### Migration Fails on Startup

**Symptom**: Backend container shows migration errors but continues running

**Solution**: 
1. Check logs: `docker-compose logs backend`
2. Run migrations manually: `docker-compose exec backend alembic upgrade head`
3. Check database connection settings

### Wrong Alembic Version

**Symptom**: "Can't locate revision identifier" error

**Solution**:
```bash
# Check current version
docker-compose exec backend alembic current

# Force to specific version
docker-compose exec backend alembic stamp 3be61ad5f00f
```

### Fresh Database Not Recognized

**Symptom**: Migrations try to create existing tables

**Solution**: The migration script should detect this and stamp the database. If not:
```bash
docker-compose exec backend alembic stamp head
```

## Environment Variables

- `DATABASE_URL` - Full PostgreSQL connection string
- `RUN_MIGRATIONS` - Set to "false" to skip migrations
- `ALEMBIC_CONFIG` - Path to alembic.ini (default: /app/alembic.ini)

## Best Practices

1. **Always Test Migrations**: Run in development before production
2. **Backup Before Major Changes**: Especially for data migrations
3. **Monitor Startup Logs**: Check for migration warnings
4. **Use Migration Service**: For production deployments
5. **Version Control**: Commit migration files with code changes

## Migration Safety

The integration is designed to be safe:
- Migrations run in a transaction (rollback on error)
- Application starts even if migrations fail
- Clear logging of all migration activities
- Automatic detection of database state

## Future Improvements

- [ ] Migration rollback support in containers
- [ ] Automated migration testing
- [ ] Migration performance metrics
- [ ] Schema validation after migrations