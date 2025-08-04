# Production Security Best Practices for Containerized SynapseDTE

## Table of Contents
1. [Overview](#overview)
2. [Container Security](#container-security)
3. [Network Security](#network-security)
4. [Secrets Management](#secrets-management)
5. [Database Security](#database-security)
6. [API Security](#api-security)
7. [Temporal Security](#temporal-security)
8. [Monitoring & Auditing](#monitoring--auditing)
9. [Compliance & Governance](#compliance--governance)
10. [Incident Response](#incident-response)

## Overview

This document outlines security best practices for deploying SynapseDTE in a production containerized environment. These practices follow industry standards including OWASP, CIS Docker Benchmark, and NIST guidelines.

## Container Security

### 1. Base Image Security

```dockerfile
# ✅ GOOD: Use specific, minimal base images
FROM python:3.11-slim-bookworm@sha256:specific-hash

# ❌ BAD: Using latest or full images
FROM python:latest
```

**Best Practices:**
- Use official, minimal base images (alpine, slim, distroless)
- Pin image versions with SHA256 digests
- Regularly update base images for security patches
- Scan images for vulnerabilities using tools like Trivy or Snyk

### 2. Build-Time Security

```dockerfile
# Multi-stage build for security
FROM python:3.11-slim-bookworm as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better caching)
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim-bookworm

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy only necessary files
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser ./app /app

# Switch to non-root user
USER appuser

# Set security headers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/appuser/.local/bin:$PATH
```

### 3. Runtime Security

```yaml
# docker-compose.yml security configurations
services:
  backend:
    # Read-only root filesystem
    read_only: true
    
    # Temporary directories for runtime
    tmpfs:
      - /tmp
      - /var/run
    
    # Drop all capabilities, add only required
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    
    # Security options
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined  # Or custom profile
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### 4. Container Hardening Checklist

- [ ] Run as non-root user
- [ ] Use read-only root filesystem
- [ ] Drop unnecessary capabilities
- [ ] Set resource limits
- [ ] Enable security options
- [ ] Disable inter-container communication where not needed
- [ ] Use health checks for all services
- [ ] Sign and verify images
- [ ] Implement vulnerability scanning in CI/CD

## Network Security

### 1. Network Isolation

```yaml
networks:
  frontend:
    driver: bridge
    internal: false  # Needs external access
    
  backend:
    driver: bridge
    internal: true   # No external access
    
  database:
    driver: bridge
    internal: true   # Isolated network
```

### 2. Service Communication

```nginx
# nginx.conf with security headers
server {
    listen 443 ssl http2;
    server_name synapse.example.com;
    
    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline';" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
}
```

### 3. Firewall Rules

```yaml
# Host-level firewall (iptables/ufw)
# Only expose necessary ports
- 80/tcp   # HTTP (redirect to HTTPS)
- 443/tcp  # HTTPS
- 22/tcp   # SSH (restricted source IPs)
```

## Secrets Management

### 1. Environment Variables

```bash
# ❌ BAD: Secrets in docker-compose.yml
environment:
  - DATABASE_PASSWORD=secretpassword

# ✅ GOOD: Use Docker secrets
secrets:
  db_password:
    external: true
    
# ✅ GOOD: Use external secret management
environment:
  - DATABASE_PASSWORD_FILE=/run/secrets/db_password
```

### 2. Secret Storage Solutions

**Option 1: Docker Swarm Secrets**
```bash
# Create secret
echo "mypassword" | docker secret create db_password -

# Use in service
services:
  backend:
    secrets:
      - db_password
    environment:
      - DATABASE_PASSWORD_FILE=/run/secrets/db_password
```

**Option 2: HashiCorp Vault**
```python
# Vault integration in app
import hvac

client = hvac.Client(url='https://vault.example.com')
client.token = os.environ['VAULT_TOKEN']
secret = client.read('secret/data/database')
db_password = secret['data']['data']['password']
```

**Option 3: AWS Secrets Manager / Azure Key Vault**
```python
# AWS Secrets Manager example
import boto3

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='synapse/database')
db_password = json.loads(response['SecretString'])['password']
```

### 3. Secret Rotation

```yaml
# Implement automatic secret rotation
- Database passwords: 90 days
- API keys: 180 days
- JWT secrets: 365 days
- Certificates: Before expiration
```

## Database Security

### 1. PostgreSQL Hardening

```sql
-- Create restricted database user
CREATE USER synapse_app WITH PASSWORD 'complex-password';
GRANT CONNECT ON DATABASE synapse_db TO synapse_app;
GRANT USAGE ON SCHEMA public TO synapse_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO synapse_app;

-- Enable SSL
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = '/var/lib/postgresql/server.crt';
ALTER SYSTEM SET ssl_key_file = '/var/lib/postgresql/server.key';

-- Connection limits
ALTER ROLE synapse_app CONNECTION LIMIT 100;

-- Enable logging
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_statement = 'mod';
```

### 2. Database Network Security

```yaml
# PostgreSQL container configuration
postgres:
  image: postgres:15-alpine
  environment:
    - POSTGRES_PASSWORD_FILE=/run/secrets/db_password
    - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256 --auth-local=trust
  networks:
    - database  # Isolated network
  volumes:
    - ./postgresql.conf:/etc/postgresql/postgresql.conf:ro
    - postgres_data:/var/lib/postgresql/data
```

### 3. Backup Security

```bash
#!/bin/bash
# Encrypted backup script
BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"

# Create backup
pg_dump -h postgres -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_FILE

# Encrypt backup
openssl enc -aes-256-cbc -salt -in $BACKUP_FILE -out $BACKUP_FILE.enc -k $BACKUP_ENCRYPTION_KEY

# Upload to secure storage
aws s3 cp $BACKUP_FILE.enc s3://secure-backup-bucket/ --server-side-encryption

# Cleanup
rm $BACKUP_FILE
```

## API Security

### 1. Authentication & Authorization

```python
# JWT with refresh tokens
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        # Verify JWT
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_aud": True}
        )
        
        # Check token expiration
        if payload['exp'] < datetime.utcnow().timestamp():
            raise HTTPException(status_code=401, detail="Token expired")
            
        # Verify user permissions
        if not check_permissions(payload['sub'], payload['permissions']):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
            
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2. Rate Limiting

```python
# Redis-based rate limiting
from fastapi import Request
from fastapi.responses import JSONResponse
import redis
import time

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    try:
        requests = redis_client.incr(key)
        if requests == 1:
            redis_client.expire(key, 60)  # 1 minute window
            
        if requests > 100:  # 100 requests per minute
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
    except redis.RedisError:
        # Fail open if Redis is down
        pass
        
    response = await call_next(request)
    return response
```

### 3. Input Validation

```python
# Pydantic model with security validations
from pydantic import BaseModel, validator, constr
import re

class UserInput(BaseModel):
    username: constr(min_length=3, max_length=50, regex='^[a-zA-Z0-9_-]+$')
    email: EmailStr
    password: constr(min_length=12, max_length=128)
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain special character')
        return v
    
    @validator('*', pre=True)
    def prevent_xss(cls, v):
        if isinstance(v, str):
            # Basic XSS prevention
            dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
            if any(pattern in v.lower() for pattern in dangerous_patterns):
                raise ValueError('Input contains potentially dangerous content')
        return v
```

## Temporal Security

### 1. Temporal Server Security

```yaml
# Temporal server configuration
temporal:
  image: temporalio/server:1.22.4
  environment:
    - ENABLE_ES=true  # Enable Elasticsearch
    - ES_SCHEME=https
    - ES_USER=temporal
    - ES_PWD_FILE=/run/secrets/es_password
    - DYNAMIC_CONFIG_FILE_PATH=/etc/temporal/dynamic_config.yaml
  volumes:
    - ./temporal/dynamic_config.yaml:/etc/temporal/dynamic_config.yaml:ro
  secrets:
    - es_password
    - temporal_tls_cert
    - temporal_tls_key
```

### 2. mTLS Configuration

```yaml
# dynamic_config.yaml for Temporal
system.rps:
  - value: 1000
    
system.workerActivitiesPerSecond:
  - value: 1000
    
frontend.enableClientVersionCheck:
  - value: true
    
frontend.tls:
  - value:
      certFile: /run/secrets/temporal_tls_cert
      keyFile: /run/secrets/temporal_tls_key
      requireClientAuth: true
      clientCaFiles:
        - /run/secrets/temporal_client_ca
```

### 3. Worker Security

```python
# Secure Temporal worker configuration
from temporalio.client import Client, TLSConfig

# Configure mTLS
tls_config = TLSConfig(
    client_cert=open("/run/secrets/worker_cert").read(),
    client_private_key=open("/run/secrets/worker_key").read(),
    server_root_ca_cert=open("/run/secrets/temporal_ca").read(),
    server_name="temporal.synapse.internal"
)

# Create secure client
client = await Client.connect(
    "temporal:7233",
    namespace="synapse-production",
    tls=tls_config,
    data_converter=EncryptedDataConverter()  # Encrypt payloads
)
```

## Monitoring & Auditing

### 1. Security Monitoring Stack

```yaml
# Security monitoring services
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--web.enable-admin-api'
      - '--web.enable-lifecycle'
    
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD_FILE=/run/secrets/grafana_password
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_AUTH_DISABLE_SIGNOUT_MENU=true
    
  falco:
    image: falcosecurity/falco:latest
    privileged: true
    volumes:
      - /var/run/docker.sock:/host/var/run/docker.sock
      - /proc:/host/proc:ro
      - /boot:/host/boot:ro
      - /lib/modules:/host/lib/modules:ro
      - /usr:/host/usr:ro
```

### 2. Audit Logging

```python
# Structured audit logging
import structlog
from fastapi import Request

logger = structlog.get_logger()

async def audit_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Extract request details
    audit_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "user_id": getattr(request.state, "user_id", None)
    }
    
    # Process request
    response = await call_next(request)
    
    # Add response details
    audit_data.update({
        "status_code": response.status_code,
        "duration_ms": int((time.time() - start_time) * 1000)
    })
    
    # Log security-relevant events
    if response.status_code >= 400:
        logger.warning("security_event", **audit_data)
    elif request.url.path.startswith("/api/v1/auth"):
        logger.info("auth_event", **audit_data)
    
    return response
```

### 3. Security Alerts

```yaml
# Prometheus alerting rules
groups:
  - name: security
    rules:
      - alert: HighFailedLoginRate
        expr: rate(auth_failures_total[5m]) > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High rate of failed login attempts"
          
      - alert: UnauthorizedDatabaseAccess
        expr: postgres_unauthorized_attempts > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Unauthorized database access attempt detected"
          
      - alert: ContainerPrivilegeEscalation
        expr: falco_privilege_escalation_attempts > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Container privilege escalation detected"
```

## Compliance & Governance

### 1. Compliance Checklist

**GDPR Compliance:**
- [ ] Data encryption at rest and in transit
- [ ] Right to erasure implementation
- [ ] Data portability features
- [ ] Consent management
- [ ] Privacy by design

**SOC 2 Requirements:**
- [ ] Access control policies
- [ ] Change management procedures
- [ ] Incident response plan
- [ ] Business continuity plan
- [ ] Regular security assessments

**HIPAA (if applicable):**
- [ ] PHI encryption
- [ ] Access audit logs
- [ ] Minimum necessary access
- [ ] Data retention policies
- [ ] Business Associate Agreements

### 2. Security Policies

```yaml
# Security policy enforcement
policies:
  password_policy:
    min_length: 12
    require_uppercase: true
    require_lowercase: true
    require_numbers: true
    require_special: true
    max_age_days: 90
    history_count: 5
    
  session_policy:
    timeout_minutes: 30
    max_concurrent: 3
    require_mfa: true
    
  data_classification:
    levels:
      - public
      - internal
      - confidential
      - restricted
```

### 3. Compliance Automation

```python
# Automated compliance checks
import schedule
import time

def compliance_scan():
    """Run automated compliance checks"""
    results = {
        "timestamp": datetime.utcnow(),
        "checks": []
    }
    
    # Check encryption
    results["checks"].append({
        "name": "database_encryption",
        "status": check_database_encryption(),
        "required": True
    })
    
    # Check access logs
    results["checks"].append({
        "name": "audit_logs_retention",
        "status": check_audit_log_retention(days=90),
        "required": True
    })
    
    # Check security patches
    results["checks"].append({
        "name": "security_patches",
        "status": check_security_patches(),
        "required": True
    })
    
    # Generate report
    generate_compliance_report(results)

# Schedule daily compliance scans
schedule.every().day.at("02:00").do(compliance_scan)
```

## Incident Response

### 1. Incident Response Plan

```yaml
incident_response:
  phases:
    1_detection:
      - Automated alerting
      - Log analysis
      - User reports
      
    2_containment:
      - Isolate affected systems
      - Disable compromised accounts
      - Block malicious IPs
      
    3_eradication:
      - Remove malware
      - Patch vulnerabilities
      - Reset credentials
      
    4_recovery:
      - Restore from backups
      - Verify system integrity
      - Resume operations
      
    5_lessons_learned:
      - Document incident
      - Update procedures
      - Implement improvements
```

### 2. Emergency Procedures

```bash
#!/bin/bash
# Emergency shutdown script

echo "EMERGENCY SHUTDOWN INITIATED"

# Stop accepting new requests
docker exec nginx nginx -s stop

# Gracefully stop application
docker-compose stop backend worker

# Backup current data
./scripts/emergency_backup.sh

# Stop all services
docker-compose down

# Log incident
echo "Emergency shutdown at $(date)" >> /var/log/incidents.log
```

### 3. Recovery Procedures

```bash
#!/bin/bash
# System recovery script

# Verify system integrity
./scripts/verify_integrity.sh || exit 1

# Restore from backup if needed
if [ "$1" == "--restore" ]; then
    ./scripts/restore_from_backup.sh $2
fi

# Start services with health checks
docker-compose up -d postgres redis
./scripts/wait_for_healthy.sh postgres redis

docker-compose up -d backend
./scripts/wait_for_healthy.sh backend

docker-compose up -d frontend nginx
./scripts/verify_full_system.sh
```

## Security Checklist Summary

### Pre-Deployment
- [ ] Security scan all container images
- [ ] Review and update all dependencies
- [ ] Configure secrets management
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Review RBAC permissions
- [ ] Set up monitoring and alerting
- [ ] Document incident response procedures

### Deployment
- [ ] Use secure communication channels
- [ ] Verify all security configurations
- [ ] Test backup and recovery procedures
- [ ] Validate monitoring and alerts
- [ ] Perform penetration testing
- [ ] Review audit logs
- [ ] Update security documentation

### Post-Deployment
- [ ] Regular security patching schedule
- [ ] Continuous vulnerability scanning
- [ ] Regular security audits
- [ ] Incident response drills
- [ ] Compliance verification
- [ ] Security training for team
- [ ] Regular backup verification

## Conclusion

Implementing these security best practices will significantly enhance the security posture of the containerized SynapseDTE application. Security is an ongoing process that requires continuous monitoring, updating, and improvement.

Regular security assessments, staying updated with the latest threats, and maintaining a security-first culture within the development team are essential for long-term security success.

---

**Document Version**: 1.0  
**Last Updated**: January 2025  
**Classification**: Internal Use Only