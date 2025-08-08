# Temporal Database Architecture in SynapseDTE

## Overview

SynapseDTE uses **TWO SEPARATE DATABASES**:

1. **Main Application Database** (`synapse_dt`) - Port 5432
2. **Temporal Server Database** (`temporal`) - Port 5434

## Database Separation

### Main Application Database (`synapse_dt`)
- **Purpose**: Stores all application data
- **Port**: 5432 (PostgreSQL default)
- **Contains**:
  - User data, roles, permissions
  - Test cycles, reports, observations
  - Workflow metadata (10 tables prefixed with `workflow_`)
  - Audit logs, documents, configurations

### Temporal Server Database (`temporal`)
- **Purpose**: Stores Temporal's internal workflow execution state
- **Port**: 5434 (custom to avoid conflicts)
- **Contains**:
  - Workflow execution history
  - Task queues
  - Activity execution records
  - Temporal's internal state management
  - Visibility data for Temporal UI

## Why Separate Databases?

1. **Isolation**: Temporal's high-volume internal operations don't impact application performance
2. **Scaling**: Each database can be scaled independently
3. **Maintenance**: Separate backup strategies and maintenance windows
4. **Security**: Different access controls and permissions
5. **Best Practice**: Temporal recommends separate database for production

## Workflow Tables Clarification

### In Main Database (`synapse_dt`):
The 10 `workflow_*` tables are **application-specific** metadata:
```sql
workflow_activities          -- Track application workflow activities
workflow_activity_dependencies -- Define activity relationships
workflow_activity_histories  -- Audit trail for activities
workflow_activity_templates  -- Predefined activity templates
workflow_alerts             -- Application-level alerts
workflow_executions         -- High-level execution tracking
workflow_metrics           -- Business metrics
workflow_phases            -- Application phase management
workflow_steps             -- Business process steps
workflow_transitions       -- State machine transitions
```

### In Temporal Database (`temporal`):
Temporal's internal tables (auto-created):
```sql
namespaces               -- Temporal namespaces
executions              -- Workflow execution state
current_executions      -- Active workflows
history_node            -- Event history
activities              -- Activity state
task_queues            -- Task distribution
visibility             -- Search and UI data
... (30+ internal tables)
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────┐
│                 Application Layer                │
│                                                  │
│  ┌─────────────┐         ┌──────────────────┐  │
│  │   FastAPI   │         │  Temporal Worker │  │
│  │   Backend   │         │    Processes     │  │
│  └──────┬──────┘         └────────┬─────────┘  │
│         │                          │             │
│         │                          │             │
└─────────┼──────────────────────────┼────────────┘
          │                          │
          ▼                          ▼
┌─────────────────────┐    ┌─────────────────────┐
│  Main App Database  │    │  Temporal Database  │
│    (synapse_dt)     │    │     (temporal)      │
│     Port: 5432      │    │     Port: 5434      │
│                     │    │                     │
│  • User data        │    │  • Workflow state   │
│  • Test results     │    │  • Execution history│
│  • Workflow metadata│    │  • Task queues      │
│  • Audit logs       │    │  • Internal state   │
└─────────────────────┘    └─────────────────────┘
```

## Docker Compose Setup

From `docker-compose.temporal.yml`:

```yaml
services:
  # Temporal's PostgreSQL (SEPARATE DATABASE)
  temporal-postgresql:
    image: postgres:12
    environment:
      POSTGRES_DB: temporal
      POSTGRES_USER: temporal
      POSTGRES_PASSWORD: temporal
    ports:
      - "5434:5432"  # Different external port!
    volumes:
      - temporal_postgres_data:/var/lib/postgresql/data

  # Temporal Server
  temporal-server:
    image: temporalio/auto-setup:latest
    depends_on:
      - temporal-postgresql
    environment:
      - DB=postgresql
      - DB_PORT=5432  # Internal container port
      - POSTGRES_HOST=temporal-postgresql
      - POSTGRES_DB=temporal
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
    ports:
      - "7233:7233"

  # Temporal UI
  temporal-ui:
    image: temporalio/ui:latest
    environment:
      - TEMPORAL_ADDRESS=temporal-server:7233
    ports:
      - "8088:8080"
```

## Connection Configuration

### Main Application (.env):
```bash
# Main database
DATABASE_URL=postgresql://postgres:password@localhost:5432/synapse_dt

# Temporal connection (to server, not database)
TEMPORAL_HOST=localhost:7233
TEMPORAL_NAMESPACE=default
```

### Temporal Database (Docker managed):
```bash
# Automatically configured by docker-compose
# Direct access (if needed):
psql -U temporal -h localhost -p 5434 -d temporal
```

## Important Notes

1. **This export contains ONLY the main database** (`synapse_dt`)
2. **Temporal database is created automatically** when you run `docker-compose up`
3. **Never mix data** between the two databases
4. **Workflow metadata != Workflow execution data**
   - Metadata (main DB) = business-level tracking
   - Execution (Temporal DB) = technical execution state

## Checking Both Databases

```bash
# Check main application database
psql -U postgres -p 5432 -d synapse_dt -c "\dt" | grep workflow

# Check Temporal database (after Docker startup)
psql -U temporal -h localhost -p 5434 -d temporal -c "\dt"

# View running Temporal workflows
docker exec -it temporal-server temporal workflow list
```

## Backup Considerations

1. **Main Database**: Use the exports in this directory
2. **Temporal Database**: 
   ```bash
   # Backup Temporal data
   docker exec temporal-postgresql pg_dump -U temporal temporal > temporal_backup.sql
   
   # Or use Docker volumes
   docker run --rm -v temporal_postgres_data:/data -v $(pwd):/backup \
     alpine tar czf /backup/temporal_data.tar.gz /data
   ```

## Recovery Scenarios

### Main Database Loss:
- Use exports in this directory
- Application data is restored
- Workflow metadata is restored

### Temporal Database Loss:
- Running workflows will be lost
- History will be lost
- Application can create new workflows
- Consider workflow replay from application events

### Best Practice:
- Backup both databases regularly
- Test recovery procedures
- Monitor both databases separately
- Keep Temporal version consistent