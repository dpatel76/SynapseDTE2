# SynapseDTE Containerization Plan - Phase 1

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Current Application Analysis](#current-application-analysis)
3. [Containerization Strategy](#containerization-strategy)
4. [Architecture Design](#architecture-design)
5. [Service Breakdown](#service-breakdown)
6. [Network Architecture](#network-architecture)
7. [Data Persistence Strategy](#data-persistence-strategy)
8. [Environment Configuration](#environment-configuration)
9. [Build and Deployment Workflow](#build-and-deployment-workflow)
10. [Testing Strategy](#testing-strategy)
11. [Risk Assessment](#risk-assessment)
12. [Implementation Timeline](#implementation-timeline)

## Executive Summary

This document outlines a comprehensive containerization strategy for the SynapseDTE application, a complex end-to-end data testing system built with React JS (frontend), FastAPI/Python (backend), PostgreSQL (database), and Temporal (workflow orchestration).

### Key Objectives
- Containerize all application components
- Support both development and production environments
- Ensure zero data loss during container lifecycle
- Maintain high availability and scalability
- Simplify deployment and development workflows

## Current Application Analysis

### Technology Stack Overview

#### Frontend
- **Framework**: React 19.1.0 with TypeScript
- **Build Tool**: React Scripts 5.0.1
- **UI Library**: Material-UI v7
- **State Management**: React Query v5
- **Routing**: React Router v7
- **Key Dependencies**: Axios, Chart.js, React Hook Form
- **Port**: 3000 (development)

#### Backend
- **Framework**: FastAPI 0.104.1
- **Language**: Python 3.11+ (assumed)
- **Server**: Uvicorn with async support
- **Database ORM**: SQLAlchemy 2.0.23 with async support
- **Authentication**: JWT with python-jose
- **Background Tasks**: Celery with Redis
- **LLM Integration**: Anthropic Claude, Google Gemini
- **Port**: 8000

#### Database
- **Primary**: PostgreSQL 14+ 
- **Async Driver**: asyncpg
- **Migration Tool**: Alembic
- **Connection Pool**: SQLAlchemy pool management

#### Workflow Engine
- **System**: Temporal.io
- **Components**: Server, Worker, UI, Admin Tools
- **Database**: Separate PostgreSQL instance
- **Ports**: 7233 (gRPC), 8088 (UI)

#### Supporting Services
- **Cache/Queue**: Redis
- **File Storage**: Local filesystem (./uploads)
- **Email**: SMTP integration

### Current Infrastructure Challenges

1. **Manual Setup**: Complex multi-service setup requiring multiple terminals
2. **Environment Management**: Manual .env file configuration
3. **Service Dependencies**: Complex startup order requirements
4. **Development Friction**: Difficult to onboard new developers
5. **Production Deployment**: No standardized deployment process

## Containerization Strategy

### Multi-Stage Build Approach

We will use multi-stage Docker builds to:
1. Minimize final image sizes
2. Separate build dependencies from runtime
3. Cache dependencies efficiently
4. Ensure security by not including build tools in production

### Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Docker Network                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐   │
│  │   Nginx     │  │  Frontend   │  │      Backend         │   │
│  │  (Reverse   │──│   (React)   │  │    (FastAPI)         │   │
│  │   Proxy)    │  │  Port:3000  │  │    Port:8000         │   │
│  └─────────────┘  └─────────────┘  └──────────────────────┘   │
│         │                               │         │              │
│         └───────────────────────────────┘         │              │
│                                                   │              │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────▼──────────┐   │
│  │ PostgreSQL  │  │    Redis    │  │  Temporal Worker      │   │
│  │   Main DB   │  │  Port:6379  │  │  (Python Process)     │   │
│  │  Port:5432  │  └─────────────┘  └──────────────────────┘   │
│  └─────────────┘                           │                    │
│                                            │                    │
│  ┌─────────────────────────────────────────▼─────────────────┐ │
│  │                  Temporal Services                          │ │
│  ├─────────────┬──────────────┬──────────────┬──────────────┤ │
│  │  Temporal   │   Temporal   │   Temporal   │  PostgreSQL  │ │
│  │   Server    │      UI      │  Admin Tools │  (Temporal)  │ │
│  │  Port:7233  │  Port:8088   │              │  Port:5434   │ │
│  └─────────────┴──────────────┴──────────────┴──────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Architecture Design

### Container Images

1. **synapse-frontend**
   - Base: node:20-alpine (build), nginx:alpine (runtime)
   - Multi-stage build for optimization
   - Static file serving with nginx

2. **synapse-backend**
   - Base: python:3.11-slim
   - Multi-stage build with poetry/pip
   - Includes all Python dependencies

3. **synapse-worker**
   - Base: Same as backend
   - Runs Temporal worker processes
   - Can scale horizontally

4. **synapse-nginx**
   - Base: nginx:alpine
   - Reverse proxy configuration
   - SSL termination (production)

### Base Images Selection Rationale

- **Alpine Linux**: Minimal size, security-focused
- **Official Images**: Well-maintained, security updates
- **Slim Variants**: Reduced attack surface
- **Version Pinning**: Reproducible builds

## Service Breakdown

### 1. Frontend Service (synapse-frontend)
```yaml
Container Specifications:
- Base Image: node:20-alpine (build), nginx:alpine (runtime)
- Build Context: ./frontend
- Exposed Port: 80
- Environment Variables:
  - REACT_APP_API_URL
  - REACT_APP_TEMPORAL_UI_URL
- Volume Mounts: None (static build)
- Health Check: HTTP GET /
```

### 2. Backend Service (synapse-backend)
```yaml
Container Specifications:
- Base Image: python:3.11-slim
- Build Context: ./
- Exposed Port: 8000
- Environment Variables: All from .env
- Volume Mounts:
  - ./uploads:/app/uploads (persistent storage)
  - ./logs:/app/logs (optional, for debugging)
- Health Check: HTTP GET /api/v1/health
- Dependencies: PostgreSQL, Redis, Temporal
```

### 3. Temporal Worker Service (synapse-worker)
```yaml
Container Specifications:
- Base Image: python:3.11-slim (same as backend)
- Build Context: ./
- Command: python -m app.temporal.worker
- Environment Variables: Subset of backend
- Volume Mounts: Shared with backend
- Health Check: Custom worker health endpoint
- Scaling: Horizontal (multiple instances)
```

### 4. PostgreSQL Service (synapse-postgres)
```yaml
Container Specifications:
- Base Image: postgres:15-alpine
- Exposed Port: 5432
- Environment Variables:
  - POSTGRES_DB
  - POSTGRES_USER
  - POSTGRES_PASSWORD
- Volume Mounts:
  - postgres_data:/var/lib/postgresql/data
  - ./scripts/db/init:/docker-entrypoint-initdb.d
- Health Check: pg_isready
```

### 5. Redis Service (synapse-redis)
```yaml
Container Specifications:
- Base Image: redis:7-alpine
- Exposed Port: 6379
- Volume Mounts:
  - redis_data:/data
- Config: Custom redis.conf for persistence
- Health Check: redis-cli ping
```

### 6. Nginx Service (synapse-nginx)
```yaml
Container Specifications:
- Base Image: nginx:alpine
- Exposed Ports: 80, 443
- Volume Mounts:
  - ./nginx/conf.d:/etc/nginx/conf.d
  - ./nginx/ssl:/etc/nginx/ssl (production)
- Health Check: HTTP GET /health
```

### 7. Temporal Services (Containerized)
As requested, we will containerize the entire Temporal stack:

```yaml
Temporal Server Specifications:
- Base Image: temporalio/server:1.22.4
- Exposed Port: 7233
- Environment: Production configurations
- Dependencies: PostgreSQL (Temporal)
- Security: mTLS enabled

Temporal UI Specifications:
- Base Image: temporalio/ui:latest
- Exposed Port: 8088
- Environment: Read-only access
- Security: Authentication required

Temporal PostgreSQL:
- Base Image: postgres:15-alpine
- Exposed Port: 5434 (non-standard)
- Dedicated database instance
- Separate from main application DB
```

## Network Architecture

### Network Topology
```yaml
Networks:
  synapse-network:
    - All application services
    - Internal communication only
    
  temporal-network:
    - Temporal services
    - Temporal worker
    - Bridge to synapse-network
    
  public-network:
    - Nginx only
    - External access point
```

### Service Discovery
- Internal DNS using container names
- Environment variable injection
- Health check based routing

### Security Considerations
- No direct database exposure
- API access only through reverse proxy
- Network isolation between services
- Secrets management via environment

## Data Persistence Strategy

### Volume Management

1. **Database Volumes**
   ```yaml
   Named Volumes:
   - postgres_data: Main application database
   - postgres_temporal_data: Temporal database
   - redis_data: Redis persistence
   ```

2. **Application Volumes**
   ```yaml
   Bind Mounts (Development):
   - ./uploads:/app/uploads
   - ./logs:/app/logs
   - ./frontend/src:/app/src (hot reload)
   - ./app:/app/app (hot reload)
   
   Named Volumes (Production):
   - uploads_data:/app/uploads
   - logs_data:/app/logs
   ```

### Backup Strategy
- Automated PostgreSQL backups
- Redis persistence configuration
- Upload directory synchronization
- Volume snapshot capabilities

## Environment Configuration

### Development Configuration
```yaml
# docker-compose.dev.yml
- Hot reload for frontend/backend
- Exposed database ports for debugging
- Volume mounts for code
- Debug logging enabled
- Temporal UI accessible
```

### Production Configuration
```yaml
# docker-compose.yml
- Optimized images
- No code volumes
- Restricted port exposure
- Production logging
- Health checks enabled
- Restart policies
```

### Environment Variables Management
```
Structure:
├── .env.example        # Template with all variables
├── .env.development    # Development defaults
├── .env.production     # Production template
├── .env.local          # Local overrides (gitignored)
```

## Build and Deployment Workflow

### Build Process
```bash
# Development Build
docker-compose -f docker-compose.dev.yml build

# Production Build
docker-compose build --no-cache

# Multi-platform Build
docker buildx build --platform linux/amd64,linux/arm64
```

### Deployment Process
```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production
docker-compose up -d

# Rolling Update
docker-compose up -d --no-deps --build <service>
```

### CI/CD Integration
- GitHub Actions for automated builds
- Container registry publication
- Automated testing in containers
- Environment-specific deployments

## Testing Strategy

### Container Testing Levels

1. **Build Verification**
   - Dockerfile linting
   - Security scanning (Trivy)
   - Size optimization checks

2. **Service Testing**
   - Individual container startup
   - Health check validation
   - Port accessibility

3. **Integration Testing**
   - Inter-service communication
   - Database migrations
   - Temporal workflow execution

4. **End-to-End Testing**
   - Full application flow
   - Data persistence verification
   - Performance benchmarking

### Test Implementation
```yaml
# docker-compose.test.yml
- Isolated test network
- Test database instances
- Mock external services
- Automated test runners
```

## Risk Assessment

### Technical Risks
1. **Data Loss**: Mitigated by proper volume management
2. **Service Dependencies**: Handled by health checks and restart policies
3. **Resource Constraints**: Addressed by resource limits
4. **Network Issues**: Resolved by proper network configuration

### Mitigation Strategies
- Comprehensive backup procedures
- Graceful shutdown handling
- Rolling update capabilities
- Monitoring and alerting setup

## Implementation Timeline

### Phase 1 Completion Checklist
- [x] Application structure analysis
- [x] Dependency identification
- [x] Architecture design
- [x] Service specification
- [x] Network planning
- [x] Volume strategy
- [x] Environment configuration
- [x] Testing approach

### Next Steps (Phase 2 - Pending Approval)
1. Create Dockerfiles for each service
2. Develop docker-compose configurations
3. Implement health checks
4. Setup environment templates
5. Create build and deployment scripts
6. Document operational procedures

## Recommendations

1. **Start with Development Environment**: Focus on developer experience first
2. **Incremental Migration**: Containerize services one at a time
3. **Maintain Backward Compatibility**: Support both containerized and native development
4. **Invest in Monitoring**: Add observability from the start
5. **Automate Everything**: Scripts for common operations

## Security Considerations

For comprehensive security best practices, please refer to the [Security Best Practices](./SECURITY_BEST_PRACTICES.md) document which covers:

- Container hardening and runtime security
- Network isolation and firewall rules
- Secrets management (Docker Secrets, Vault, AWS Secrets Manager)
- Database security and encryption
- API security with JWT and rate limiting
- Temporal security with mTLS
- Monitoring and audit logging
- Compliance requirements (GDPR, SOC2, HIPAA)
- Incident response procedures

### Key Security Highlights

1. **Zero Trust Architecture**: All services communicate over encrypted channels
2. **Least Privilege**: Each container runs with minimal required permissions
3. **Defense in Depth**: Multiple layers of security controls
4. **Continuous Monitoring**: Real-time security event detection
5. **Automated Compliance**: Regular security scans and audits

## Conclusion

This containerization plan provides a comprehensive roadmap for modernizing the SynapseDTE deployment architecture. The proposed solution addresses all current pain points while providing a foundation for future scalability and maintainability.

The multi-service architecture with proper separation of concerns, combined with development and production configurations, will significantly improve both developer experience and operational efficiency.

**Key Decisions Made:**
- ✅ Temporal server will be fully containerized
- ✅ Comprehensive security best practices documented
- ✅ Multi-stage builds for all services
- ✅ Separate development and production configurations

---

**Document Version**: 1.1  
**Date**: January 2025  
**Status**: Awaiting Approval for Phase 2 Implementation