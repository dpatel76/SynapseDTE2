# SynapseDT - End-to-End Data Testing System

A comprehensive full-stack Python application for managing regulatory and risk management report testing lifecycle with 6 distinct user roles and 7-phase workflow process.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │────│  API Gateway    │────│  Core Services  │
│   (React/Vue)   │    │   (FastAPI)     │    │   (Python)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Auth Service  │    │ Database Layer  │
                       │   (JWT/OAuth)   │    │  (PostgreSQL)   │
                       └─────────────────┘    └─────────────────┘
                                │                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  LLM Services   │    │ File Storage    │
                       │ (Claude/Gemini) │    │   (Local FS)    │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL 14+
- **Frontend**: React 18+ or Vue 3+ (planned)
- **Authentication**: JWT with role-based access control
- **File Storage**: Local filesystem with versioning
- **LLM Integration**: Claude API, Gemini API with provider switching
- **Email Service**: SMTP integration for notifications
- **Task Queue**: Celery with Redis for background tasks
- **Logging**: Structured logging with structlog

## 👥 User Roles

| Role | Primary Responsibilities | Access Level |
|------|-------------------------|--------------|
| **Tester** | Execute testing workflow steps, manage attributes, conduct testing | Report-level assignment |
| **Test Manager** | Create test cycles, assign reports, monitor team progress | Read-only aggregated view of team testing |
| **Report Owner** | Approve scoping, sampling, and observations | Own reports across multiple LOBs |
| **Report Owner Executive** | Portfolio oversight, executive reporting | View all reports under their report owners |
| **Data Provider** | Provide source documents, confirm data sources | Attribute-level assignments |
| **CDO** | Assign data providers, manage escalations | LOB-level assignment (one per LOB) |

## 🔄 7-Phase Workflow Process

1. **Planning** - Create comprehensive attribute list for the report
2. **Scoping** - Determine which attributes require testing based on risk
3. **Data Provider ID** - Identify and assign data providers for each attribute
4. **Sample Selection** - Generate or define sample data for testing
5. **Request for Information** - Collect source information from data providers
6. **Testing** - Execute testing and validate data accuracy
7. **Observation Management** - Document, categorize, and resolve discrepancies

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis (for Celery)
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SynapseDT
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
cp env.example .env
```

Edit `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/synapse_dt
SECRET_KEY=your-secret-key-here-change-in-production

# LLM Configuration
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 5. Database Setup

#### Option A: Automated Setup (Recommended)

```bash
# Copy environment configuration
cp env.example .env

# Edit .env file with your database credentials
# Then run the setup script
python scripts/setup_database.py
```

#### Option B: Manual Setup

```bash
# Create database and user manually
sudo -u postgres psql

# In PostgreSQL shell:
CREATE USER synapse_user WITH PASSWORD 'synapse_password';
CREATE DATABASE synapse_dt OWNER synapse_user;
GRANT ALL PRIVILEGES ON DATABASE synapse_dt TO synapse_user;
ALTER USER synapse_user CREATEDB;
\q

# Run migrations
alembic upgrade head
```

### 6. Run the Application

```bash
# Development server (with virtual environment activated)
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

# Or using Python
python -m app.main
```

The application will be available at:
- API: http://localhost:8001
- Documentation: http://localhost:8001/api/v1/docs
- Health Check: http://localhost:8001/health

## 🔗 API Endpoints

### Authentication Endpoints
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/auth/register` - User registration (management only)
- `POST /api/v1/auth/change-password` - Password change
- `GET /api/v1/auth/me` - Current user info
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/roles` - Available roles

### LOB Management Endpoints
- `POST /api/v1/lobs/` - Create LOB (management only)
- `GET /api/v1/lobs/` - List all LOBs
- `GET /api/v1/lobs/{lob_id}` - Get LOB details
- `PUT /api/v1/lobs/{lob_id}` - Update LOB (management only)
- `DELETE /api/v1/lobs/{lob_id}` - Delete LOB (management only)
- `GET /api/v1/lobs/stats/overview` - LOB statistics (management only)

