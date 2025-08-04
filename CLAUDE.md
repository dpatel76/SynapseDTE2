# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 API Authentication - STOP WASTING TIME!

**ALWAYS use these credentials for API testing:**
- Email: `tester@example.com`
- Password: `password123`
- Login endpoint: `POST /api/v1/auth/login`
- Request format: `json={"email": "tester@example.com", "password": "password123"}`

**Test Execution API Endpoints:**
- Create and execute: `POST /api/v1/test-execution/execute`
- Execute specific test case: `POST /api/v1/test-execution/test-cases/{test_case_id}/execute`
- Bulk execute: `POST /api/v1/test-execution/{cycle_id}/reports/{report_id}/execute`

# Claude.md - Architecture & Design Principles Guide

## 🚨 CRITICAL: Accuracy and Verification Requirements

### MANDATORY: Always Verify Claims with Facts

**NEVER make claims about completed work without actual verification.** This is a zero-tolerance policy.

#### Common False Claims to Avoid:
1. **"I tested X and it works"** - Only say this if you actually ran the test and saw the results
2. **"The feature is implemented"** - Only say this if you've seen the code and verified it exists
3. **"Data is saved to the database"** - Only say this if you've queried the database and confirmed the data exists
4. **"The API endpoint works"** - Only say this if you've called the endpoint and received a successful response

#### Required Verification Process:
Before making ANY claim about functionality:
1. **Actually test it** - Run the code, call the API, query the database
2. **Show evidence** - Include actual output, response codes, or data retrieved
3. **Be explicit about what wasn't tested** - If you only checked part of a flow, say so
4. **Distinguish between "should work" and "does work"** - Theory vs. verified reality

#### Example of Proper Testing:
```python
# ❌ WRONG: Claiming without verification
print("✅ Data source creation tested successfully")

# ✅ CORRECT: Actually test and show results
response = requests.post(f"{BASE_URL}/api/v1/data-sources", ...)
if response.status_code == 201:
    print(f"✅ Data source created: {response.json()}")
else:
    print(f"❌ Failed to create data source: {response.status_code} - {response.text}")

# Then verify in database
result = await db.execute(text("SELECT * FROM data_sources WHERE id = :id"), {"id": created_id})
if result.first():
    print("✅ Verified: Data source exists in database")
else:
    print("❌ Data source NOT found in database")
```

#### When Uncertain:
- Say "I haven't tested this"
- Say "Let me verify this first"
- Say "The code suggests X should happen, but I need to confirm"
- NEVER make assumptions and present them as facts

