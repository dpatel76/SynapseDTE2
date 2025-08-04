# Security Best Practices & Remediation Guide for SynapseDTE

## Table of Contents
1. [Immediate Security Fixes](#immediate-security-fixes)
2. [Authentication & Authorization](#authentication--authorization)
3. [Input Validation & Sanitization](#input-validation--sanitization)
4. [API Security](#api-security)
5. [Data Protection](#data-protection)
6. [Infrastructure Security](#infrastructure-security)
7. [Secure Development Practices](#secure-development-practices)
8. [Security Monitoring](#security-monitoring)
9. [Incident Response](#incident-response)
10. [Compliance & Governance](#compliance--governance)

## Immediate Security Fixes

### 🚨 Critical Issues to Fix Now

#### 1. Remove Hardcoded Secrets
```python
# ❌ BAD: Hardcoded secret
SECRET_KEY = "my-secret-key-123"

# ✅ GOOD: Environment variable
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")
```

#### 2. Fix SQL Injection Vulnerabilities
```python
# ❌ BAD: String concatenation
query = f"SELECT * FROM users WHERE email = '{email}'"

# ✅ GOOD: Parameterized queries
query = select(User).where(User.email == email)
# or
query = text("SELECT * FROM users WHERE email = :email")
result = await db.execute(query, {"email": email})
```

#### 3. Implement Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def login(request: Request, credentials: LoginRequest):
    # Login logic
```

#### 4. Enable Security Headers
```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';"
    return response
```

## Authentication & Authorization

### Password Security

#### Strong Password Policy
```python
import re
from pydantic import validator

class UserCreate(BaseModel):
    password: str
    
    @validator('password')
    def validate_password_strength(cls, password):
        if len(password) < 12:
            raise ValueError('Password must be at least 12 characters long')
        
        if not re.search(r'[A-Z]', password):
            raise ValueError('Password must contain uppercase letters')
        
        if not re.search(r'[a-z]', password):
            raise ValueError('Password must contain lowercase letters')
        
        if not re.search(r'\d', password):
            raise ValueError('Password must contain numbers')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError('Password must contain special characters')
        
        # Check against common passwords
        common_passwords = ['password123', 'admin123', 'letmein']
        if password.lower() in common_passwords:
            raise ValueError('Password is too common')
        
        return password
```

#### Secure Password Hashing
```python
from passlib.context import CryptContext

# Use bcrypt with high cost factor
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12  # Increase cost factor
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### JWT Security

#### Secure JWT Implementation
```python
from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets

# Generate secure secret key
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived tokens

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16)  # Unique token ID
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Additional validation
        if "sub" not in payload:
            raise JWTError("Invalid token")
        
        # Check if token is blacklisted
        if is_token_blacklisted(payload.get("jti")):
            raise JWTError("Token has been revoked")
        
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Account Lockout Protection
```python
from datetime import datetime, timedelta
import redis

redis_client = redis.Redis()

class LoginAttemptTracker:
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 30  # minutes
    
    @classmethod
    async def record_attempt(cls, email: str, success: bool):
        key = f"login_attempts:{email}"
        
        if success:
            redis_client.delete(key)
            return
        
        attempts = redis_client.incr(key)
        if attempts == 1:
            redis_client.expire(key, cls.LOCKOUT_DURATION * 60)
        
        if attempts >= cls.MAX_ATTEMPTS:
            cls.lock_account(email)
    
    @classmethod
    def is_locked(cls, email: str) -> bool:
        return redis_client.exists(f"locked:{email}")
    
    @classmethod
    def lock_account(cls, email: str):
        redis_client.setex(
            f"locked:{email}",
            cls.LOCKOUT_DURATION * 60,
            "locked"
        )
```

### RBAC Implementation
```python
from enum import Enum
from typing import List, Optional

class Permission(str, Enum):
    READ_USERS = "users:read"
    WRITE_USERS = "users:write"
    DELETE_USERS = "users:delete"
    READ_REPORTS = "reports:read"
    WRITE_REPORTS = "reports:write"

class RolePermissions:
    PERMISSIONS = {
        "Admin": [Permission.READ_USERS, Permission.WRITE_USERS, Permission.DELETE_USERS],
        "Tester": [Permission.READ_REPORTS, Permission.WRITE_REPORTS],
        "User": [Permission.READ_REPORTS]
    }
    
    @classmethod
    def has_permission(cls, user_role: str, permission: Permission) -> bool:
        return permission in cls.PERMISSIONS.get(user_role, [])

def require_permission(permission: Permission):
    def decorator(func):
        async def wrapper(*args, current_user: User = Depends(get_current_user), **kwargs):
            if not RolePermissions.has_permission(current_user.role, permission):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

## Input Validation & Sanitization

### Comprehensive Input Validation
```python
from pydantic import BaseModel, validator, EmailStr
import bleach
import re

class SecureInputModel(BaseModel):
    email: EmailStr
    name: str
    description: Optional[str]
    
    @validator('name')
    def validate_name(cls, name):
        # Remove any HTML tags
        name = bleach.clean(name, tags=[], strip=True)
        
        # Check length
        if not 1 <= len(name) <= 100:
            raise ValueError('Name must be between 1 and 100 characters')
        
        # Allow only alphanumeric and spaces
        if not re.match(r'^[a-zA-Z0-9\s]+$', name):
            raise ValueError('Name contains invalid characters')
        
        return name
    
    @validator('description')
    def sanitize_description(cls, description):
        if not description:
            return description
        
        # Allow only specific HTML tags
        allowed_tags = ['p', 'br', 'strong', 'em']
        description = bleach.clean(
            description,
            tags=allowed_tags,
            strip=True
        )
        
        # Limit length
        if len(description) > 1000:
            raise ValueError('Description too long')
        
        return description
```

### SQL Injection Prevention
```python
from sqlalchemy import select, and_
from sqlalchemy.sql import text

class SecureRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_by_email(self, email: str):
        # ✅ GOOD: Using SQLAlchemy ORM
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_reports(self, search_term: str, user_id: int):
        # ✅ GOOD: Parameterized query with LIKE
        query = select(Report).where(
            and_(
                Report.user_id == user_id,
                Report.title.ilike(f"%{search_term}%")
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def custom_query(self, table_name: str):
        # ✅ GOOD: Whitelist allowed tables
        allowed_tables = ['users', 'reports', 'cycles']
        if table_name not in allowed_tables:
            raise ValueError("Invalid table name")
        
        # Use parameterized query even for dynamic SQL
        query = text(f"SELECT COUNT(*) FROM {table_name} WHERE is_active = :active")
        result = await self.db.execute(query, {"active": True})
        return result.scalar()
```

### XSS Prevention
```python
import html
from markupsafe import Markup, escape

def sanitize_html_output(user_input: str) -> str:
    """Sanitize user input for HTML output"""
    # Escape HTML entities
    return html.escape(user_input)

def sanitize_javascript_string(user_input: str) -> str:
    """Sanitize for use in JavaScript strings"""
    return json.dumps(user_input)[1:-1]  # Remove quotes

# In templates (Jinja2)
# {{ user_input | e }}  # Auto-escapes

# React component
const SafeOutput = ({ userInput }) => {
    // React auto-escapes by default
    return <div>{userInput}</div>;
    
    // For HTML content, use DOMPurify
    const sanitized = DOMPurify.sanitize(userInput);
    return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
};
```

## API Security

### API Rate Limiting
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    storage_uri="redis://localhost:6379"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Different limits for different endpoints
@app.post("/api/v1/auth/login")
@limiter.limit("5 per minute")
async def login(request: Request):
    pass

@app.get("/api/v1/public/data")
@limiter.limit("1000 per hour")
async def public_data(request: Request):
    pass
```

### API Versioning
```python
from fastapi import APIRouter, HTTPException

def create_versioned_app():
    app = FastAPI()
    
    # Version 1 API
    v1_router = APIRouter(prefix="/api/v1")
    v1_router.include_router(auth_router_v1)
    v1_router.include_router(users_router_v1)
    
    # Version 2 API with breaking changes
    v2_router = APIRouter(prefix="/api/v2")
    v2_router.include_router(auth_router_v2)
    v2_router.include_router(users_router_v2)
    
    app.include_router(v1_router)
    app.include_router(v2_router)
    
    # Deprecation notice for old versions
    @app.middleware("http")
    async def add_deprecation_header(request: Request, call_next):
        response = await call_next(request)
        if "/api/v1" in request.url.path:
            response.headers["X-API-Deprecation"] = "true"
            response.headers["X-API-Deprecation-Date"] = "2024-12-31"
        return response
    
    return app
```

### Request Validation
```python
from typing import Optional
from pydantic import BaseModel, Field, validator

class PaginationParams(BaseModel):
    skip: int = Field(0, ge=0, le=10000)
    limit: int = Field(100, ge=1, le=1000)
    
class SearchParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    filters: Optional[Dict[str, str]] = Field(default_factory=dict)
    
    @validator('filters')
    def validate_filters(cls, filters):
        allowed_keys = ['status', 'type', 'date_from', 'date_to']
        for key in filters:
            if key not in allowed_keys:
                raise ValueError(f"Invalid filter key: {key}")
        return filters

# Use in endpoint
@app.get("/api/v1/search")
async def search(
    params: SearchParams = Depends(),
    pagination: PaginationParams = Depends()
):
    # Validated and sanitized inputs
    pass
```

## Data Protection

### Data Classification
```python
from enum import Enum

class DataClassification(Enum):
    PUBLIC = "public"           # Can be shared publicly
    INTERNAL = "internal"       # Internal use only
    CONFIDENTIAL = "confidential"  # Restricted access
    SENSITIVE = "sensitive"     # PII, financial data
    TOP_SECRET = "top_secret"   # Highest protection

# Data classification mapping
DATA_CLASSIFICATIONS = {
    "users.password_hash": DataClassification.TOP_SECRET,
    "users.email": DataClassification.SENSITIVE,
    "users.ssn": DataClassification.SENSITIVE,
    "reports.financial_data": DataClassification.CONFIDENTIAL,
    "audit_logs.ip_address": DataClassification.INTERNAL,
    "public_content": DataClassification.PUBLIC
}
```

### Encryption at Rest
```python
from cryptography.fernet import Fernet
import base64

class EncryptionService:
    def __init__(self):
        # Load key from secure storage
        self.key = self._load_encryption_key()
        self.cipher = Fernet(self.key)
    
    def _load_encryption_key(self):
        # Load from environment or key management service
        key = os.environ.get("ENCRYPTION_KEY")
        if not key:
            raise ValueError("Encryption key not configured")
        return key.encode()
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data before storage"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data after retrieval"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Usage in model
class SensitiveDataModel(Base):
    __tablename__ = "sensitive_data"
    
    id = Column(Integer, primary_key=True)
    encrypted_ssn = Column(String)
    encrypted_credit_card = Column(String)
    
    @property
    def ssn(self):
        if self.encrypted_ssn:
            return encryption_service.decrypt_sensitive_data(self.encrypted_ssn)
        return None
    
    @ssn.setter
    def ssn(self, value):
        if value:
            self.encrypted_ssn = encryption_service.encrypt_sensitive_data(value)
```

### Secure File Upload
```python
import os
import hashlib
import magic
from pathlib import Path

class SecureFileUploadService:
    ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.csv', '.xlsx'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile, user_id: int) -> str:
        # Validate file size
        file_size = 0
        contents = bytearray()
        
        while chunk := await file.read(8192):
            file_size += len(chunk)
            if file_size > self.MAX_FILE_SIZE:
                raise ValueError("File too large")
            contents.extend(chunk)
        
        # Validate file type by magic bytes
        file_type = magic.from_buffer(contents, mime=True)
        allowed_types = ['application/pdf', 'image/png', 'image/jpeg', 'text/csv']
        if file_type not in allowed_types:
            raise ValueError("Invalid file type")
        
        # Validate extension
        ext = Path(file.filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError("Invalid file extension")
        
        # Generate secure filename
        file_hash = hashlib.sha256(contents).hexdigest()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        secure_filename = f"{user_id}_{timestamp}_{file_hash[:8]}{ext}"
        
        # Save to isolated directory
        file_path = self.upload_dir / secure_filename
        with open(file_path, 'wb') as f:
            f.write(contents)
        
        # Set restrictive permissions
        os.chmod(file_path, 0o644)
        
        return str(file_path)
```

### Encryption in Transit
```python
from fastapi import FastAPI, Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import ssl

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Force HTTPS for all requests"""
    
    async def dispatch(self, request: Request, call_next):
        if request.url.scheme == "http":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=str(url), status_code=301)
        
        response = await call_next(request)
        
        # Add security headers for data protection
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
        
        return response

# TLS Configuration
def create_ssl_context():
    """Create secure SSL context"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    
    # Set minimum TLS version
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    # Disable weak ciphers
    context.set_ciphers(
        'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS'
    )
    
    # Load certificates
    context.load_cert_chain(
        certfile="path/to/cert.pem",
        keyfile="path/to/key.pem"
    )
    
    return context

# API Encryption
class EncryptedRequest(BaseModel):
    """Encrypted request wrapper"""
    encrypted_data: str
    signature: str
    timestamp: int

class EncryptionMiddleware(BaseHTTPMiddleware):
    """Encrypt sensitive API requests/responses"""
    
    def __init__(self, app, encryption_service: EncryptionService):
        super().__init__(app)
        self.encryption_service = encryption_service
    
    async def dispatch(self, request: Request, call_next):
        # Decrypt request if needed
        if request.url.path in ENCRYPTED_ENDPOINTS:
            body = await request.body()
            if body:
                decrypted = self.encryption_service.decrypt_request(body)
                request._body = decrypted
        
        response = await call_next(request)
        
        # Encrypt response if needed
        if request.url.path in ENCRYPTED_ENDPOINTS:
            if hasattr(response, 'body'):
                encrypted_body = self.encryption_service.encrypt_response(
                    response.body
                )
                response.body = encrypted_body
        
        return response
```

### Data Masking
```python
import re

class DataMasker:
    @staticmethod
    def mask_email(email: str) -> str:
        """Mask email: test@example.com -> t***@example.com"""
        parts = email.split('@')
        if len(parts) != 2:
            return email
        
        username = parts[0]
        if len(username) <= 2:
            masked = username[0] + '*' * (len(username) - 1)
        else:
            masked = username[0] + '***' + username[-1]
        
        return f"{masked}@{parts[1]}"
    
    @staticmethod
    def mask_ssn(ssn: str) -> str:
        """Mask SSN: 123-45-6789 -> ***-**-6789"""
        return re.sub(r'^\d{3}-\d{2}', '***-**', ssn)
    
    @staticmethod
    def mask_credit_card(cc: str) -> str:
        """Mask credit card: 1234567812345678 -> ************5678"""
        cc_digits = re.sub(r'\D', '', cc)
        if len(cc_digits) < 4:
            return '*' * len(cc_digits)
        return '*' * (len(cc_digits) - 4) + cc_digits[-4:]
```

## Infrastructure Security

### CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

# Production CORS configuration
origins = [
    "https://app.synapseDTE.com",
    "https://www.synapseDTE.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=86400,  # 24 hours
)

# Development CORS (separate config)
if settings.debug:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### HTTPS Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name synapseDTE.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/synapseDTE.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/synapseDTE.com/privkey.pem;
    
    # Strong SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    
    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    
    # Other security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;
    
    # Redirect HTTP to HTTPS
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect all HTTP to HTTPS
server {
    listen 80;
    server_name synapseDTE.com;
    return 301 https://$server_name$request_uri;
}
```

## Secure Development Practices

### Dependency Management
```yaml
# .github/workflows/security.yml
name: Security Checks

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Run Bandit
        run: |
          pip install bandit
          bandit -r app/ -f json -o bandit-report.json
      
      - name: Check Dependencies
        run: |
          pip install safety
          safety check
      
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: "p/security-audit p/python"
```

### Code Review Security Checklist
```markdown
## Security Review Checklist

- [ ] No hardcoded secrets or API keys
- [ ] All user inputs are validated and sanitized
- [ ] SQL queries use parameterization
- [ ] Authentication and authorization checks in place
- [ ] Sensitive data is encrypted
- [ ] Error messages don't leak sensitive information
- [ ] Logging doesn't include sensitive data
- [ ] Dependencies are up to date
- [ ] Security headers are configured
- [ ] HTTPS is enforced
```

### Secure Logging
```python
import logging
import re

class SecureFormatter(logging.Formatter):
    """Custom formatter that masks sensitive data"""
    
    SENSITIVE_PATTERNS = [
        (r'\b\d{3}-\d{2}-\d{4}\b', '***-**-****'),  # SSN
        (r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '****-****-****-****'),  # Credit card
        (r'password["\']?\s*[:=]\s*["\']?([^"\'\s]+)', 'password=***'),  # Passwords
        (r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'\s]+)', 'api_key=***'),  # API keys
    ]
    
    def format(self, record):
        msg = super().format(record)
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            msg = re.sub(pattern, replacement, msg, flags=re.IGNORECASE)
        return msg

# Configure secure logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(SecureFormatter())
logger.addHandler(handler)
```

## Security Monitoring

### Real-time Security Monitoring
```python
from datetime import datetime, timedelta
import asyncio

class SecurityMonitor:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.alert_thresholds = {
            'failed_logins': (10, timedelta(minutes=5)),
            'api_errors': (100, timedelta(minutes=1)),
            'suspicious_activity': (5, timedelta(minutes=10))
        }
    
    async def track_event(self, event_type: str, details: dict):
        """Track security events"""
        key = f"security:{event_type}:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        self.redis.incr(key)
        self.redis.expire(key, 3600)  # Keep for 1 hour
        
        # Check thresholds
        await self.check_thresholds(event_type)
    
    async def check_thresholds(self, event_type: str):
        """Check if thresholds are exceeded"""
        if event_type not in self.alert_thresholds:
            return
        
        threshold, window = self.alert_thresholds[event_type]
        count = await self.get_event_count(event_type, window)
        
        if count > threshold:
            await self.send_alert(event_type, count, window)
    
    async def send_alert(self, event_type: str, count: int, window: timedelta):
        """Send security alert"""
        alert = {
            'type': event_type,
            'count': count,
            'window': str(window),
            'timestamp': datetime.utcnow().isoformat()
        }
        # Send to monitoring system
        logger.critical(f"SECURITY ALERT: {alert}")
```

### Audit Logging
```python
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AuditLogger:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_action(
        self,
        action: str,
        resource_type: str,
        resource_id: str = None,
        user_id: int = None,
        request: Request = None,
        details: dict = None
    ):
        """Log security-relevant actions"""
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("User-Agent") if request else None,
            details=details
        )
        self.db.add(audit_entry)
        await self.db.commit()

# Usage
await audit_logger.log_action(
    action="LOGIN_SUCCESS",
    resource_type="AUTH",
    user_id=user.id,
    request=request,
    details={"method": "password"}
)
```

## Incident Response

### Incident Response Plan
```python
class IncidentResponse:
    SEVERITY_LEVELS = {
        'CRITICAL': 1,  # Data breach, RCE
        'HIGH': 2,      # Auth bypass, SQLi
        'MEDIUM': 3,    # XSS, Information disclosure
        'LOW': 4        # Missing headers, verbose errors
    }
    
    async def handle_incident(self, incident_type: str, severity: str, details: dict):
        """Handle security incident"""
        incident_id = await self.create_incident(incident_type, severity, details)
        
        # Immediate actions based on severity
        if severity == 'CRITICAL':
            await self.emergency_response(incident_id)
        elif severity == 'HIGH':
            await self.high_priority_response(incident_id)
        
        # Log and notify
        await self.log_incident(incident_id)
        await self.notify_team(incident_id, severity)
        
        return incident_id
    
    async def emergency_response(self, incident_id: str):
        """Emergency response for critical incidents"""
        # 1. Isolate affected systems
        await self.isolate_system()
        
        # 2. Revoke potentially compromised tokens
        await self.revoke_all_tokens()
        
        # 3. Enable emergency mode
        await self.enable_emergency_mode()
        
        # 4. Start forensic logging
        await self.start_forensic_logging(incident_id)
```

### Security Playbooks
```python
# Playbook for different incident types
SECURITY_PLAYBOOKS = {
    "DATA_BREACH": [
        "Isolate affected systems",
        "Identify scope of breach",
        "Preserve evidence",
        "Notify legal team",
        "Prepare disclosure statement",
        "Reset all user passwords",
        "Audit all access logs"
    ],
    "RANSOMWARE": [
        "Disconnect from network",
        "Identify infected systems",
        "Restore from backups",
        "Report to authorities",
        "Do not pay ransom"
    ],
    "DDoS_ATTACK": [
        "Enable DDoS protection",
        "Scale infrastructure",
        "Block attacking IPs",
        "Contact ISP",
        "Monitor bandwidth"
    ]
}
```

## Compliance & Governance

### GDPR Compliance
```python
class GDPRCompliance:
    @staticmethod
    async def export_user_data(user_id: int) -> dict:
        """Export all user data for GDPR data portability"""
        data = {
            "user_profile": await get_user_profile(user_id),
            "activity_logs": await get_user_activity_logs(user_id),
            "uploaded_files": await get_user_files(user_id),
            "generated_reports": await get_user_reports(user_id)
        }
        return data
    
    @staticmethod
    async def delete_user_data(user_id: int):
        """Delete user data for GDPR right to erasure"""
        # Anonymize instead of hard delete for audit trail
        await anonymize_user_profile(user_id)
        await delete_user_files(user_id)
        await anonymize_user_logs(user_id)
        
        # Log deletion request
        await audit_logger.log_action(
            action="GDPR_DATA_DELETION",
            resource_type="USER",
            resource_id=str(user_id),
            details={"reason": "user_request"}
        )
```

### Security Metrics
```python
class SecurityMetrics:
    @staticmethod
    async def calculate_security_score() -> dict:
        """Calculate overall security posture score"""
        metrics = {
            "authentication_security": await calculate_auth_score(),
            "data_protection": await calculate_data_score(),
            "infrastructure_security": await calculate_infra_score(),
            "compliance": await calculate_compliance_score()
        }
        
        overall_score = sum(metrics.values()) / len(metrics)
        
        return {
            "overall_score": overall_score,
            "metrics": metrics,
            "recommendations": generate_recommendations(metrics)
        }
```

## Summary

This comprehensive guide provides actionable security best practices and remediation strategies for the SynapseDTE application. Key takeaways:

1. **Fix Critical Issues First**: Address SQL injection, hardcoded secrets, and authentication vulnerabilities immediately
2. **Implement Defense in Depth**: Layer security controls throughout the application
3. **Monitor Continuously**: Set up real-time security monitoring and alerting
4. **Plan for Incidents**: Have response procedures ready before incidents occur
5. **Maintain Compliance**: Ensure ongoing compliance with relevant regulations

Remember: Security is not a one-time effort but an ongoing process. Regular security assessments, updates, and training are essential for maintaining a strong security posture.