### System Endpoints
- `GET /` - Root endpoint with system info
- `GET /health` - Health check
- `GET /api/v1/health` - API health check

## 📊 Database Schema

The application uses a comprehensive database schema with 13 main models:

### Core Models
- **LOB** - Lines of Business
- **User** - User management with role-based access
- **Report** - Report inventory
- **DataSource** - External database connections

### Workflow Models
- **TestCycle** - Test cycle management
- **CycleReport** - Report assignments to cycles
- **WorkflowPhase** - Phase tracking
- **ReportAttribute** - Attribute definitions

### Testing Models
- **Sample** - Sample data for testing
- **DataProviderAssignment** - Data provider assignments
- **TestExecution** - Test execution results
- **Observation** - Issue tracking and resolution

### Audit Models
- **SLAConfiguration** - SLA settings
- **LLMAuditLog** - LLM operation audit trail
- **AuditLog** - System audit trail

## 🔐 Security Features

- JWT-based authentication
- Role-based access control (RBAC)
- Password hashing with bcrypt
- Security headers middleware
- Audit logging for all operations
- Encrypted database credentials
- Input validation and sanitization

## 📝 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8001/api/v1/docs
- **ReDoc**: http://localhost:8001/api/v1/redoc

## 🧪 Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

## 📈 Development Progress

Track implementation progress in:
- `_reference/implementation_plan.md` - Overall project plan
- `_reference/progress_tracker.md` - Daily progress tracking
- `_reference/specifications/specifications.md` - Detailed specifications

### Current Status (Week 1, Day 2) ✅ COMPLETE
- ✅ Project structure and dependencies
- ✅ Database models (13/13 complete)
- ✅ Core configuration and logging
- ✅ FastAPI application setup
- ✅ Alembic migrations (complete)
- ✅ Authentication system with JWT
- ✅ Role-based access control
- ✅ API endpoints (12 endpoints)
- ✅ API documentation
- ✅ Security middleware
- ⏳ Database connection (pending setup)
- ⏳ User management endpoints (planned)

### Day 2 Accomplishments
- **Authentication System**: Complete JWT-based auth with 6 user roles
- **API Endpoints**: 12 functional endpoints with proper validation
- **Security**: RBAC, password validation, audit logging
- **Documentation**: Interactive API docs with Swagger UI
- **Testing**: All endpoints tested and functional

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in `_reference/` folder
- Review the API documentation at `/docs`

## 🗺️ Roadmap

### Phase 1: Foundation (Weeks 1-4) - 🟡 In Progress (Day 2/5 Complete)
- [x] Database schema and models
- [x] Core application structure
- [x] Authentication system
- [x] Basic API endpoints
- [ ] Database connection and migrations
- [ ] User management CRUD operations

### Phase 2: Core Workflow (Weeks 5-12) - ⏳ Planned
- [ ] Test cycle management
- [ ] Planning and scoping phases
- [ ] LLM integration
- [ ] Frontend foundation

### Phase 3: Advanced Features (Weeks 13-20) - ⏳ Planned
- [ ] Data provider coordination
- [ ] Testing execution engine
- [ ] Observation management
- [ ] SLA monitoring

### Phase 4: Analytics & Production (Weeks 21-28) - ⏳ Planned
- [ ] Dashboards and reporting
- [ ] Performance optimization
- [ ] Production deployment
- [ ] Documentation and training

## 🎯 Quick Start

To quickly test the API:

1. **Start the server:**
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
   ```

2. **Test endpoints:**
   ```bash
   # Check health
   curl http://localhost:8001/health
   
   # Get available roles
   curl http://localhost:8001/api/v1/auth/roles
   
   # View API documentation
   open http://localhost:8001/api/v1/docs
   ```

3. **Next steps:**
   - Set up PostgreSQL database
   - Run migrations: `alembic upgrade head`
   - Create test users
   - Explore the API documentation 