### Consequences of False Claims:
False claims waste time, create confusion, and erode trust. Always prioritize accuracy over appearing knowledgeable.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Architecture Principles](#architecture-principles)
4. [Technology Stack Guidelines](#technology-stack-guidelines)
5. [Code Standards](#code-standards)
6. [Database Design](#database-design)
7. [API Design](#api-design)
8. [Frontend Architecture](#frontend-architecture)
9. [Workflow Management](#workflow-management)
10. [Error Handling](#error-handling)
11. [Testing Strategy](#testing-strategy)
12. [Security Guidelines](#security-guidelines)
13. [Performance Standards](#performance-standards)
14. [Code Review Checklist](#code-review-checklist)
15. [Refactoring Guidelines](#refactoring-guidelines)
16. [Background Jobs & Async Operations](#background-jobs--async-operations)
17. [Component Reuse Pattern](#component-reuse-pattern)

## 🎯 Overview

This document establishes strict architecture and design principles for a modern web application built with React JS, Python, PostgreSQL, Temporal, and FastAPI. These guidelines ensure maintainability, scalability, and code quality.

## 🏗️ Project Structure

```
project-root/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   └── dependencies/
│   │   │   └── middleware/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   ├── base.py
│   │   │   └── domain/
│   │   ├── services/
│   │   │   ├── business/
│   │   │   └── external/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   │   ├── requests/
│   │   │   └── responses/
│   │   ├── workflows/
│   │   │   ├── activities/
│   │   │   └── definitions/
│   │   └── utils/
│   ├── tests/
│   ├── migrations/
│   └── scripts/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/
│   │   │   ├── forms/
│   │   │   └── layout/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── utils/
│   │   ├── types/
│   │   └── constants/
│   ├── public/
│   └── tests/
├── docker/
├── docs/
└── scripts/
```

## 🎨 Architecture Principles

### 1. Separation of Concerns
- **Single Responsibility**: Each class/function has one reason to change
- **Layered Architecture**: Clear separation between presentation, business, and data layers
- **Domain-Driven Design**: Business logic organized around domain concepts

### 2. Dependency Inversion
- High-level modules should not depend on low-level modules
- Use dependency injection for loose coupling
- Abstract interfaces for external dependencies

### 3. Clean Architecture
```
┌─────────────────────────────────────────────┐
│                  UI Layer                   │
├─────────────────────────────────────────────┤
│              Business Logic                 │
├─────────────────────────────────────────────┤
│               Data Access                   │
├─────────────────────────────────────────────┤
│              External Services              │
└─────────────────────────────────────────────┘
```

### 4. SOLID Principles
- **S**ingle Responsibility
- **O**pen/Closed
- **L**iskov Substitution
- **I**nterface Segregation
- **D**ependency Inversion

## 🛠️ Technology Stack Guidelines

### Backend (Python/FastAPI)

#### File Organization
```python
# ✅ Good: Clear module structure
from app.services.business.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.schemas.responses.user_response import UserResponse

# ❌ Bad: Unclear imports
from app.stuff import get_user_thing
```

#### Service Layer Pattern
```python
# ✅ Good: Clean service interface
class UserService:
    def __init__(self, user_repo: UserRepository, email_service: EmailService):
        self._user_repo = user_repo
        self._email_service = email_service
    
    async def create_user(self, user_data: CreateUserRequest) -> UserResponse:
        # Business logic here
        pass

# ❌ Bad: Direct database access in endpoint
@app.post("/users")
async def create_user(user_data: dict, db: Session = Depends(get_db)):
    # Direct DB manipulation - violates layering
    pass
```

#### Repository Pattern
```python
# ✅ Good: Abstract repository interface
from abc import ABC, abstractmethod

class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        pass

class PostgreSQLUserRepository(UserRepository):
    async def create(self, user: User) -> User:
        # PostgreSQL specific implementation
        pass
```

#### Error Handling
```python
# ✅ Good: Custom exceptions with context
class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with ID {user_id} not found")

# ✅ Good: Centralized error handling
@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": "User not found", "user_id": exc.user_id}
    )
```

### Frontend (React JS)

#### Component Structure
```typescript
// ✅ Good: Functional component with clear interface
interface UserProfileProps {
  userId: string;
  onUpdate: (user: User) => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ userId, onUpdate }) => {
  const { data: user, loading, error } = useUser(userId);
  
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return (
    <div className="user-profile">
      {/* Component content */}
    </div>
  );
};
```

#### Custom Hooks
```typescript
// ✅ Good: Custom hook for data fetching
const useUser = (userId: string) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        const userData = await userService.getUser(userId);
        setUser(userData);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [userId]);

  return { user, loading, error };
};
```

### Database (PostgreSQL)

#### Schema Design
```sql
-- ✅ Good: Clear table structure with constraints
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ✅ Good: Proper indexing
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

#### Migration Strategy
```python
# ✅ Good: Reversible migration
"""add_user_email_index

Revision ID: 001
Revises: 000
Create Date: 2024-01-01 10:00:00.000000
"""

def upgrade():
    op.create_index('idx_users_email', 'users', ['email'])

def downgrade():
    op.drop_index('idx_users_email', table_name='users')
```

### Workflow Management (Temporal)

#### Activity Design
```python
# ✅ Good: Pure activity function
@activity.defn
async def send_welcome_email(user_id: int, email: str) -> bool:
    try:
        await email_service.send_welcome_email(user_id, email)
        return True
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        raise

# ✅ Good: Workflow definition
@workflow.defn
class UserRegistrationWorkflow:
    @workflow.run
    async def run(self, user_data: UserRegistrationData) -> UserRegistrationResult:
        # Create user
        user = await workflow.execute_activity(
            create_user_activity,
            user_data,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Send welcome email
        await workflow.execute_activity(
            send_welcome_email,
            SendWelcomeEmailInput(user.id, user.email),
            start_to_close_timeout=timedelta(minutes=2)
        )
        
        return UserRegistrationResult(user_id=user.id, success=True)
```

## 📝 Code Standards

### Python Standards

#### Type Hints
```python
# ✅ Good: Complete type hints
from typing import Optional, List, Dict, Any

def process_users(
    users: List[User], 
    filters: Optional[Dict[str, Any]] = None
) -> List[ProcessedUser]:
    pass

# ❌ Bad: Missing type hints
def process_users(users, filters=None):
    pass
```

#### Error Handling
```python
# ✅ Good: Specific exception handling
try:
    user = await user_service.get_user(user_id)
except UserNotFoundError:
    raise HTTPException(status_code=404, detail="User not found")
except ValidationError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### TypeScript Standards

#### Interface Definition
```typescript
// ✅ Good: Clear interface with documentation
interface User {
  readonly id: string;
  email: string;
  firstName: string;
  lastName: string;
  createdAt: Date;
  updatedAt: Date;
}

// ✅ Good: Union types for state
type LoadingState = 'idle' | 'loading' | 'success' | 'error';
```

#### Error Handling
```typescript
// ✅ Good: Typed error handling
type ApiError = {
  code: string;
  message: string;
  details?: Record<string, any>;
};

const handleApiError = (error: ApiError): void => {
  switch (error.code) {
    case 'USER_NOT_FOUND':
      showNotification('User not found', 'error');
      break;
    case 'VALIDATION_ERROR':
      showValidationErrors(error.details);
      break;
    default:
      showNotification('An unexpected error occurred', 'error');
  }
};
```

## 💾 Database Design

### Schema Guidelines

#### Naming Conventions
- Tables: `snake_case` (e.g., `user_profiles`)
- Columns: `snake_case` (e.g., `created_at`)
- Indexes: `idx_table_column` (e.g., `idx_users_email`)
- Foreign keys: `fk_table_column` (e.g., `fk_posts_user_id`)

#### Data Types
```sql
-- ✅ Good: Appropriate data types
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ❌ Bad: Inefficient data types
CREATE TABLE orders (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255),
    total_amount FLOAT,
    status TEXT,
    created_at VARCHAR(50)
);
```

#### Relationships
```sql
-- ✅ Good: Proper foreign key constraints
ALTER TABLE posts 
ADD CONSTRAINT fk_posts_user_id 
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- ✅ Good: Junction table for many-to-many
CREATE TABLE user_roles (
    user_id UUID NOT NULL,
    role_id UUID NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);
```

## 🔌 API Design

### RESTful Endpoints
```python
# ✅ Good: RESTful resource design
@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, service: UserService = Depends()):
    return await service.get_user(user_id)

@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: CreateUserRequest, service: UserService = Depends()):
    return await service.create_user(user_data)

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UpdateUserRequest, service: UserService = Depends()):
    return await service.update_user(user_id, user_data)
```

### Request/Response Models
```python
# ✅ Good: Separate request/response schemas
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True
```

### Error Responses
```python
# ✅ Good: Consistent error format
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

## ⚛️ Frontend Architecture

### State Management
```typescript
// ✅ Good: Centralized state management
interface AppState {
  user: UserState;
  posts: PostState;
  ui: UIState;
}

const useAppStore = create<AppState>((set, get) => ({
  user: {
    currentUser: null,
    loading: false,
    error: null,
  },
  // ... other state slices
}));
```

### Component Patterns
```typescript
// ✅ Good: Compound component pattern
const UserCard = ({ children, ...props }: UserCardProps) => (
  <div className="user-card" {...props}>
    {children}
  </div>
);

UserCard.Avatar = ({ src, alt }: AvatarProps) => (
  <img className="user-card__avatar" src={src} alt={alt} />
);

UserCard.Name = ({ children }: NameProps) => (
  <h3 className="user-card__name">{children}</h3>
);

// Usage
<UserCard>
  <UserCard.Avatar src={user.avatar} alt={user.name} />
  <UserCard.Name>{user.name}</UserCard.Name>
</UserCard>
```

## 🔄 Workflow Management

### Activity Design
```python
# ✅ Good: Idempotent activities
@activity.defn
async def process_payment(payment_data: PaymentData) -> PaymentResult:
    # Check if payment already processed
    existing_payment = await payment_repo.get_by_idempotency_key(payment_data.idempotency_key)
    if existing_payment:
        return PaymentResult(payment_id=existing_payment.id, status=existing_payment.status)
    
    # Process payment
    result = await payment_service.process(payment_data)
    return PaymentResult(payment_id=result.id, status=result.status)
```

### Workflow Testing
```python
# ✅ Good: Workflow testing
async def test_user_registration_workflow():
    async with WorkflowTester() as tester:
        workflow = UserRegistrationWorkflow()
        
        # Execute workflow
        result = await tester.execute_workflow(
            workflow.run,
            UserRegistrationData(email="test@example.com", password="password123")
        )
        
        # Verify activities were called
        assert tester.activity_calls[0].activity == create_user_activity
        assert tester.activity_calls[1].activity == send_welcome_email
        assert result.success is True
```

## 🚨 Error Handling

### Backend Error Hierarchy
```python
# ✅ Good: Domain-specific exceptions
class DomainError(Exception):
    """Base exception for domain errors"""
    pass

class ValidationError(DomainError):
    """Raised when validation fails"""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"Validation error on {field}: {message}")

class ResourceNotFoundError(DomainError):
    """Raised when a resource is not found"""
    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier
        super().__init__(f"{resource_type} with identifier {identifier} not found")
```

### Frontend Error Boundaries
```typescript
// ✅ Good: Error boundary component
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Log to error tracking service
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback error={this.state.error} />;
    }

    return this.props.children;
  }
}
```

## 🧪 Testing Strategy

### Backend Testing
```python
# ✅ Good: Unit test with mocks
@pytest.mark.asyncio
async def test_create_user_success():
    # Arrange
    user_repo = Mock(spec=UserRepository)
    email_service = Mock(spec=EmailService)
    service = UserService(user_repo, email_service)
    
    user_data = CreateUserRequest(
        email="test@example.com",
        password="password123",
        first_name="John",
        last_name="Doe"
    )
    
    # Act
    result = await service.create_user(user_data)
    
    # Assert
    user_repo.create.assert_called_once()
    email_service.send_welcome_email.assert_called_once()
    assert result.email == "test@example.com"
```

### Frontend Testing
```typescript
// ✅ Good: React component testing
describe('UserProfile', () => {
  it('displays user information correctly', async () => {
    const mockUser = {
      id: '1',
      email: 'test@example.com',
      firstName: 'John',
      lastName: 'Doe',
    };

    render(<UserProfile userId="1" />);

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });
});
```

## 🔒 Security Guidelines

### Authentication & Authorization
```python
# ✅ Good: JWT token handling
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await user_service.get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

### Input Validation
```python
# ✅ Good: Comprehensive validation
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100, regex=r'^[a-zA-Z\s]+$')
    last_name: str = Field(min_length=1, max_length=100, regex=r'^[a-zA-Z\s]+$')
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
```

## 🚀 Performance Standards

### Database Optimization
```sql
-- ✅ Good: Efficient queries with proper indexing
CREATE INDEX CONCURRENTLY idx_posts_user_id_created_at 
ON posts(user_id, created_at DESC);

-- Query with proper pagination
SELECT * FROM posts 
WHERE user_id = $1 
ORDER BY created_at DESC 
LIMIT 20 OFFSET $2;
```

### Frontend Performance
```typescript
// ✅ Good: Memoization and lazy loading
const UserList = React.memo(({ users }: UserListProps) => {
  const memoizedUsers = useMemo(() => 
    users.filter(user => user.isActive), [users]
  );

  return (
    <div>
      {memoizedUsers.map(user => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  );
});

// ✅ Good: Lazy loading
const LazyUserProfile = React.lazy(() => import('./UserProfile'));
```

## ✅ Code Review Checklist

### Architecture Review
- [ ] Does the code follow the established layered architecture?
- [ ] Are dependencies properly injected?
- [ ] Is the single responsibility principle followed?
- [ ] Are abstractions used appropriately?

### Code Quality
- [ ] Are there proper type hints/types?
- [ ] Is error handling comprehensive?
- [ ] Are naming conventions followed?
- [ ] Is the code well-documented?

### Security
- [ ] Are inputs properly validated?
- [ ] Are authentication/authorization checks in place?
- [ ] Are secrets properly managed?
- [ ] Are SQL injection vulnerabilities avoided?

### Performance
- [ ] Are database queries efficient?
- [ ] Are proper indexes in place?
- [ ] Is caching used appropriately?
- [ ] Are memory leaks avoided?

### Testing
- [ ] Are unit tests present and comprehensive?
- [ ] Are integration tests included?
- [ ] Is test coverage adequate (>80%)?
- [ ] Are edge cases covered?

## 🔧 Refactoring Guidelines

### When to Refactor
- Code duplication exceeds 3 instances
- Function/method exceeds 20 lines
- Class has more than 7 methods
- Cyclomatic complexity > 10
- Test coverage < 80%

### Refactoring Techniques

#### Extract Function
```python
# ❌ Before: Long function
def process_user_registration(user_data):
    # Validate email
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', user_data['email']):
        raise ValidationError("Invalid email")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
    
    # Save to database
    user = User(
        email=user_data['email'],
        password_hash=hashed_password,
        first_name=user_data['first_name'],
        last_name=user_data['last_name']
    )
    db.session.add(user)
    db.session.commit()
    
    # Send welcome email
    send_email(user.email, "Welcome!", "Welcome to our platform!")

# ✅ After: Extracted functions
def validate_email(email: str) -> None:
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValidationError("Invalid email")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def create_user_record(user_data: dict, password_hash: str) -> User:
    user = User(
        email=user_data['email'],
        password_hash=password_hash,
        first_name=user_data['first_name'],
        last_name=user_data['last_name']
    )
    db.session.add(user)
    db.session.commit()
    return user

def process_user_registration(user_data: dict) -> User:
    validate_email(user_data['email'])
    password_hash = hash_password(user_data['password'])
    user = create_user_record(user_data, password_hash)
    send_welcome_email(user.email)
    return user
```

#### Replace Conditional with Polymorphism
```python
# ❌ Before: Complex conditionals
class PaymentProcessor:
    def process_payment(self, payment_type: str, amount: float):
        if payment_type == "credit_card":
            # Credit card processing logic
            pass
        elif payment_type == "paypal":
            # PayPal processing logic
            pass
        elif payment_type == "bank_transfer":
            # Bank transfer processing logic
            pass

# ✅ After: Polymorphic approach
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    @abstractmethod
    def process(self, amount: float) -> PaymentResult:
        pass

class CreditCardProcessor(PaymentProcessor):
    def process(self, amount: float) -> PaymentResult:
        # Credit card processing logic
        pass

class PayPalProcessor(PaymentProcessor):
    def process(self, amount: float) -> PaymentResult:
        # PayPal processing logic
        pass

class PaymentService:
    def __init__(self):
        self.processors = {
            "credit_card": CreditCardProcessor(),
            "paypal": PayPalProcessor(),
            "bank_transfer": BankTransferProcessor()
        }
    
    def process_payment(self, payment_type: str, amount: float) -> PaymentResult:
        processor = self.processors.get(payment_type)
        if not processor:
            raise ValueError(f"Unsupported payment type: {payment_type}")
        return processor.process(amount)
```

### Refactoring Checklist
- [ ] All tests pass after refactoring
- [ ] Code coverage is maintained or improved
- [ ] Performance is not degraded
- [ ] API contracts are preserved
- [ ] Documentation is updated
- [ ] Code review is conducted

## 📚 Additional Resources

### Documentation Standards
- Use docstrings for all public functions/classes
- Include type hints in all function signatures
- Document complex business logic
- Maintain up-to-date API documentation
- Include examples in documentation

### Code Comments
```python
# ✅ Good: Explains why, not what
def calculate_discount(price: float, user_tier: str) -> float:
    """Calculate discount based on user tier.
    
    Premium users get 15% discount to encourage retention
    since they have higher lifetime value.
    """
    if user_tier == "premium":
        return price * 0.15
    return 0.0

# ❌ Bad: States the obvious
def calculate_discount(price: float, user_tier: str) -> float:
    # Check if user is premium
    if user_tier == "premium":
        # Return 15% of price
        return price * 0.15
    # Return 0 if not premium
    return 0.0
```

### Version Control
- Use conventional commits
- Keep commits atomic and focused
- Write descriptive commit messages
- Use feature branches for development
- Perform code reviews before merging

---

## 📋 Summary

This guide establishes comprehensive standards for building maintainable, scalable applications with React JS, Python, PostgreSQL, Temporal, and FastAPI. Regular adherence to these principles will ensure code quality, team productivity, and system reliability.

**Key Takeaways:**
- Follow clean architecture principles
- Implement proper error handling
- Write comprehensive tests
- Use type hints/types consistently
- Maintain security best practices
- Refactor regularly to prevent technical debt

**Next Steps:**
1. Set up linting and formatting tools
2. Implement CI/CD pipeline
3. Create code review templates
4. Establish monitoring and logging
5. Document deployment procedures

## 🔄 Background Jobs & Async Operations

### CRITICAL: Required Reading
Before implementing ANY background job or async database operation:
1. **MUST READ**: `/docs/TROUBLESHOOTING_PLANNING_JOBS.md` - Contains critical lessons learned
2. **MUST FOLLOW**: `/AGENT_REVIEW_CHECKLIST.md` - Quick reference for correct patterns
3. **RUN**: `python scripts/check_async_patterns.py` - Automated pattern checker

### Common Issues to Avoid

#### 1. SQLAlchemy Session Management
```python
# ❌ WRONG: Loading objects outside async task
existing_data = await db.query(...)  # In endpoint
async def background_task():
    # Using existing_data here - objects are detached!
    
# ✅ CORRECT: Load objects inside async task
async def background_task():
    async with AsyncSessionLocal() as task_db:
        # Load all data within task session
        existing_data = await task_db.query(...)
```

#### 2. Job Status Updates
```python
# ❌ WRONG: Forgetting to update job status
async def background_task():
    # Starting work without status update
    
# ✅ CORRECT: Always update status immediately
async def background_task():
    job_manager.update_job_progress(
        job_id,
        status="running",  # CRITICAL!
        current_step="Starting"
    )
```

#### 3. Timestamp Updates
```python
# ❌ WRONG: Not updating timestamps
existing.field = new_value

# ✅ CORRECT: Always update timestamps
existing.field = new_value
existing.updated_at = datetime.utcnow()
existing.updated_by_id = current_user.user_id
db.add(existing)  # Ensure tracking
```

#### 4. Job Manager Methods
```python
# ❌ WRONG: Using non-existent method
job_manager.update_job_status(job_id, "running")

# ✅ CORRECT: Use update_job_progress
job_manager.update_job_progress(
    job_id,
    status="running",
    current_step="Starting"
)
```

### Phase ID Architecture Pattern

#### Understanding Phase IDs
The system uses phase_id as a unique identifier for each phase instance:
```python
# ❌ WRONG: Assuming phase_id from cycle/report
phase_id = f"{cycle_id}_{report_id}_planning"  # Don't construct IDs

# ✅ CORRECT: Always query for phase_id
phase_query = select(WorkflowPhase).where(
    and_(
        WorkflowPhase.cycle_id == cycle_id,
        WorkflowPhase.report_id == report_id,
        WorkflowPhase.phase_name == "Planning"
    )
)
phase_result = await db.execute(phase_query)
phase = phase_result.scalar_one_or_none()
if phase:
    phase_id = phase.phase_id
```

#### Phase-Related Data Loading
```python
# ✅ CORRECT: Load phase-related data using phase_id
# Example: Loading PDE mappings for a phase
mappings_query = select(PlanningPDEMapping).where(
    PlanningPDEMapping.phase_id == phase.phase_id
)
mappings = await db.execute(mappings_query)
```

### Quick Checklist
- [ ] Loaded all DB objects inside async task session?
- [ ] Updated job status to "running" as first action?
- [ ] Set updated_at on all modified records?
- [ ] Used correct job manager methods?
- [ ] Added comprehensive logging?
- [ ] Called db.add() after modifications?
- [ ] Queried for phase_id instead of constructing it?

### Testing Background Jobs
```bash
# Monitor execution
tail -f backend_logs.txt | grep -E "(job_id|status|ERROR)"

# Check specific job
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/jobs/{job_id}/status
```

### Troubleshooting: Background Thread Appears Stuck

#### Issue Description (Fixed: 2025-01-27)
Background threads for LLM-based rule generation (e.g., data profiling) appeared to be stuck in "pending" status, with no apparent progress or error messages.

#### Root Cause Analysis
1. **The thread was actually working** - Processing 118 attributes through LLM service takes 15-20 minutes
2. **Logging inconsistency** - Error handler was using wrong attribute key (`attribute.get('name')` instead of `attribute.get('attribute_name')`)
3. **Misdiagnosis** - The "stuck" appearance was due to:
   - Large workload (118 attributes × ~10 seconds per LLM call)
   - Silent failures from logging bug
   - Lack of detailed progress logging

#### How It Was Fixed
```python
# 1. Fixed logging inconsistency in error handler
# ❌ WRONG: Using incorrect attribute key
logger.error(f"Failed to generate rules for attribute {attribute.get('name')}: {str(attr_error)}")

# ✅ CORRECT: Using consistent attribute key
logger.error(f"Failed to generate rules for attribute {attribute.get('attribute_name')}: {str(attr_error)}")

# 2. Added detailed logging for thread lifecycle
def run_in_background():
    """Run the async LLM generation in a background thread"""
    import traceback
    logger.info(f"Background thread started for job {job_id}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        from app.tasks.data_profiling_tasks import _generate_profiling_rules_async
        logger.info(f"Successfully imported _generate_profiling_rules_async")
        loop.run_until_complete(_generate_profiling_rules_async(...))
        logger.info(f"Background task completed successfully for job {job_id}")
    except Exception as e:
        logger.error(f"Background task failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        job_manager.complete_job(job_id, error=str(e))
    finally:
        loop.close()
        logger.info(f"Background thread finished for job {job_id}")
```

#### Key Lessons
1. **Always check job progress via job manager** - Don't assume "pending" means stuck
   ```python
   # Check job status in jobs_storage.json
   job_manager.get_job_status(job_id)
   ```

2. **LLM operations are slow** - Plan for 5-15 seconds per attribute
   - 100+ attributes = 10-20 minutes total processing time

3. **Consistent attribute naming** - Ensure all code uses the same attribute keys
   - Use `attribute_name` consistently, not `name` or other variations

4. **Daemon threads work correctly** - The `daemon=True` pattern is fine for FastAPI
   - Threads continue running after request completes
   - Just ensure proper error handling and logging

#### Monitoring Long-Running Jobs
```python
# Check job progress
import json
with open('jobs_storage.json', 'r') as f:
    jobs = json.load(f)
    job = jobs.get(job_id)
    print(f"Status: {job.get('status')}")
    print(f"Progress: {job.get('progress_percentage')}%")
    print(f"Current: {job.get('completed_steps')} / {job.get('total_steps')}")
```

## 🐛 Troubleshooting: Data Profiling Rule Execution Issues

### Issue Description (Fixed: 2025-01-28)
Data profiling rules for certain attributes (Current Credit Limit Decimal Precision Check and Current Credit Limit Range Validation) were showing 0 records despite data being present in the database.

### Root Cause Analysis
The issue had two main causes:

1. **Incorrect pandas DataFrame access pattern in LLM-generated rule code**
   - The failing rules were using `.apply()` on a filtered DataFrame and trying to access columns by name within lambda functions
   - When using `df.apply(lambda x: ...)`, `x` is a Series (row), not the DataFrame
   - This caused `KeyError: 'current_credit_limit'` when the lambda tried to access `x[column_name]`

2. **Counting logic error**
   - The Decimal Precision Check rule had incorrect counting logic that resulted in impossible counts (1002 passed out of 1001 total)
   - The logic was subtracting apply results from notna() count incorrectly

### How It Was Fixed

#### 1. Fixed DataFrame access pattern
```python
# ❌ WRONG: Trying to access column by name on a Series
df[df[column_name].notna()].apply(lambda x: not check_decimals(x[column_name]))

# ✅ CORRECT: Apply function directly to the column
df[column_name].apply(check_decimals)
```

#### 2. Fixed counting logic
```python
# ❌ WRONG: Confusing subtraction logic
failed = df[column_name].notna().sum() - df[column_name].apply(check_decimals).sum()

# ✅ CORRECT: Direct counting
passed = df[column_name].apply(check_decimals).sum()
failed = total - passed
```

### Complete fixed rule code examples:

```python
# Fixed Current Credit Limit Decimal Precision Check
def check_rule(df, column_name):
    def check_decimals(x):
        if pd.isna(x): return True
        try: return len(str(float(x)).split('.')[-1]) <= 2 if '.' in str(float(x)) else True
        except: return False
    total = len(df)
    # Fixed: Properly count passed and failed records
    passed = df[column_name].apply(check_decimals).sum()
    failed = total - passed
    return {'passed': passed, 'failed': failed, 'total': total, 'pass_rate': (passed/total)*100 if total > 0 else 0}

# Fixed Current Credit Limit Range Validation
def check_rule(df, column_name):
    def check_range(x):
        if pd.isna(x): return True
        try: return 0 <= float(x) <= 10000000000
        except: return False
    total = len(df)
    # Fixed: Apply check_range directly to the column values
    passed = df[column_name].apply(check_range).sum()
    failed = total - passed
    return {'passed': passed, 'failed': failed, 'total': total, 'pass_rate': (passed/total)*100 if total > 0 else 0}
```

### Key Lessons

1. **Understand pandas apply() behavior**
   - When using `df.apply()`, the function receives each row as a Series
   - When using `df[column].apply()`, the function receives individual values from that column
   - Always test LLM-generated code with actual data

2. **Keep counting logic simple**
   - Count what you need directly (passed records)
   - Calculate the complement (failed = total - passed)
   - Avoid complex subtraction logic that can lead to errors

3. **Debug with extensive logging**
   - Log DataFrame shape and columns before execution
   - Log the actual error messages, not just "rule failed"
   - Verify data is being loaded correctly before blaming the rule code

4. **LLM-generated code needs validation**
   - Even well-structured prompts can produce code with subtle errors
   - Always test generated code with sample data
   - Common pitfall: Incorrect DataFrame access patterns

## 🔁 Component Reuse Pattern

### Overview
The application follows a component reuse pattern that allows complex UI components to be shared across different phases while maintaining phase-specific behavior through role-based permissions and callbacks.

### Key Benefits
1. **Consistency**: Users see the same interface across different phases
2. **Maintainability**: Single source of truth for component logic
3. **Efficiency**: Reduced code duplication and faster development
4. **Flexibility**: Components adapt behavior based on context

### Implementation Example: TestExecutionTable

#### Component Design
The `TestExecutionTable` component is designed to be reusable across multiple phases:

```typescript
interface TestExecutionTableProps {
  testCases: TestCase[];
  onExecuteTest?: (testCase: TestCase) => void;
  onViewEvidence?: (testCase: TestCase) => void;
  onViewComparison?: (testCase: TestCase) => void;
  onReviewResult?: (testCase: TestCase, decision: 'pass' | 'fail' | 'resend') => void;
  userRole?: string;  // Key prop for role-based behavior
}
```

#### Usage in Test Execution Phase
```typescript
// Full functionality for testers
<TestExecutionTable
  testCases={testCases}
  onExecuteTest={handleExecuteTest}
  onViewEvidence={handleViewEvidence}
  onViewComparison={handleViewComparison}
  onReviewResult={handleReviewResult}
  userRole="Tester"
/>
```

#### Usage in Observation Management Phase
```typescript
// Read-only view with observation creation
<TestExecutionTable
  testCases={testExecutionResults}
  onReviewResult={(testCase, decision) => {
    // Open observation dialog for failed tests
    setSelectedTestCase(testCase);
    setObservationDialogOpen(true);
  }}
  userRole="Observer"  // Makes component read-only
/>
```

### Pattern Guidelines

#### 1. Design for Flexibility
```typescript
// ✅ Good: Optional callbacks for different use cases
interface ComponentProps {
  data: DataType[];
  onAction?: (item: DataType) => void;
  onSecondaryAction?: (item: DataType) => void;
  userRole?: string;
  readOnly?: boolean;
}

// ❌ Bad: Rigid interface that assumes specific usage
interface ComponentProps {
  data: DataType[];
  onTestExecute: (item: DataType) => void;  // Too specific
  isTestPhase: boolean;  // Phase-specific flag
}
```

#### 2. Role-Based Behavior
```typescript
// Inside component
const renderActions = () => {
  if (userRole === 'Observer') {
    // Show read-only actions (view, create observation)
    return (
      <IconButton onClick={() => onReviewResult?.(item, 'fail')}>
        <BugReportIcon />
      </IconButton>
    );
  } else if (userRole === 'Tester') {
    // Show full test execution actions
    return <TestExecutionResults {...props} />;
  }
};
```

#### 3. Data Transformation at Usage Point
```typescript
// ✅ Good: Transform data to match component interface
const transformedData = rawData.map(item => ({
  ...item,
  // Map fields to expected names
  test_case_id: item.id,
  data_owner_name: dataOwners[item.data_owner_id]?.name || 'Unknown',
  // Add computed fields
  has_evidence: item.evidence_count > 0,
}));

<ReusableComponent testCases={transformedData} />
```

### Candidates for Component Reuse

#### 1. Evidence Display Components
- `EvidenceModal`: Already reused across phases
- `EvidenceValidationResults`: Can be used in multiple contexts

#### 2. Planning Phase Components
- Attribute selection tables
- PDE mapping interfaces
- Rule configuration panels

#### 3. Scoping Phase Components
- Sample selection grids
- Test case builders
- Coverage visualizations

#### 4. Common Patterns
- Data tables with actions
- Review/approval workflows
- Status tracking displays
- Progress indicators

### Implementation Checklist

When implementing reusable components:

- [ ] Design props interface to be phase-agnostic
- [ ] Use optional callbacks for phase-specific actions
- [ ] Include role/permission props for behavior control
- [ ] Avoid hardcoded phase names or assumptions
- [ ] Document different usage contexts
- [ ] Test component in all intended contexts
- [ ] Ensure consistent styling across uses

### Example: Making a Planning Component Reusable

#### Before: Phase-specific component
```typescript
const PlanningAttributeTable = ({ planningPhaseId, onSelectAttribute }) => {
  // Hardcoded for planning phase only
};
```

#### After: Reusable component
```typescript
interface AttributeTableProps {
  attributes: Attribute[];
  selectedAttributes?: Set<number>;
  onSelectAttribute?: (attr: Attribute) => void;
  onViewDetails?: (attr: Attribute) => void;
  selectionMode?: 'single' | 'multiple' | 'none';
  showActions?: boolean;
  userRole?: string;
}

const AttributeTable: React.FC<AttributeTableProps> = ({
  attributes,
  selectedAttributes = new Set(),
  onSelectAttribute,
  onViewDetails,
  selectionMode = 'multiple',
  showActions = true,
  userRole = 'Planner',
}) => {
  // Flexible implementation that adapts to context
};
```

### Benefits Realized

1. **Test Execution Table Reuse**
   - Saved ~500 lines of duplicate code
   - Consistent UI between Test Execution and Observation phases
   - Single point of maintenance for bug fixes

2. **Evidence Modal Reuse**
   - Used in 4+ different contexts
   - Unified evidence viewing experience
   - Reduced testing surface area

3. **Future Opportunities**
   - Planning attribute selection → Scoping attribute review
   - Test case builder → Test case viewer
   - Status indicators → Progress tracking

### Best Practices

1. **Start Specific, Refactor to General**
   - Build for one use case first
   - Identify reuse opportunities
   - Refactor with minimal breaking changes

2. **Maintain Backwards Compatibility**
   - Keep existing props working
   - Use sensible defaults
   - Document migration path

3. **Test Thoroughly**
   - Unit tests for each usage context
   - Integration tests for phase interactions
   - Visual regression tests for UI consistency

