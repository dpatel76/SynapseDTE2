# COMPREHENSIVE PROJECT FILE AUDIT - SynapseDTE

## Executive Summary
This document provides a granular audit of EVERY file in the SynapseDTE project, analyzing purpose, usage status, consolidation opportunities, and naming convention issues.

---

## BACKEND FILES (/app directory)

### Root Application Files

#### `/app/__init__.py`
- **Purpose**: Python package initialization file for the app module
- **Status**: ACTIVELY USED - Required for Python module structure
- **Consolidation**: Cannot be consolidated - Essential for Python packaging
- **Naming**: CORRECT - Standard Python convention

#### `/app/main.py`
- **Purpose**: FastAPI application entry point, contains app initialization, middleware setup, and route registration
- **Status**: ACTIVELY USED - Core application entry point
- **Consolidation**: Cannot be consolidated - Central application file
- **Naming**: CORRECT - Standard FastAPI convention

#### `/app/main.py.backup`
- **Purpose**: Backup copy of main.py
- **Status**: ORPHANED - Backup file, not actively used
- **Consolidation**: DELETE - Unnecessary backup in version control
- **Naming**: CLEANUP NEEDED - Backup files should not be in repo

---

### API Layer (/app/api/)

#### `/app/api/__init__.py`
- **Purpose**: API package initialization
- **Status**: ACTIVELY USED - Required for Python module structure
- **Consolidation**: Cannot be consolidated
- **Naming**: CORRECT

#### `/app/api/v1/__init__.py`
- **Purpose**: API v1 package initialization
- **Status**: ACTIVELY USED - Required for Python module structure
- **Consolidation**: Cannot be consolidated
- **Naming**: CORRECT

#### `/app/api/v1/api.py`
- **Purpose**: Main API router aggregating all endpoint routers
- **Status**: ACTIVELY USED - Core API routing file
- **Consolidation**: Cannot be consolidated - Central routing
- **Naming**: CORRECT

#### `/app/api/v1/api.py.backup` & `/app/api/v1/api.py.role_backup`
- **Purpose**: Backup copies of api.py
- **Status**: ORPHANED - Backup files
- **Consolidation**: DELETE - Unnecessary backups
- **Naming**: CLEANUP NEEDED - Remove backup files

#### `/app/api/v1/api_clean.py`
- **Purpose**: Alternative/clean version of API routing
- **Status**: QUESTIONABLE - Potential duplicate functionality
- **Consolidation**: REVIEW NEEDED - May be consolidated with api.py
- **Naming**: INCONSISTENT - Should follow standard naming

#### `/app/api/v1/deps.py`
- **Purpose**: Dependency injection functions for API endpoints
- **Status**: ACTIVELY USED - Essential for FastAPI dependency injection
- **Consolidation**: Cannot be consolidated - Core dependency management
- **Naming**: CORRECT

#### `/app/api/v1/metrics.py`
- **Purpose**: Metrics-related API functions (unclear if endpoint or utility)
- **Status**: UNCLEAR - May duplicate functionality in endpoints/metrics.py
- **Consolidation**: CONSOLIDATION CANDIDATE - Review against endpoints/metrics.py
- **Naming**: AMBIGUOUS - Unclear if endpoint or utility

---

### API Endpoints (/app/api/v1/endpoints/)

#### `/app/api/v1/endpoints/__init__.py`
- **Purpose**: Endpoints package initialization
- **Status**: ACTIVELY USED - Required for Python module structure
- **Consolidation**: Cannot be consolidated
- **Naming**: CORRECT

#### `/app/api/v1/endpoints/DEPRECATED_METRICS.md`
- **Purpose**: Documentation for deprecated metrics functionality
- **Status**: DOCUMENTATION - Informational
- **Consolidation**: REVIEW - May be outdated
- **Naming**: CORRECT - Clear deprecation marker

#### Core Endpoint Files Analysis:

**Authentication & Authorization:**
- `/app/api/v1/endpoints/auth.py` - ACTIVELY USED - Core auth endpoints
- `/app/api/v1/endpoints/auth_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/users.py` - ACTIVELY USED - User management
- `/app/api/v1/endpoints/users_clean.py` - DUPLICATE - Consolidation needed

**Administrative Functions:**
- `/app/api/v1/endpoints/admin.py` - ACTIVELY USED - Admin endpoints
- `/app/api/v1/endpoints/admin_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/admin_rbac.py` - ACTIVELY USED - RBAC admin functions
- `/app/api/v1/endpoints/admin_rbac_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/admin_sla.py` - ACTIVELY USED - SLA admin functions
- `/app/api/v1/endpoints/admin_sla_clean.py` - DUPLICATE - Consolidation needed

**Core Workflow Endpoints:**
- `/app/api/v1/endpoints/cycles.py` - ACTIVELY USED - Test cycle management
- `/app/api/v1/endpoints/cycles_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/cycle_reports.py` - ACTIVELY USED - Cycle report management
- `/app/api/v1/endpoints/cycle_reports_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/reports.py` - ACTIVELY USED - Report management
- `/app/api/v1/endpoints/reports_clean.py` - DUPLICATE - Consolidation needed

**Dashboard Endpoints:**
- `/app/api/v1/endpoints/dashboards.py` - ACTIVELY USED - Dashboard data
- `/app/api/v1/endpoints/dashboards_clean.py` - DUPLICATE - Consolidation needed

**Workflow Phase Endpoints:**
- `/app/api/v1/endpoints/planning.py` - ACTIVELY USED - Planning phase
- `/app/api/v1/endpoints/planning_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/scoping.py` - ACTIVELY USED - Scoping phase
- `/app/api/v1/endpoints/scoping_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/scoping_submission.py` - SPECIALIZED - Scoping submissions
- `/app/api/v1/endpoints/sample_selection.py` - ACTIVELY USED - Sample selection phase
- `/app/api/v1/endpoints/sample_selection_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/sample_selection_old.py` - ORPHANED - Old version
- `/app/api/v1/endpoints/request_info.py` - ACTIVELY USED - Request info phase
- `/app/api/v1/endpoints/request_info_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/test_execution.py` - ACTIVELY USED - Test execution phase
- `/app/api/v1/endpoints/test_execution_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/test_execution_refactored.py` - REFACTORED VERSION - Consolidation needed
- `/app/api/v1/endpoints/testing_execution.py` - NAMING INCONSISTENCY - Should be test_execution
- `/app/api/v1/endpoints/testing_execution_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/testing_execution_refactored.py` - DUPLICATE - Consolidation needed

**Observation Management:**
- `/app/api/v1/endpoints/observation_management.py` - ACTIVELY USED - Observation management
- `/app/api/v1/endpoints/observation_management_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/observation_enhanced.py` - ENHANCED VERSION - Consolidation needed

**Data Management:**
- `/app/api/v1/endpoints/data_owner.py` - ACTIVELY USED - Data owner endpoints
- `/app/api/v1/endpoints/data_owner_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/data_provider.py` - LEGACY - May be renamed to data_owner
- `/app/api/v1/endpoints/data_profiling_clean.py` - STANDALONE - Data profiling
- `/app/api/v1/endpoints/data_sources.py` - ACTIVELY USED - Data source management
- `/app/api/v1/endpoints/data_sources_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/data_dictionary.py` - ACTIVELY USED - Data dictionary

**Metrics & Analytics:**
- `/app/api/v1/endpoints/metrics.py` - ACTIVELY USED - Core metrics
- `/app/api/v1/endpoints/metrics_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/metrics_simple.py` - SIMPLIFIED VERSION - Consolidation candidate
- `/app/api/v1/endpoints/metrics_v2.py` - VERSION 2 - Consolidation candidate

**LLM Integration:**
- `/app/api/v1/endpoints/llm.py` - ACTIVELY USED - LLM endpoints
- `/app/api/v1/endpoints/llm_clean.py` - DUPLICATE - Consolidation needed

**Supporting Services:**
- `/app/api/v1/endpoints/lobs.py` - ACTIVELY USED - Line of Business
- `/app/api/v1/endpoints/lobs_clean.py` - DUPLICATE - Consolidation needed
- `/app/api/v1/endpoints/sla.py` - ACTIVELY USED - SLA management
- `/app/api/v1/endpoints/background_jobs.py` - ACTIVELY USED - Job management
- `/app/api/v1/endpoints/activity_states.py` - ACTIVELY USED - Activity state management
- `/app/api/v1/endpoints/versioning.py` - ACTIVELY USED - Version management

**Workflow Management:**
- `/app/api/v1/endpoints/workflow_clean.py` - Workflow endpoints
- `/app/api/v1/endpoints/workflow_compensation.py` - Compensation workflows
- `/app/api/v1/endpoints/workflow_management.py` - General workflow management
- `/app/api/v1/endpoints/workflow_metrics.py` - Workflow metrics
- `/app/api/v1/endpoints/workflow_start.py` - Workflow initiation
- `/app/api/v1/endpoints/workflow_versioning.py` - Workflow versioning

**Testing & Utilities:**
- `/app/api/v1/endpoints/test.py` - Test endpoints
- `/app/api/v1/endpoints/test_report.py` - Test reporting
- `/app/api/v1/endpoints/temporal_signals.py` - Temporal workflow signals

---

### Application Layer (/app/application/)

#### Data Transfer Objects (DTOs)

**Legacy DTO Structure (/app/application/dto/):**
- `/app/application/dto/__init__.py` - ACTIVELY USED - Package init
- `/app/application/dto/report_dto.py` - LEGACY DTO - May be consolidated
- `/app/application/dto/test_cycle_dto.py` - LEGACY DTO - May be consolidated  
- `/app/application/dto/workflow_dto.py` - LEGACY DTO - May be consolidated

**Current DTO Structure (/app/application/dtos/):**
- `/app/application/dtos/__init__.py` - ACTIVELY USED - Package init
- `/app/application/dtos/admin.py` - ACTIVELY USED - Admin DTOs
- `/app/application/dtos/admin_rbac.py` - ACTIVELY USED - RBAC admin DTOs
- `/app/application/dtos/auth.py` - ACTIVELY USED - Authentication DTOs
- `/app/application/dtos/cycle_report.py` - ACTIVELY USED - Cycle report DTOs
- `/app/application/dtos/dashboard.py` - ACTIVELY USED - Dashboard DTOs
- `/app/application/dtos/data_owner.py` - ACTIVELY USED - Data owner DTOs
- `/app/application/dtos/data_source.py` - ACTIVELY USED - Data source DTOs
- `/app/application/dtos/llm.py` - ACTIVELY USED - LLM DTOs
- `/app/application/dtos/lob.py` - ACTIVELY USED - Line of Business DTOs
- `/app/application/dtos/metrics.py` - ACTIVELY USED - Metrics DTOs
- `/app/application/dtos/observation.py` - ACTIVELY USED - Observation DTOs
- `/app/application/dtos/report.py` - ACTIVELY USED - Report DTOs
- `/app/application/dtos/request_info.py` - ACTIVELY USED - Request info DTOs
- `/app/application/dtos/sample_selection.py` - ACTIVELY USED - Sample selection DTOs
- `/app/application/dtos/sla.py` - ACTIVELY USED - SLA DTOs
- `/app/application/dtos/test_cycle.py` - ACTIVELY USED - Test cycle DTOs
- `/app/application/dtos/user.py` - ACTIVELY USED - User DTOs

**CONSOLIDATION OPPORTUNITY**: The legacy `/dto/` directory appears to be superseded by `/dtos/` - should be reviewed for consolidation.

#### Interface Definitions (/app/application/interfaces/)
- `/app/application/interfaces/__init__.py` - ACTIVELY USED - Package init
- `/app/application/interfaces/external_services.py` - ACTIVELY USED - External service interfaces
- `/app/application/interfaces/repositories.py` - ACTIVELY USED - Repository interfaces
- `/app/application/interfaces/services.py` - ACTIVELY USED - Service interfaces

#### Mappers (/app/application/mappers/)
- `/app/application/mappers/sample_selection_mapper.py` - ACTIVELY USED - Sample selection mapping logic

#### Use Cases (/app/application/use_cases/)
- `/app/application/use_cases/__init__.py` - ACTIVELY USED - Package init
- `/app/application/use_cases/base.py` - ACTIVELY USED - Base use case class
- `/app/application/use_cases/admin.py` - ACTIVELY USED - Admin use cases
- `/app/application/use_cases/admin_rbac.py` - ACTIVELY USED - RBAC admin use cases
- `/app/application/use_cases/auth.py` - ACTIVELY USED - Authentication use cases
- `/app/application/use_cases/cycle_report.py` - ACTIVELY USED - Cycle report use cases
- `/app/application/use_cases/dashboard.py` - ACTIVELY USED - Dashboard use cases
- `/app/application/use_cases/data_owner.py` - ACTIVELY USED - Data owner use cases
- `/app/application/use_cases/data_owner_identification.py` - ACTIVELY USED - Data owner ID use cases
- `/app/application/use_cases/data_source.py` - ACTIVELY USED - Data source use cases
- `/app/application/use_cases/llm.py` - ACTIVELY USED - LLM use cases
- `/app/application/use_cases/metrics.py` - ACTIVELY USED - Metrics use cases
- `/app/application/use_cases/observation.py` - ACTIVELY USED - Observation use cases
- `/app/application/use_cases/observation_management.py` - ACTIVELY USED - Observation management use cases
- `/app/application/use_cases/planning.py` - ACTIVELY USED - Planning phase use cases
- `/app/application/use_cases/request_for_information.py` - NAMING ISSUE - Should be request_info
- `/app/application/use_cases/request_info.py` - ACTIVELY USED - Request info use cases
- `/app/application/use_cases/sample_selection.py` - ACTIVELY USED - Sample selection use cases
- `/app/application/use_cases/scoping.py` - ACTIVELY USED - Scoping use cases
- `/app/application/use_cases/sla.py` - ACTIVELY USED - SLA use cases
- `/app/application/use_cases/test_execution.py` - ACTIVELY USED - Test execution use cases
- `/app/application/use_cases/testing_execution.py.backup` - ORPHANED - Backup file
- `/app/application/use_cases/testing_report.py` - ACTIVELY USED - Test reporting use cases
- `/app/application/use_cases/workflow.py` - ACTIVELY USED - Workflow use cases

**NAMING INCONSISTENCY**: `request_for_information.py` vs `request_info.py` - should be standardized.

---

### Core Infrastructure (/app/core/)

#### `/app/core/__init__.py`
- **Purpose**: Core package initialization
- **Status**: ACTIVELY USED - Required for Python module structure
- **Consolidation**: Cannot be consolidated
- **Naming**: CORRECT

#### Configuration & Security
- `/app/core/config.py` - ACTIVELY USED - Application configuration
- `/app/core/config.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/core/auth.py` - ACTIVELY USED - Authentication logic
- `/app/core/auth.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/core/security.py` - ACTIVELY USED - Security utilities
- `/app/core/security.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/core/permissions.py` - ACTIVELY USED - Permission management
- `/app/core/permissions.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/core/rbac_config.py` - ACTIVELY USED - RBAC configuration
- `/app/core/rbac_config.py.role_backup` - ORPHANED - Backup file, should be deleted

#### Database & Dependencies
- `/app/core/database.py` - ACTIVELY USED - Database configuration and session management
- `/app/core/database_refactored.py` - REFACTORED VERSION - Consolidation candidate
- `/app/core/dependencies.py` - ACTIVELY USED - FastAPI dependency injection
- `/app/core/dependencies.py.role_backup` - ORPHANED - Backup file, should be deleted

#### Application Services
- `/app/core/exceptions.py` - ACTIVELY USED - Custom exception definitions
- `/app/core/logging.py` - ACTIVELY USED - Logging configuration
- `/app/core/middleware.py` - ACTIVELY USED - FastAPI middleware
- `/app/core/middleware_performance.py` - SPECIALIZED - Performance middleware
- `/app/core/performance.py` - ACTIVELY USED - Performance monitoring
- `/app/core/activity_states.py` - ACTIVELY USED - Activity state definitions
- `/app/core/llm_config.py` - ACTIVELY USED - LLM configuration
- `/app/core/prompt_manager.py` - ACTIVELY USED - LLM prompt management

#### Background Processing
- `/app/core/background_jobs.py` - ACTIVELY USED - Background job management
- `/app/core/celery_app.py` - ACTIVELY USED - Celery configuration

**CLEANUP NEEDED**: Multiple `.role_backup` files should be removed as they're not needed in version control.

---

### CRUD Layer (/app/crud/)

#### `/app/crud/base.py`
- **Purpose**: Base CRUD operations class
- **Status**: ACTIVELY USED - Foundation for all CRUD operations
- **Consolidation**: Cannot be consolidated - Base class
- **Naming**: CORRECT

#### `/app/crud/crud_report.py`
- **Purpose**: Report-specific CRUD operations
- **Status**: ACTIVELY USED - Report data access
- **Consolidation**: Cannot be consolidated - Specialized operations
- **Naming**: INCONSISTENT - Should be `report.py` following convention

---

### Database Layer (/app/db/)

#### `/app/db/optimized_session.py`
- **Purpose**: Optimized database session management
- **Status**: ACTIVELY USED - Database performance optimization
- **Consolidation**: Cannot be consolidated - Specialized functionality
- **Naming**: CORRECT

---

### Domain Layer (/app/domain/)

This appears to be implementing Domain-Driven Design (DDD) patterns.

#### Entities (/app/domain/entities/)
- `/app/domain/entities/__init__.py` - ACTIVELY USED - Package init
- `/app/domain/entities/base.py` - ACTIVELY USED - Base entity class
- `/app/domain/entities/report.py` - ACTIVELY USED - Report domain entity
- `/app/domain/entities/sample_selection.py` - ACTIVELY USED - Sample selection entity
- `/app/domain/entities/test_cycle.py` - ACTIVELY USED - Test cycle entity
- `/app/domain/entities/user.py` - ACTIVELY USED - User entity

#### Events (/app/domain/events/)
- `/app/domain/events/__init__.py` - ACTIVELY USED - Package init
- `/app/domain/events/base.py` - ACTIVELY USED - Base event class
- `/app/domain/events/test_cycle_events.py` - ACTIVELY USED - Test cycle domain events
- `/app/domain/events/workflow_events.py` - ACTIVELY USED - Workflow domain events

#### Value Objects (/app/domain/value_objects/)
- `/app/domain/value_objects/__init__.py` - ACTIVELY USED - Package init
- `/app/domain/value_objects/cycle_status.py` - ACTIVELY USED - Cycle status value object
- `/app/domain/value_objects/email.py` - ACTIVELY USED - Email value object
- `/app/domain/value_objects/identifiers.py` - ACTIVELY USED - ID value objects
- `/app/domain/value_objects/password.py` - ACTIVELY USED - Password value object
- `/app/domain/value_objects/report_assignment.py` - ACTIVELY USED - Report assignment value object
- `/app/domain/value_objects/risk_score.py` - ACTIVELY USED - Risk score value object

---

### Infrastructure Layer (/app/infrastructure/)

This implements the infrastructure layer of clean architecture.

#### Dependency Injection
- `/app/infrastructure/__init__.py` - ACTIVELY USED - Package init
- `/app/infrastructure/container.py` - ACTIVELY USED - DI container
- `/app/infrastructure/di.py` - ACTIVELY USED - Dependency injection setup

#### External Services (/app/infrastructure/external_services/)
- `/app/infrastructure/external_services/auth_service_impl.py` - ACTIVELY USED - Auth service implementation
- `/app/infrastructure/external_services/email_service_impl.py` - ACTIVELY USED - Email service implementation
- `/app/infrastructure/external_services/file_storage_service_impl.py` - ACTIVELY USED - File storage implementation
- `/app/infrastructure/external_services/llm_service_impl.py` - ACTIVELY USED - LLM service implementation
- `/app/infrastructure/external_services/temporal_service_impl.py` - ACTIVELY USED - Temporal service implementation

#### Repositories (/app/infrastructure/repositories/)
- `/app/infrastructure/repositories/__init__.py` - ACTIVELY USED - Package init
- `/app/infrastructure/repositories/report_repository.py` - ACTIVELY USED - Report repository interface
- `/app/infrastructure/repositories/sqlalchemy_report_repository.py` - ACTIVELY USED - SQLAlchemy report repo
- `/app/infrastructure/repositories/sqlalchemy_sample_selection_repository.py` - ACTIVELY USED - Sample selection repo
- `/app/infrastructure/repositories/sqlalchemy_test_cycle_repository.py` - ACTIVELY USED - Test cycle repo
- `/app/infrastructure/repositories/sqlalchemy_user_repository.py` - ACTIVELY USED - User repo
- `/app/infrastructure/repositories/sqlalchemy_workflow_repository.py` - ACTIVELY USED - Workflow repo
- `/app/infrastructure/repositories/test_cycle_repository.py` - ACTIVELY USED - Test cycle interface
- `/app/infrastructure/repositories/user_repository.py` - ACTIVELY USED - User repository interface

#### Infrastructure Services (/app/infrastructure/services/)
- `/app/infrastructure/services/__init__.py` - ACTIVELY USED - Package init
- `/app/infrastructure/services/audit_service_impl.py` - ACTIVELY USED - Audit service implementation
- `/app/infrastructure/services/document_storage_service_impl.py` - ACTIVELY USED - Document storage
- `/app/infrastructure/services/email_service_impl.py` - ACTIVELY USED - Email service implementation
- `/app/infrastructure/services/llm_service_impl.py` - ACTIVELY USED - LLM service implementation
- `/app/infrastructure/services/notification_service_impl.py` - ACTIVELY USED - Notification service
- `/app/infrastructure/services/sla_service_impl.py` - ACTIVELY USED - SLA service implementation

---

### Models Layer (/app/models/)

SQLAlchemy ORM model definitions.

#### Core Models
- `/app/models/__init__.py` - ACTIVELY USED - Package init and model exports
- `/app/models/__init__.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/models/base.py` - ACTIVELY USED - Base model class
- `/app/models/audit.py` - ACTIVELY USED - Audit trail models
- `/app/models/user.py` - ACTIVELY USED - User and role models
- `/app/models/user.py.role_backup` - ORPHANED - Backup file, should be deleted

#### Business Domain Models
- `/app/models/report.py` - ACTIVELY USED - Report models
- `/app/models/report.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/models/report_attribute.py` - ACTIVELY USED - Report attribute models
- `/app/models/report_attribute.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/models/test_cycle.py` - ACTIVELY USED - Test cycle models
- `/app/models/test_cycle.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/models/test_execution.py` - ACTIVELY USED - Test execution models
- `/app/models/testing.py` - ACTIVELY USED - General testing models
- `/app/models/testing.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/models/testing_execution.py.backup` - ORPHANED - Backup file, should be deleted

#### Workflow & Phase Models
- `/app/models/cycle_report.py` - ACTIVELY USED - Cycle-report relationship models
- `/app/models/sample_selection.py` - ACTIVELY USED - Sample selection models
- `/app/models/sample_selection_phase.py` - ACTIVELY USED - Sample selection phase models
- `/app/models/scoping.py` - ACTIVELY USED - Scoping phase models
- `/app/models/request_info.py` - ACTIVELY USED - Request info phase models
- `/app/models/request_info.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/models/workflow.py` - ACTIVELY USED - Workflow models
- `/app/models/workflow_tracking.py` - ACTIVELY USED - Workflow tracking models

#### Observation & Management Models
- `/app/models/observation_enhanced.py` - ACTIVELY USED - Enhanced observation models
- `/app/models/observation_management.py` - ACTIVELY USED - Observation management models

#### Data & Configuration Models
- `/app/models/data_owner.py` - ACTIVELY USED - Data owner models
- `/app/models/data_provider.py.role_backup` - ORPHANED - Legacy backup, likely renamed to data_owner
- `/app/models/data_profiling.py` - ACTIVELY USED - Data profiling models
- `/app/models/data_dictionary.py` - ACTIVELY USED - Data dictionary models
- `/app/models/document.py` - ACTIVELY USED - Document models
- `/app/models/lob.py` - ACTIVELY USED - Line of Business models
- `/app/models/lob.py.role_backup` - ORPHANED - Backup file, should be deleted

#### System Models
- `/app/models/rbac.py` - ACTIVELY USED - RBAC models
- `/app/models/rbac_resource.py` - ACTIVELY USED - RBAC resource models
- `/app/models/sla.py` - ACTIVELY USED - SLA models
- `/app/models/sla.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/models/metrics.py` - ACTIVELY USED - Metrics models
- `/app/models/versioned_models.py` - ACTIVELY USED - Versioning support models
- `/app/models/versioning.py` - ACTIVELY USED - Versioning models

**CLEANUP NEEDED**: Multiple `.role_backup` files should be removed.

---

### Schemas Layer (/app/schemas/)

Pydantic schema definitions for API request/response validation.

#### Core Schemas
- `/app/schemas/__init__.py` - ACTIVELY USED - Package init
- `/app/schemas/auth.py` - ACTIVELY USED - Authentication schemas
- `/app/schemas/user.py` - ACTIVELY USED - User schemas
- `/app/schemas/report.py` - ACTIVELY USED - Report schemas

#### Workflow Phase Schemas
- `/app/schemas/planning.py` - ACTIVELY USED - Planning phase schemas
- `/app/schemas/scoping.py` - ACTIVELY USED - Scoping phase schemas
- `/app/schemas/sample_selection.py` - ACTIVELY USED - Sample selection schemas
- `/app/schemas/sample_individual.py` - ACTIVELY USED - Individual sample schemas
- `/app/schemas/request_info.py` - ACTIVELY USED - Request info schemas
- `/app/schemas/request_info.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/schemas/test_execution.py` - ACTIVELY USED - Test execution schemas
- `/app/schemas/testing_execution.py.backup` - ORPHANED - Backup file, should be deleted

#### System & Management Schemas
- `/app/schemas/observation.py` - ACTIVELY USED - Observation schemas
- `/app/schemas/observation_enhanced.py` - ACTIVELY USED - Enhanced observation schemas
- `/app/schemas/observation_management.py` - ACTIVELY USED - Observation management schemas
- `/app/schemas/workflow_phase.py` - ACTIVELY USED - Workflow phase schemas
- `/app/schemas/activity.py` - ACTIVELY USED - Activity schemas
- `/app/schemas/activity_states.py` - ACTIVELY USED - Activity state schemas

#### Data & Configuration Schemas
- `/app/schemas/data_owner.py` - ACTIVELY USED - Data owner schemas
- `/app/schemas/data_provider.py.role_backup` - ORPHANED - Legacy backup
- `/app/schemas/data_source.py` - ACTIVELY USED - Data source schemas
- `/app/schemas/data_dictionary.py` - ACTIVELY USED - Data dictionary schemas
- `/app/schemas/lob.py` - ACTIVELY USED - Line of Business schemas

#### System Management Schemas
- `/app/schemas/rbac.py` - ACTIVELY USED - RBAC schemas
- `/app/schemas/sla.py` - ACTIVELY USED - SLA schemas
- `/app/schemas/sla.py.role_backup` - ORPHANED - Backup file, should be deleted
- `/app/schemas/cycle.py` - ACTIVELY USED - Cycle schemas
- `/app/schemas/versioning.py` - ACTIVELY USED - Versioning schemas

**CLEANUP NEEDED**: Remove backup files.

---

### Services Layer (/app/services/)

Business logic and service implementations.

#### Core Services
- `/app/services/llm_service.py` - ACTIVELY USED - Core LLM integration service
- `/app/services/llm_service.py.backup` - ORPHANED - Backup file, should be deleted
- `/app/services/llm_service_v2.py` - VERSION 2 - Consolidation candidate with v1
- `/app/services/workflow_orchestrator.py` - ACTIVELY USED - Core workflow orchestration
- `/app/services/workflow_orchestrator.py.role_backup` - ORPHANED - Backup file
- `/app/services/workflow_service.py` - ACTIVELY USED - Workflow services

#### Dashboard Services
- `/app/services/cdo_dashboard_service.py` - ACTIVELY USED - CDO dashboard service
- `/app/services/cdo_dashboard_service.py.role_backup` - ORPHANED - Backup file
- `/app/services/data_owner_dashboard_service.py` - ACTIVELY USED - Data owner dashboard
- `/app/services/data_provider_dashboard_service.py` - LEGACY - May be renamed to data_owner
- `/app/services/executive_dashboard_service.py` - ACTIVELY USED - Executive dashboard

#### Metrics Services
- `/app/services/metrics_service.py` - ACTIVELY USED - Core metrics service
- `/app/services/metrics_service.py.role_backup` - ORPHANED - Backup file
- `/app/services/metrics_service_v2.py` - VERSION 2 - Consolidation candidate
- `/app/services/workflow_metrics_service.py` - ACTIVELY USED - Workflow-specific metrics

**Metrics Calculator Hierarchy (/app/services/metrics/):**
- `/app/services/metrics/__init__.py` - Package init
- `/app/services/metrics/base_metrics_calculator.py` - Base calculator class
- `/app/services/metrics/data_executive_metrics_calculator.py` - Data executive metrics
- `/app/services/metrics/data_provider_metrics_calculator.py` - Data provider metrics
- `/app/services/metrics/report_owner_metrics_calculator.py` - Report owner metrics
- `/app/services/metrics/test_executive_metrics_calculator.py` - Test executive metrics
- `/app/services/metrics/tester_metrics_calculator.py` - Tester metrics

#### Phase-Specific Services
- `/app/services/request_info_service.py` - ACTIVELY USED - Request info service
- `/app/services/request_info_service.py.role_backup` - ORPHANED - Backup file
- `/app/services/data_source_service.py` - ACTIVELY USED - Data source service
- `/app/services/sample_set_versioning_service.py` - ACTIVELY USED - Sample versioning
- `/app/services/attribute_versioning_service.py` - ACTIVELY USED - Attribute versioning

#### System Services
- `/app/services/email_service.py` - ACTIVELY USED - Email service
- `/app/services/email_service.py.role_backup` - ORPHANED - Backup file
- `/app/services/sla_service.py` - ACTIVELY USED - SLA service
- `/app/services/sla_service.py.role_backup` - ORPHANED - Backup file
- `/app/services/sla_escalation_email_service.py` - ACTIVELY USED - SLA escalation emails
- `/app/services/sla_escalation_email_service.py.role_backup` - ORPHANED - Backup file
- `/app/services/security_service.py` - ACTIVELY USED - Security service
- `/app/services/permission_service.py` - ACTIVELY USED - Permission service
- `/app/services/rbac_restrictions.py` - ACTIVELY USED - RBAC restrictions
- `/app/services/rbac_restrictions.py.role_backup` - ORPHANED - Backup file

#### Utility Services
- `/app/services/activity_state_manager.py` - ACTIVELY USED - Activity state management
- `/app/services/audit_database_service.py` - ACTIVELY USED - Audit database service
- `/app/services/backup_service.py` - ACTIVELY USED - Backup service
- `/app/services/batch_processor.py` - ACTIVELY USED - Batch processing
- `/app/services/cache_service.py` - ACTIVELY USED - Caching service
- `/app/services/multi_database_service.py` - ACTIVELY USED - Multi-database support
- `/app/services/temporal_service.py` - ACTIVELY USED - Temporal workflow service
- `/app/services/test_report_service.py` - ACTIVELY USED - Test report service

#### Benchmarking Services
- `/app/services/benchmarking_service.py` - ACTIVELY USED - Benchmarking service
- `/app/services/benchmarking_service_refactored.py` - REFACTORED VERSION - Consolidation candidate

**MAJOR CLEANUP NEEDED**: Many backup files need removal, and version consolidation is needed.

---

### Tasks Layer (/app/tasks/)

Background task definitions.

#### `/app/tasks/__init__.py`
- **Purpose**: Tasks package initialization
- **Status**: ACTIVELY USED - Required for Python module structure
- **Consolidation**: Cannot be consolidated
- **Naming**: CORRECT

#### `/app/tasks/llm_tasks.py`
- **Purpose**: LLM-related background tasks
- **Status**: ACTIVELY USED - LLM processing tasks
- **Consolidation**: Cannot be consolidated - Specialized functionality
- **Naming**: CORRECT

#### `/app/tasks/optimized_tasks.py`
- **Purpose**: Optimized versions of background tasks
- **Status**: ACTIVELY USED - Performance-optimized tasks
- **Consolidation**: May be consolidated with other task files
- **Naming**: VAGUE - Should be more specific about optimization type

---

### Templates Layer (/app/templates/)

Email and notification templates.

#### `/app/templates/emails/`
- `/app/templates/emails/data_owner_assignment.txt` - ACTIVELY USED - Data owner assignment email
- `/app/templates/emails/report_approve.txt` - ACTIVELY USED - Report approval email
- `/app/templates/emails/report_reject.txt` - ACTIVELY USED - Report rejection email
- `/app/templates/emails/rfi_request.html` - ACTIVELY USED - RFI request HTML email
- `/app/templates/emails/rfi_request.txt` - ACTIVELY USED - RFI request text email

All template files are actively used and appropriately named.

---

### Temporal Layer (/app/temporal/)

Temporal workflow engine integration.

#### Core Temporal Files
- `/app/temporal/__init__.py` - ACTIVELY USED - Package init
- `/app/temporal/client.py` - ACTIVELY USED - Temporal client configuration
- `/app/temporal/retry_policies.py` - ACTIVELY USED - Retry policy definitions
- `/app/temporal/worker.py` - ACTIVELY USED - Temporal worker
- `/app/temporal/worker_reconciled.py` - RECONCILED VERSION - Consolidation candidate
- `/app/temporal/workflow_versioning.py` - ACTIVELY USED - Workflow versioning
- `/app/temporal/workflows.py` - ACTIVELY USED - Workflow definitions

#### Shared Components (/app/temporal/shared/)
- `/app/temporal/shared/__init__.py` - Package init
- `/app/temporal/shared/constants.py` - Shared constants
- `/app/temporal/shared/types.py` - Shared type definitions

#### Activities (/app/temporal/activities/)
Temporal activity definitions organized by domain:

**Core Activities:**
- `/app/temporal/activities/__init__.py` - Package init
- `/app/temporal/activities/llm_activities.py` - LLM processing activities
- `/app/temporal/activities/notification_activities.py` - Notification activities
- `/app/temporal/activities/phase_activities.py` - Phase management activities
- `/app/temporal/activities/tracking_activities.py` - Tracking activities

**Phase-Specific Activities:**
- `/app/temporal/activities/data_owner_activities.py` - Data owner activities
- `/app/temporal/activities/data_provider_activities_reconciled.py` - Data provider activities
- `/app/temporal/activities/planning_activities.py` - Planning phase activities
- `/app/temporal/activities/planning_activities_reconciled.py` - Reconciled planning activities
- `/app/temporal/activities/planning_activities_wrapper.py` - Planning wrapper activities
- `/app/temporal/activities/scoping_activities.py` - Scoping activities
- `/app/temporal/activities/scoping_activities_reconciled.py` - Reconciled scoping activities
- `/app/temporal/activities/scoping_activities_wrapper.py` - Scoping wrapper activities
- `/app/temporal/activities/sample_selection_activities.py` - Sample selection activities
- `/app/temporal/activities/sample_selection_activities_reconciled.py` - Reconciled sample selection
- `/app/temporal/activities/sample_selection_activities_wrapper.py` - Sample selection wrapper
- `/app/temporal/activities/request_info_activities.py` - Request info activities
- `/app/temporal/activities/request_info_activities_reconciled.py` - Reconciled request info
- `/app/temporal/activities/test_activities.py` - Test activities
- `/app/temporal/activities/test_execution_activities.py` - Test execution activities
- `/app/temporal/activities/test_execution_activities_reconciled.py` - Reconciled test execution
- `/app/temporal/activities/observation_activities.py` - Observation activities
- `/app/temporal/activities/observation_activities_reconciled.py` - Reconciled observation
- `/app/temporal/activities/finalize_report_activities.py` - Report finalization activities
- `/app/temporal/activities/test_report_activities_reconciled.py` - Test report activities

#### Workflows (/app/temporal/workflows/)
- `/app/temporal/workflows/__init__.py` - Package init
- `/app/temporal/workflows/enhanced_test_cycle_workflow.py` - Enhanced test cycle workflow
- `/app/temporal/workflows/llm_analysis_workflow.py` - LLM analysis workflow
- `/app/temporal/workflows/report_testing_workflow.py` - Report testing workflow
- `/app/temporal/workflows/test_cycle_workflow.py` - Basic test cycle workflow
- `/app/temporal/workflows/test_cycle_workflow_reconciled.py` - Reconciled test cycle workflow
- `/app/temporal/workflows/test_cycle_workflow_reconciled.py.backup` - ORPHANED - Backup file
- `/app/temporal/workflows/test_cycle_workflow_simple.py` - Simplified test cycle workflow

**CONSOLIDATION OPPORTUNITY**: Multiple versions of similar workflows and activities suggest consolidation is needed.

---

### Utils Layer (/app/utils/)

#### `/app/utils/data_dictionary_loader.py`
- **Purpose**: Utility for loading data dictionary files
- **Status**: ACTIVELY USED - Data dictionary management
- **Consolidation**: Cannot be consolidated - Specialized utility
- **Naming**: CORRECT

---

## MAJOR FINDINGS & RECOMMENDATIONS

### 1. Backup File Proliferation
**CRITICAL CLEANUP NEEDED**: The project contains numerous `.backup`, `.role_backup`, and `.bak` files that should be removed from version control:
- 20+ backup files across models, core, services, and other directories
- These files create confusion and bloat the repository
- Version control already provides backup functionality

### 2. Duplicate "Clean" Files
**CONSOLIDATION REQUIRED**: Many endpoints have both regular and `_clean.py` versions:
- All endpoint files in `/app/api/v1/endpoints/` have `_clean.py` counterparts
- This suggests a refactoring that was never completed
- Decision needed: keep clean versions and remove originals, or vice versa

### 3. Version Fragmentation
**VERSION MANAGEMENT ISSUE**: Multiple versioned files suggest incomplete migrations:
- `llm_service.py` vs `llm_service_v2.py`
- `metrics_service.py` vs `metrics_service_v2.py`
- `metrics.py` vs `metrics_simple.py` vs `metrics_v2.py`
- Multiple workflow versions in temporal layer

### 4. Naming Inconsistencies
**STANDARDIZATION NEEDED**:
- `testing_execution.py` should be `test_execution.py` (used elsewhere)
- `request_for_information.py` should be `request_info.py` (standard elsewhere)
- `crud_report.py` should be `report.py` (following CRUD layer convention)

### 5. Legacy DTO Structure
**ARCHITECTURAL CLEANUP**: Two DTO directories exist:
- `/app/application/dto/` (legacy)
- `/app/application/dtos/` (current)
- Legacy directory should be removed after migration verification

### 6. Temporal Layer Complexity
**OVER-ENGINEERING CONCERN**: The temporal layer shows signs of over-engineering:
- Multiple reconciled versions of the same activities
- Wrapper activities that may not be necessary
- Multiple workflow implementations for similar functionality

### 7. Infrastructure Pattern Adoption
**POSITIVE FINDING**: The project shows good adoption of clean architecture patterns:
- Proper separation of concerns with domain, application, and infrastructure layers
- Good use of dependency injection
- Proper interface definitions

---

## NEXT STEPS RECOMMENDATION

1. **Immediate Cleanup** (High Priority):
   - Remove all `.backup`, `.role_backup`, and similar files
   - Consolidate `_clean.py` files with their counterparts
   - Standardize naming conventions

2. **Version Consolidation** (Medium Priority):
   - Decide on final versions for services and consolidate
   - Remove outdated temporal workflow versions
   - Consolidate metrics implementations

3. **Architectural Review** (Medium Priority):
   - Remove legacy DTO directory after verification
   - Review temporal layer for over-engineering
   - Standardize naming conventions across all layers

4. **Documentation** (Low Priority):
   - Document the final architectural decisions
   - Create coding standards document
   - Update CLAUDE.md with final structure

This audit reveals a project with good architectural foundations but significant cleanup opportunities. The core functionality appears solid, but maintenance burden is high due to file proliferation and versioning issues.

---

*This completes the backend (/app directory) analysis. Continuing with frontend analysis...*

---

## FRONTEND FILES (/frontend directory)

### Root Frontend Files

#### Configuration Files
- `/frontend/package.json` - ACTIVELY USED - NPM package configuration and dependencies
- `/frontend/package-lock.json` - ACTIVELY USED - NPM lock file for reproducible builds
- `/frontend/tsconfig.json` - ACTIVELY USED - TypeScript configuration
- `/frontend/playwright.config.ts` - ACTIVELY USED - Playwright E2E test configuration

#### Build & Development Files
- `/frontend/README.md` - ACTIVELY USED - Frontend documentation
- `/frontend/build/` - BUILD OUTPUT - Generated build artifacts directory
- `/frontend/node_modules/` - DEPENDENCIES - NPM dependencies (ignored in git)
- `/frontend/restart_frontend.sh` - ACTIVELY USED - Frontend restart script

#### Log & Process Files
- `/frontend/backend.log` - LOG FILE - Should not be in repository
- `/frontend/frontend.log` - LOG FILE - Should not be in repository
- `/frontend/frontend.pid` - PROCESS FILE - Should not be in repository

#### Debug & Screenshot Files
- `/frontend/check_new_theme.py` - DEBUG SCRIPT - Temporary debugging file
- `/frontend/dashboard-debug.png` - DEBUG SCREENSHOT - Temporary debugging file
- `/frontend/login-error-debug.png` - DEBUG SCREENSHOT - Temporary debugging file
- `/frontend/screenshots/` - DEBUG DIRECTORY - Debug screenshots directory
- `/frontend/test-results/` - TEST RESULTS - Test output directory
- `/frontend/test_results/` - DUPLICATE TEST RESULTS - Duplicate test results directory

#### Upload Directory
- `/frontend/uploads/` - UPLOAD STORAGE - File upload storage directory

#### Utility Scripts
- `/frontend/util/` - UTILITY SCRIPTS - Data dictionary processing utilities
  - Contains Python scripts for regulatory data processing
  - Multiple versions of similar functionality (RegDD14M.py, RegDD14M2_Final.py, etc.)

**CLEANUP NEEDED**: Log files, PID files, and debug screenshots should not be in version control.

---

### Public Assets (/frontend/public/)

#### Static Assets
- `/frontend/public/index.html` - ACTIVELY USED - Main HTML template
- `/frontend/public/favicon.ico` - ACTIVELY USED - Browser favicon
- `/frontend/public/logo192.png` - ACTIVELY USED - App logo (192px)
- `/frontend/public/logo512.png` - ACTIVELY USED - App logo (512px)
- `/frontend/public/manifest.json` - ACTIVELY USED - PWA manifest
- `/frontend/public/robots.txt` - ACTIVELY USED - Search engine robots file

All public assets are actively used and properly named.

---

### Source Code (/frontend/src/)

#### Root Source Files
- `/frontend/src/index.tsx` - ACTIVELY USED - React application entry point
- `/frontend/src/App.tsx` - ACTIVELY USED - Main application component
- `/frontend/src/App.tsx.role_backup` - ORPHANED - Backup file, should be deleted
- `/frontend/src/App.test.tsx` - ACTIVELY USED - App component tests
- `/frontend/src/App.css` - ACTIVELY USED - App component styles
- `/frontend/src/index.css` - ACTIVELY USED - Global styles
- `/frontend/src/logo.svg` - ACTIVELY USED - React logo
- `/frontend/src/react-app-env.d.ts` - ACTIVELY USED - React TypeScript definitions
- `/frontend/src/reportWebVitals.ts` - ACTIVELY USED - Performance monitoring
- `/frontend/src/setupTests.ts` - ACTIVELY USED - Jest test setup
- `/frontend/src/setupProxy.js` - ACTIVELY USED - Development proxy configuration

#### Theme & Styling
- `/frontend/src/theme.ts` - ACTIVELY USED - Material-UI theme configuration
- `/frontend/src/theme-enhanced.ts` - ENHANCED VERSION - Consolidation candidate with theme.ts
- `/frontend/src/styles/design-system.ts` - ACTIVELY USED - Design system definitions

#### Shell Scripts
- `/frontend/src/fix-grid-legacy.sh` - UTILITY SCRIPT - Grid component fix script

---

### API Layer (/frontend/src/api/)

#### Core API Files
- `/frontend/src/api/client.ts` - ACTIVELY USED - HTTP client configuration
- `/frontend/src/api/api.ts` - ACTIVELY USED - Core API functions
- `/frontend/src/api/auth.ts` - ACTIVELY USED - Authentication API
- `/frontend/src/api/mockData.ts` - ACTIVELY USED - Mock data for development
- `/frontend/src/api/mockInterceptor.ts` - ACTIVELY USED - Mock API interceptor

#### Domain-Specific API Files
- `/frontend/src/api/cycles.ts` - ACTIVELY USED - Test cycles API
- `/frontend/src/api/reports.ts` - ACTIVELY USED - Reports API
- `/frontend/src/api/users.ts` - ACTIVELY USED - Users API
- `/frontend/src/api/workflow.ts` - ACTIVELY USED - Workflow API
- `/frontend/src/api/planning.ts` - ACTIVELY USED - Planning phase API
- `/frontend/src/api/dataProfiling.ts` - ACTIVELY USED - Data profiling API
- `/frontend/src/api/dataDictionary.ts` - ACTIVELY USED - Data dictionary API
- `/frontend/src/api/lobs.ts` - ACTIVELY USED - Line of Business API
- `/frontend/src/api/metrics.ts` - ACTIVELY USED - Metrics API
- `/frontend/src/api/rbac.ts` - ACTIVELY USED - RBAC API

All API files are actively used and follow consistent naming conventions.

---

### Component Architecture (/frontend/src/components/)

#### Root Level Components
- `/frontend/src/components/LLMProgressModal.tsx` - ACTIVELY USED - LLM progress modal
- `/frontend/src/components/PhaseStepperCard.tsx` - ACTIVELY USED - Phase stepper component
- `/frontend/src/components/WorkflowProgress.tsx` - ACTIVELY USED - Workflow progress component
- `/frontend/src/components/WorkflowProgress.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/components/WorkflowProgressEnhanced.tsx` - ENHANCED VERSION - Consolidation candidate
- `/frontend/src/components/WorkflowVisualization.tsx` - ACTIVELY USED - Workflow visualization

#### Analytics Components (/frontend/src/components/analytics/)
- `/frontend/src/components/analytics/AnalyticsDashboard.tsx` - ACTIVELY USED - Analytics dashboard
- `/frontend/src/components/analytics/AdvancedAnalyticsDashboard.tsx` - ACTIVELY USED - Advanced analytics
- `/frontend/src/components/analytics/AdvancedAnalyticsDashboard.tsx.role_backup` - ORPHANED - Backup file

#### Authentication Components (/frontend/src/components/auth/)
- `/frontend/src/components/auth/PermissionGate.tsx` - ACTIVELY USED - Permission-based rendering
- `/frontend/src/components/auth/ProtectedRoute.tsx` - ACTIVELY USED - Route protection

#### Common Components (/frontend/src/components/common/)
- `/frontend/src/components/common/ErrorBoundary.tsx` - ACTIVELY USED - Error boundary component
- `/frontend/src/components/common/ErrorDisplays.tsx` - ACTIVELY USED - Error display components
- `/frontend/src/components/common/GlobalSearch.tsx` - ACTIVELY USED - Global search component
- `/frontend/src/components/common/Layout.tsx` - ACTIVELY USED - Layout component
- `/frontend/src/components/common/Layout.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/components/common/LazyComponent.tsx` - ACTIVELY USED - Lazy loading component
- `/frontend/src/components/common/LoadingStates.tsx` - ACTIVELY USED - Loading state components
- `/frontend/src/components/common/MockDataToggle.tsx` - ACTIVELY USED - Mock data toggle

**Activity & State Management:**
- `/frontend/src/components/common/ActivityStateBadge.tsx` - ACTIVELY USED - Activity state badge
- `/frontend/src/components/common/ActivityStateManager.tsx` - ACTIVELY USED - Activity state manager
- `/frontend/src/components/common/BatchProgressIndicator.tsx` - ACTIVELY USED - Batch progress indicator
- `/frontend/src/components/common/PhaseStatusIndicator.tsx` - ACTIVELY USED - Phase status indicator

**Versioning Components:**
- `/frontend/src/components/common/PhaseVersioningSection.tsx` - ACTIVELY USED - Phase versioning UI
- `/frontend/src/components/common/VersionApprovalButtons.tsx` - ACTIVELY USED - Version approval buttons
- `/frontend/src/components/common/VersionComparisonDialog.tsx` - ACTIVELY USED - Version comparison dialog
- `/frontend/src/components/common/VersionHistoryViewer.tsx` - ACTIVELY USED - Version history viewer
- `/frontend/src/components/common/VersionSelector.tsx` - ACTIVELY USED - Version selector
- `/frontend/src/components/common/WorkflowHeader.tsx` - ACTIVELY USED - Workflow header component
- `/frontend/src/components/common/VERSIONING_GUIDE.md` - DOCUMENTATION - Versioning implementation guide

#### Dashboard Components (/frontend/src/components/dashboards/)
- `/frontend/src/components/dashboards/RoleDashboardRouter.tsx` - ACTIVELY USED - Role-based dashboard routing

#### Layout Components (/frontend/src/components/layout/)
- `/frontend/src/components/layout/Layout.tsx` - ACTIVELY USED - Main layout component
- `/frontend/src/components/layout/Sidebar.tsx` - ACTIVELY USED - Sidebar component
- `/frontend/src/components/layout/Sidebar.tsx.role_backup` - ORPHANED - Backup file

#### Metrics Components (/frontend/src/components/metrics/)
- `/frontend/src/components/metrics/index.ts` - ACTIVELY USED - Metrics component exports
- `/frontend/src/components/metrics/MetricBox.tsx` - ACTIVELY USED - Individual metric box
- `/frontend/src/components/metrics/MetricsGrid.tsx` - ACTIVELY USED - Metrics grid layout
- `/frontend/src/components/metrics/MetricsRow.tsx` - ACTIVELY USED - Metrics row layout
- `/frontend/src/components/metrics/PhaseMetrics.tsx` - ACTIVELY USED - General phase metrics
- `/frontend/src/components/metrics/PhaseMetricsCard.tsx` - ACTIVELY USED - Phase metrics card
- `/frontend/src/components/metrics/PhaseMetricsExample.tsx` - ACTIVELY USED - Example metrics

**Phase-Specific Metrics:**
- `/frontend/src/components/metrics/DataProfilingPhaseMetrics.tsx` - ACTIVELY USED - Data profiling metrics
- `/frontend/src/components/metrics/DataProviderPhaseMetrics.tsx` - ACTIVELY USED - Data provider metrics
- `/frontend/src/components/metrics/ObservationManagementPhaseMetrics.tsx` - ACTIVELY USED - Observation mgmt metrics
- `/frontend/src/components/metrics/ObservationPhaseMetrics.tsx` - ACTIVELY USED - Observation metrics
- `/frontend/src/components/metrics/PlanningPhaseMetrics.tsx` - ACTIVELY USED - Planning metrics
- `/frontend/src/components/metrics/RequestInfoPhaseMetrics.tsx` - ACTIVELY USED - Request info metrics
- `/frontend/src/components/metrics/SampleSelectionPhaseMetrics.tsx` - ACTIVELY USED - Sample selection metrics
- `/frontend/src/components/metrics/ScopingPhaseMetrics.tsx` - ACTIVELY USED - Scoping metrics
- `/frontend/src/components/metrics/TestExecutionPhaseMetrics.tsx` - ACTIVELY USED - Test execution metrics

#### Navigation Components (/frontend/src/components/navigation/)
- `/frontend/src/components/navigation/RoleBasedNavigation.tsx` - ACTIVELY USED - Role-based navigation
- `/frontend/src/components/navigation/RoleBasedNavigation.tsx.role_backup` - ORPHANED - Backup file

#### Notification Components (/frontend/src/components/notifications/)
- `/frontend/src/components/notifications/UnifiedNotificationCenter.tsx` - ACTIVELY USED - Notification center

#### Report Components (/frontend/src/components/reports/)
- `/frontend/src/components/reports/ReportTestingSummary.tsx` - ACTIVELY USED - Report testing summary

#### Scoping Components (/frontend/src/components/scoping/)
- `/frontend/src/components/scoping/ScopingDecisionSummary.tsx` - ACTIVELY USED - Scoping decision summary
- `/frontend/src/components/scoping/ScopingDecisionToggle.tsx` - ACTIVELY USED - Scoping decision toggle
- `/frontend/src/components/scoping/ScopingSubmissionDialog.tsx` - ACTIVELY USED - Scoping submission dialog

#### Workflow Components (/frontend/src/components/workflow/)
- `/frontend/src/components/workflow/WorkflowVisualization.tsx` - ACTIVELY USED - Workflow visualization

---

### Context Providers (/frontend/src/contexts/)

#### Core Contexts
- `/frontend/src/contexts/AuthContext.tsx` - ACTIVELY USED - Authentication context
- `/frontend/src/contexts/NotificationContext.tsx` - ACTIVELY USED - Notification context
- `/frontend/src/contexts/NotificationContext.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/contexts/PermissionContext.tsx` - ACTIVELY USED - Permission context
- `/frontend/src/contexts/PermissionContext.tsx.role_backup` - ORPHANED - Backup file

---

### Custom Hooks (/frontend/src/hooks/)

#### Hook Definitions
- `/frontend/src/hooks/useApiCache.ts` - ACTIVELY USED - API caching hook
- `/frontend/src/hooks/usePhaseSteps.ts` - ACTIVELY USED - Phase steps hook
- `/frontend/src/hooks/useTemporalWorkflow.ts` - ACTIVELY USED - Temporal workflow hook

---

### Pages (/frontend/src/pages/)

#### Root Level Pages
- `/frontend/src/pages/LoginPage.tsx` - ACTIVELY USED - Login page
- `/frontend/src/pages/DashboardPage.tsx` - ACTIVELY USED - Main dashboard page
- `/frontend/src/pages/TestCyclesPage.tsx` - ACTIVELY USED - Test cycles listing page
- `/frontend/src/pages/TestCyclesPage.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/ReportsPage.tsx` - ACTIVELY USED - Reports listing page
- `/frontend/src/pages/UsersPage.tsx` - ACTIVELY USED - Users management page
- `/frontend/src/pages/UsersPage.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/AnalyticsPage.tsx` - ACTIVELY USED - Analytics page
- `/frontend/src/pages/WorkflowMonitoringDashboard.tsx` - ACTIVELY USED - Workflow monitoring

#### Cycle & Report Pages
- `/frontend/src/pages/CycleDetailPage.tsx` - ACTIVELY USED - Cycle detail page
- `/frontend/src/pages/CycleDetailPage.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/CycleDetailPageFixed.tsx` - FIXED VERSION - Consolidation candidate
- `/frontend/src/pages/ReportTestingPage.tsx` - ACTIVELY USED - Report testing page
- `/frontend/src/pages/ReportTestingPageRedesigned.tsx` - REDESIGNED VERSION - Consolidation candidate

#### Admin Pages (/frontend/src/pages/admin/)
- `/frontend/src/pages/admin/DataSourcesPage.tsx` - ACTIVELY USED - Data sources admin
- `/frontend/src/pages/admin/LOBManagementPage.tsx` - ACTIVELY USED - LOB management
- `/frontend/src/pages/admin/RBACManagementPage.tsx` - ACTIVELY USED - RBAC management
- `/frontend/src/pages/admin/ReportManagementPage.tsx` - ACTIVELY USED - Report management
- `/frontend/src/pages/admin/SLAConfigurationPage.tsx` - ACTIVELY USED - SLA configuration
- `/frontend/src/pages/admin/SLAConfigurationPage.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/admin/SystemSettingsPage.tsx` - ACTIVELY USED - System settings
- `/frontend/src/pages/admin/UserManagementPage.tsx` - ACTIVELY USED - User management

#### Dashboard Pages (/frontend/src/pages/dashboards/)
- `/frontend/src/pages/dashboards/DataExecutiveDashboard.tsx` - ACTIVELY USED - Data executive dashboard
- `/frontend/src/pages/dashboards/DataOwnerDashboard.tsx` - ACTIVELY USED - Data owner dashboard
- `/frontend/src/pages/dashboards/DataProviderDashboard.tsx` - ACTIVELY USED - Data provider dashboard
- `/frontend/src/pages/dashboards/DataProviderDashboard.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/dashboards/ReportOwnerDashboard.tsx` - ACTIVELY USED - Report owner dashboard
- `/frontend/src/pages/dashboards/TestExecutiveDashboard.tsx` - ACTIVELY USED - Test executive dashboard
- `/frontend/src/pages/dashboards/TestExecutiveDashboardEnhanced.tsx` - ENHANCED VERSION - Consolidation candidate
- `/frontend/src/pages/dashboards/TesterDashboard.tsx` - ACTIVELY USED - Tester dashboard

**Orphaned Dashboard Files:**
- `/frontend/src/pages/dashboards/CDODashboard.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/dashboards/TestManagerDashboard.tsx.role_backup` - ORPHANED - Backup file

#### Phase Pages (/frontend/src/pages/phases/)

**Active Phase Pages:**
- `/frontend/src/pages/phases/DataOwnerPage.tsx` - ACTIVELY USED - Data owner phase page
- `/frontend/src/pages/phases/DataProfilingPage.tsx` - ACTIVELY USED - Data profiling phase
- `/frontend/src/pages/phases/NewRequestInfoPage.tsx` - ACTIVELY USED - Request info phase
- `/frontend/src/pages/phases/ObservationManagementEnhanced.tsx` - ACTIVELY USED - Observation management
- `/frontend/src/pages/phases/ObservationManagementPage.tsx` - ACTIVELY USED - Observation management (basic)
- `/frontend/src/pages/phases/SampleReviewPage.tsx` - ACTIVELY USED - Sample review phase
- `/frontend/src/pages/phases/SampleSelectionIndividual.tsx` - ACTIVELY USED - Individual sample selection
- `/frontend/src/pages/phases/SampleSelectionPage.tsx` - ACTIVELY USED - Sample selection phase
- `/frontend/src/pages/phases/ScopingPage.tsx` - ACTIVELY USED - Scoping phase
- `/frontend/src/pages/phases/SimplifiedPlanningPage.tsx` - ACTIVELY USED - Planning phase
- `/frontend/src/pages/phases/TestExecutionPage.tsx` - ACTIVELY USED - Test execution phase
- `/frontend/src/pages/phases/TestReportPage.tsx` - ACTIVELY USED - Test report phase
- `/frontend/src/pages/phases/TestingReportPage.tsx` - NAMING INCONSISTENCY - Should be TestReportPage
- `/frontend/src/pages/phases/ReportOwnerScopingReview.tsx` - ACTIVELY USED - Report owner scoping review

**Assignment Interface Pages:**
- `/frontend/src/pages/phases/DataExecutiveAssignmentInterface.tsx` - ACTIVELY USED - Data executive assignments
- `/frontend/src/pages/phases/DataExecutiveAssignmentsPage.tsx` - ACTIVELY USED - Data executive assignments page

**Backup/Legacy Files:**
- `/frontend/src/pages/phases/CDOAssignmentInterface.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/phases/CDOAssignmentsPage.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/phases/DataProviderPage.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/phases/NewRequestInfoPage.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/phases/RequestInfoPage.tsx.backup` - ORPHANED - Backup file
- `/frontend/src/pages/phases/SampleSelectionPage.tsx.backup` - ORPHANED - Backup file
- `/frontend/src/pages/phases/SampleSelectionPage.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/phases/TestExecutionPage.tsx.role_backup` - ORPHANED - Backup file
- `/frontend/src/pages/phases/TestingExecutionPage.tsx.backup` - ORPHANED - Backup file

---

### Type Definitions (/frontend/src/types/)

#### Type Files
- `/frontend/src/types/api.ts` - ACTIVELY USED - API type definitions
- `/frontend/src/types/api.ts.role_backup` - ORPHANED - Backup file

---

### Utilities (/frontend/src/utils/)

#### Utility Files
- `/frontend/src/utils/temporalWorkflowSteps.ts` - ACTIVELY USED - Temporal workflow utilities

---

### E2E Testing (/frontend/e2e/)

#### Core E2E Files
- `/frontend/e2e/playwright.config.ts` - ACTIVELY USED - Playwright configuration
- `/frontend/e2e/global-setup.ts` - ACTIVELY USED - Global test setup
- `/frontend/e2e/global-teardown.ts` - ACTIVELY USED - Global test teardown
- `/frontend/e2e/test-utils.ts` - ACTIVELY USED - Test utilities

#### Test Specifications
- `/frontend/e2e/auth.spec.ts` - ACTIVELY USED - Authentication tests
- `/frontend/e2e/dashboard.spec.ts` - ACTIVELY USED - Dashboard tests
- `/frontend/e2e/complete-workflow.spec.ts` - ACTIVELY USED - Complete workflow tests
- `/frontend/e2e/role-based-testing.spec.ts` - ACTIVELY USED - Role-based tests
- `/frontend/e2e/llm-integration.spec.ts` - ACTIVELY USED - LLM integration tests
- `/frontend/e2e/accessibility.spec.ts` - ACTIVELY USED - Accessibility tests
- `/frontend/e2e/performance.spec.ts` - ACTIVELY USED - Performance tests
- `/frontend/e2e/simple-dashboard-validation.spec.ts` - ACTIVELY USED - Simple dashboard validation
- `/frontend/e2e/debug-auth.spec.ts` - DEBUG TEST - Temporary debugging test

#### E2E Documentation
- `/frontend/e2e/README.md` - ACTIVELY USED - E2E testing documentation
- `/frontend/e2e/IMPROVEMENTS_SUMMARY.md` - DOCUMENTATION - Test improvements summary
- `/frontend/e2e/TEST_IMPROVEMENTS_GUIDE.md` - DOCUMENTATION - Test improvements guide
- `/frontend/e2e/test-summary.md` - DOCUMENTATION - Test summary

#### Test Reports
- `/frontend/playwright-report/index.html` - TEST REPORT - Generated test report

---

## FRONTEND ANALYSIS FINDINGS

### 1. Backup File Proliferation (Critical)
**MAJOR CLEANUP NEEDED**: The frontend has extensive backup file contamination:
- 15+ `.role_backup` files across components, pages, and contexts
- Multiple `.backup` files in phases and other directories
- These files create confusion and repository bloat

### 2. Version/Enhancement Duplicates (High Priority)
**CONSOLIDATION REQUIRED**: Multiple enhanced/improved versions of components:
- `WorkflowProgress.tsx` vs `WorkflowProgressEnhanced.tsx`
- `TestExecutiveDashboard.tsx` vs `TestExecutiveDashboardEnhanced.tsx`
- `CycleDetailPage.tsx` vs `CycleDetailPageFixed.tsx`
- `ReportTestingPage.tsx` vs `ReportTestingPageRedesigned.tsx`
- `theme.ts` vs `theme-enhanced.ts`

### 3. Naming Inconsistencies (Medium Priority)
**STANDARDIZATION NEEDED**:
- `TestingReportPage.tsx` should be `TestReportPage.tsx` (consistent with backend)
- Duplicate test result directories: `test-results/` and `test_results/`

### 4. Log Files in Repository (High Priority)
**IMMEDIATE CLEANUP**: Several log and temporary files shouldn't be in version control:
- `backend.log`, `frontend.log`, `frontend.pid`
- Debug screenshots and temporary Python scripts
- Test result directories with generated content

### 5. Utility Script Organization (Medium Priority)
**ORGANIZATION ISSUE**: The `/frontend/util/` directory contains multiple similar Python scripts:
- RegDD14M.py, RegDD14M2_Final.py, RegDD14Q_Advanced.py, etc.
- Multiple versions suggest incomplete consolidation
- These appear to be data processing utilities

### 6. Component Architecture (Positive)
**WELL ORGANIZED**: The component architecture shows good organization:
- Clear separation by domain (auth, common, metrics, etc.)
- Consistent naming conventions within each domain
- Good use of TypeScript throughout

### 7. E2E Testing Suite (Positive)
**COMPREHENSIVE TESTING**: Well-structured E2E testing setup:
- Good coverage of different aspects (auth, accessibility, performance)
- Proper documentation and setup files
- Clear test organization

---

## ROOT DIRECTORY FILES ANALYSIS

### Configuration Files

#### Core Configuration
- `/README.md` - ACTIVELY USED - Main project documentation
- `/CLAUDE.md` - ACTIVELY USED - Claude Code assistant instructions
- `/env.example` - ACTIVELY USED - Environment variable template
- `/alembic.ini` - ACTIVELY USED - Alembic database migration configuration
- `/master.key` - SECURITY FILE - Encryption master key (sensitive)

#### Docker Configuration
- `/docker-compose.clean.yml` - ACTIVELY USED - Clean docker compose setup
- `/docker-compose.refactor.yml` - ACTIVELY USED - Refactored docker compose
- `/docker-compose.temporal.yml` - ACTIVELY USED - Temporal workflow docker setup

#### Shell Scripts
- `/restart_backend.sh` - ACTIVELY USED - Backend restart script
- `/restart_backend_clean.sh` - ACTIVELY USED - Clean backend restart
- `/restart_frontend.sh` - ACTIVELY USED - Frontend restart script
- `/start_all_services.sh` - ACTIVELY USED - Start all services script
- `/start_backend_clean.sh` - ACTIVELY USED - Clean backend start
- `/stop_all_services.sh` - ACTIVELY USED - Stop all services script
- `/stop_refactored.sh` - ACTIVELY USED - Stop refactored services
- `/setup_refactored.sh` - ACTIVELY USED - Setup refactored environment
- `/run_worker.sh` - ACTIVELY USED - Temporal worker startup

---

### Documentation Files (Extensive)

The project contains **60+ markdown documentation files**, indicating extensive documentation practices but potential over-documentation:

#### Status & Analysis Reports
- `/APPLICATION_READINESS_REPORT.md` - PROJECT STATUS - Application readiness analysis
- `/AUDIT_REPORT.md` - AUDIT DOCUMENTATION - Previous audit report
- `/AUDIT_VERSIONING_ANALYSIS.md` - VERSIONING ANALYSIS - Audit versioning review
- `/COMPREHENSIVE_REVIEW_SUMMARY.md` - REVIEW SUMMARY - Comprehensive project review
- `/CURRENT_STATUS_SUMMARY.md` - STATUS REPORT - Current project status
- `/FINAL_INTEGRATION_STATUS.md` - INTEGRATION STATUS - Final integration report
- `/IMPLEMENTATION_STATUS.md` - IMPLEMENTATION - Implementation progress
- `/TEST_RESULTS_SUMMARY.md` - TESTING - Test results summary
- `/TEST_SUMMARY.md` - TESTING - General test summary

#### Architecture & Design Documents
- `/CLEAN_ARCHITECTURE_COVERAGE_ANALYSIS.md` - ARCHITECTURE - Clean architecture analysis
- `/CLEAN_ARCHITECTURE_GUIDE.md` - ARCHITECTURE - Clean architecture guide
- `/CLEAN_ARCHITECTURE_STATUS.md` - ARCHITECTURE - Clean architecture status
- `/CODE_ORGANIZATION_OOP_ANALYSIS.md` - CODE ANALYSIS - OOP organization analysis
- `/DATABASE_SCHEMA_ANALYSIS.md` - DATABASE - Schema analysis
- `/DEVELOPMENT_PATTERNS.md` - PATTERNS - Development patterns guide

#### Feature-Specific Documentation
- `/CDO_ASSIGNMENTS_SUMMARY.md` - FEATURE - CDO assignments summary
- `/LLM_BATCH_SIZE_ANALYSIS.md` - LLM - Batch size analysis
- `/LLM_CONFIG_FIX_SUMMARY.md` - LLM - Configuration fix summary
- `/METRICS_IMPLEMENTATION_ANALYSIS.md` - METRICS - Metrics implementation
- `/RBAC_ANALYSIS.md` - RBAC - Role-based access control analysis
- `/RBAC_TEST_SUMMARY.md` - RBAC - RBAC testing summary
- `/SLA_TRACKING_ANALYSIS.md` - SLA - SLA tracking analysis

#### Temporal Workflow Documentation
- `/TEMPORAL_EXISTING_CODE_INTEGRATION.md` - TEMPORAL - Code integration
- `/TEMPORAL_HUMAN_IN_LOOP_PATTERN.md` - TEMPORAL - Human-in-loop pattern
- `/TEMPORAL_INTEGRATION.md` - TEMPORAL - Integration documentation
- `/TEMPORAL_PHASE_RECONCILIATION.md` - TEMPORAL - Phase reconciliation
- `/TEMPORAL_RECONCILIATION_COMPLETE.md` - TEMPORAL - Complete reconciliation
- `/TEMPORAL_RECONCILIATION_SUMMARY.md` - TEMPORAL - Reconciliation summary
- `/TEMPORAL_UI_ALIGNMENT_COMPLETE.md` - TEMPORAL - UI alignment

#### Workflow & Phase Documentation
- `/WORKFLOW_ANALYSIS.md` - WORKFLOW - Workflow analysis
- `/WORKFLOW_ORDER_CHANGES_SUMMARY.md` - WORKFLOW - Order changes
- `/WORKFLOW_PHASE_RENAME_ANALYSIS.md` - WORKFLOW - Phase rename analysis
- `/SAMPLE_SELECTION_FIX_SUMMARY.md` - SAMPLE SELECTION - Fix summary
- `/SAMPLE_FEEDBACK_ENHANCEMENTS.md` - SAMPLE FEEDBACK - Enhancements
- `/SCOPING_IMPLEMENTATION.md` - SCOPING - Implementation details
- `/SCOPING_READONLY_IMPLEMENTATION.md` - SCOPING - Read-only implementation

#### Testing & Quality Documentation
- `/COMPREHENSIVE_TESTING_GUIDE.md` - TESTING - Comprehensive testing guide
- `/COMPREHENSIVE_TEST_SUMMARY.md` - TESTING - Test summary
- `/ENHANCED_TESTING_RESULTS.md` - TESTING - Enhanced testing results
- `/UI_UX_CONSISTENCY_ANALYSIS.md` - UI/UX - Consistency analysis

#### Implementation & Enhancement Documents
- `/COMPREHENSIVE_ENHANCEMENT_RECOMMENDATIONS.md` - ENHANCEMENTS - Recommendations
- `/ENHANCEMENT_VALIDATION_REPORT.md` - VALIDATION - Enhancement validation
- `/IMPLEMENTATION_PLAN.md` - PLANNING - Implementation plan
- `/INDIVIDUAL_SAMPLES_IMPLEMENTATION.md` - SAMPLES - Individual samples
- `/MIGRATION_SUMMARY.md` - MIGRATION - Migration summary

**DOCUMENTATION PROLIFERATION ISSUE**: The project has excessive documentation files that may create maintenance burden and confusion.

---

### Database & Migration Files

#### SQL Files
- `/add_metadata_column.sql` - SQL SCRIPT - Add metadata column
- `/add_workflow_id.sql` - SQL SCRIPT - Add workflow ID
- `/add_workflow_id_to_cycle_reports.sql` - SQL SCRIPT - Workflow ID to cycle reports
- `/reset_phase_data.sql` - SQL SCRIPT - Reset phase data

#### Database Files
- `/synapse_dt.db` - DATABASE FILE - SQLite database (should not be in repo)
- `/test.db` - TEST DATABASE - Test database file (should not be in repo)

#### Migration Directory (/alembic/)
- `/alembic/README` - MIGRATION DOC - Alembic documentation
- `/alembic/env.py` - MIGRATION CONFIG - Alembic environment
- `/alembic/script.py.mako` - MIGRATION TEMPLATE - Script template

**Migration Files (/alembic/versions/):**
- 30+ migration files with various naming conventions
- Multiple `.role_backup` files (cleanup needed)
- Some migrations have conflicting numbering (008_* appears multiple times)
- `/alembic/versions/create_phase_metrics_table.py` - UNVERSIONED - Missing version prefix
- `/alembic/versions/create_version_history_table.py` - UNVERSIONED - Missing version prefix

---

### Log Files (Critical Cleanup Needed)

#### Application Logs
- `/backend.log` - LOG FILE - Should not be in repository
- `/backend.pid` - PROCESS FILE - Should not be in repository
- `/backend_20250619_184151.log` - TIMESTAMPED LOG - Should not be in repository
- `/backend_8001.log` - PORT-SPECIFIC LOG - Should not be in repository
- `/backend_final.log` - FINAL LOG - Should not be in repository
- `/backend_new.log` - NEW LOG - Should not be in repository
- `/frontend.log` - LOG FILE - Should not be in repository
- `/llm_activity.log` - LLM LOG - Should not be in repository
- `/rfi_phase_test.log` - PHASE LOG - Should not be in repository
- `/test_results.log` - TEST LOG - Should not be in repository
- `/test_output.log` - TEST OUTPUT - Should not be in repository
- `/test_run_output.txt` - TEST RUN - Should not be in repository

#### Worker Logs
- `/worker.log` - WORKER LOG - Should not be in repository
- `/worker2.log` through `/worker7.log` - MULTIPLE WORKER LOGS - Should not be in repository
- `/worker_final.log` - FINAL WORKER LOG - Should not be in repository
- `/worker_new.log` - NEW WORKER LOG - Should not be in repository
- `/temporal_worker.log` - TEMPORAL LOG - Should not be in repository

---

### Test & Debug Files

#### Test Data Files
- `/jobs_storage.json` - TEST DATA - Job storage data
- `/rbac_api_test_results.json` - TEST RESULTS - RBAC API test results
- `/rbac_test_results.json` - TEST RESULTS - RBAC test results
- `/rbac_test_results_20250607_130512.json` - TIMESTAMPED RESULTS - Historical test results
- `/rbac_test_results_20250607_130550.json` - TIMESTAMPED RESULTS - Historical test results
- `/workflow_pages_check.json` - TEST RESULTS - Workflow page check results

#### Test Documents
- `/test_document.pdf` - TEST FILE - PDF test document
- `/test_document.txt` - TEST FILE - Text test document

#### Screenshot & Debug Files
- 25+ PNG screenshot files for debugging and testing
- Multiple debug scripts and test validation files
- Screenshot naming follows pattern: `[feature]_[status]_[timestamp].png`

---

### Scripts Directory (/scripts/)

The `/scripts/` directory contains **100+ utility scripts**, indicating extensive automation but potential over-engineering:

#### Database & Migration Scripts
- `/scripts/setup_database.py` - DATABASE - Database setup automation
- `/scripts/create_metrics_tables.py` - DATABASE - Metrics table creation
- `/scripts/fix_migration_issues.py` - DATABASE - Migration fix utility
- `/scripts/create_sample_selection_migration.py` - DATABASE - Sample selection migration

#### User Management Scripts
- `/scripts/create_admin_user.py` - USER MGMT - Admin user creation
- `/scripts/create_test_users.py` - USER MGMT - Test user creation
- `/scripts/create_rbac_test_users.py` - USER MGMT - RBAC test users
- `/scripts/create_clean_test_user.py` - USER MGMT - Clean test user
- `/scripts/create_specific_test_user.py` - USER MGMT - Specific test user

#### RBAC Migration Scripts
- `/scripts/migrate_to_rbac.py` - RBAC - RBAC migration
- `/scripts/migrate_all_endpoints.py` - RBAC - Endpoint migration
- `/scripts/seed_rbac_permissions.py` - RBAC - Permission seeding
- `/scripts/define_rbac_resources.py` - RBAC - Resource definition

#### Testing Scripts
- `/scripts/comprehensive_test.py` - TESTING - Comprehensive test runner
- `/scripts/test_rbac_system.py` - TESTING - RBAC system testing
- `/scripts/automated_testing_executor.py` - TESTING - Automated test executor
- `/scripts/enhanced_test_executor.py` - TESTING - Enhanced test executor

#### Cleanup & Maintenance Scripts
- `/scripts/cleanup_files.sh` - CLEANUP - File cleanup utility
- `/scripts/cleanup_rename_backups.sh` - CLEANUP - Backup file cleanup
- `/scripts/final_cleanup.py` - CLEANUP - Final cleanup script
- `/scripts/reorganize_files.sh` - ORGANIZATION - File reorganization

#### Architecture Migration Scripts
- `/scripts/migrate_to_clean_architecture.py` - ARCHITECTURE - Clean architecture migration
- `/scripts/complete_clean_architecture_migration.py` - ARCHITECTURE - Complete migration
- `/scripts/migrate_to_permission_decorator.py` - ARCHITECTURE - Permission decorator migration

**SCRIPT PROLIFERATION**: The extensive number of scripts suggests:
1. Good automation practices
2. Potential over-engineering
3. Need for script consolidation and organization

---

### Prompts Directory (/prompts/)

#### Core Prompt Files
- `/prompts/attribute_batch_details.txt` - LLM PROMPT - Attribute batch details
- `/prompts/attribute_discovery.txt` - LLM PROMPT - Attribute discovery
- `/prompts/document_extraction.txt` - LLM PROMPT - Document extraction
- `/prompts/sample_generation.txt` - LLM PROMPT - Sample generation
- `/prompts/sample_generation_simple.txt` - LLM PROMPT - Simple sample generation
- `/prompts/scoping_recommendations.txt` - LLM PROMPT - Scoping recommendations

#### Provider-Specific Prompts
**Claude Provider (/prompts/claude/):**
- `/prompts/claude/attribute_batch_details.txt` - Provider-specific attribute prompts
- `/prompts/claude/attribute_generation.txt` - Provider-specific generation prompts
- `/prompts/claude/document_extraction.txt` - Provider-specific extraction prompts
- `/prompts/claude/sample_generation.txt` - Provider-specific sample prompts
- `/prompts/claude/scoping_recommendations.txt` - Provider-specific scoping prompts

**Gemini Provider (/prompts/gemini/):**
- `/prompts/gemini/attribute_discovery.txt` - Provider-specific discovery prompts
- `/prompts/gemini/attribute_generation.txt` - Provider-specific generation prompts
- `/prompts/gemini/document_extraction.txt` - Provider-specific extraction prompts
- `/prompts/gemini/scoping_recommendations.txt` - Provider-specific scoping prompts

#### Regulatory-Specific Prompts (/prompts/regulatory/)
- `/prompts/regulatory/REGULATORY_PROMPTS_GUIDE.md` - DOCUMENTATION - Regulatory prompts guide

**Basel III Prompts:**
- `/prompts/regulatory/basel_iii/basel_common/` - Basel III common prompts
  - attribute_batch_details.txt, attribute_discovery.txt, scoping_recommendations.txt, testing_approach.txt

**CCAR Prompts:**
- `/prompts/regulatory/ccar/common/` - CCAR common prompts
- `/prompts/regulatory/ccar/schedule_1a/` through `/prompts/regulatory/ccar/schedule_2a/` - Schedule-specific prompts

**FR Y-14M Prompts:**
- `/prompts/regulatory/fr_y_14m/README.md` - FR Y-14M documentation
- `/prompts/regulatory/fr_y_14m/common/` - Common FR Y-14M prompts
- `/prompts/regulatory/fr_y_14m/schedule_a_1/` through `/prompts/regulatory/fr_y_14m/schedule_d_2/` - Schedule-specific prompts
- `/prompts/regulatory/fr_y_14m/templates/schedule_template.md` - Template for schedules
- **DUPLICATE FILE**: `/prompts/regulatory/fr_y_14m/schedule_d_1/attribute_discovery copy.txt` - Copy file should be removed

**FR Y-14Q & FR Y-9C Prompts:**
- Similar structure to FR Y-14M with common and schedule-specific directories

**EXCELLENT ORGANIZATION**: The prompts directory shows sophisticated organization by provider and regulation type, supporting multi-LLM and multi-regulatory scenarios.

---

### Reference Documentation (/_reference/)

#### Documents Directory (/_reference/documents/)
- 20+ comprehensive analysis and implementation documents
- Well-organized guides, implementation plans, and status reports
- Multiple subdirectories: analysis/, guides/, implementation_plans/, summaries/, temporal/

#### Regulations Directory (/_reference/regulations/)
- `/14M/FR_Y-14M_Instructions.pdf` - Official regulatory document
- `/14Q/FR_Y-14Q20240331_i.pdf` - Official regulatory document
- `/MDRM_CSV.csv` - Master Data Reference Model CSV
- `/output/` - Contains processed data dictionary files (5 versions)

#### Specifications Directory (/_reference/specifications/)
- `/Claude_Prompts.txt` - Claude-specific prompts
- `/specifications.md` - Technical specifications

#### Legacy Reference (/_reference/synapsedv-reference/)
- Complete legacy system reference with services, APIs, and configurations
- Multiple service directories: auth/, document/, export/, file/, llm/, report/, testing/
- Legacy Docker configurations and database migrations

---

### Test Files & Scripts (Root Level)

#### Test Scripts (150+ files)
The root directory contains an extensive collection of test scripts:

**API Testing Scripts:**
- `test_api_response.py`, `test_rbac_api.py`, `test_cdo_api_endpoints.py`
- Multiple versions with `.role_backup` extensions

**UI Testing Scripts:**
- `test_all_pages_all_roles.py`, `test_frontend_flow.py`, `test_login.py`
- Screenshot validation and theme testing scripts

**Workflow Testing Scripts:**
- `test_complete_workflow.py`, `test_workflow_activities.py`, `test_temporal_workflow.py`
- Phase-specific testing scripts

**Database Testing Scripts:**
- `check_schema.py`, `debug_db.py`, `test_db_connection.py`
- Data validation and migration testing

**User & Permission Testing:**
- `test_authenticated_status.py`, `test_rbac_permissions.py`, `check_role_permissions.py`
- Assignment and dashboard testing scripts

#### Debug & Analysis Scripts
- 30+ debug scripts for specific issues and investigations
- Check scripts for validating system state
- Fix scripts for resolving identified issues

---

### Upload Storage (/uploads/)

#### Main Upload File
- `/uploads/5b9acc38-2e16-4e42-8524-78d8f4be50d2_test_regulation.txt` - Test regulation file

#### Request Info Uploads (/uploads/request_info/)
- 12 uploaded files (PDFs and images) for request information phase
- UUID-based naming convention for security
- Mix of sample credit card statements, bank statements, and generic PDFs

---

### Temporal Configuration (/temporal/)

#### Temporal Directory
- `/temporal/dynamicconfig/development-sql.yaml` - Temporal development configuration

---

## COMPREHENSIVE ANALYSIS SUMMARY

### 🔴 CRITICAL ISSUES (Immediate Action Required)

#### 1. Log File Contamination
**SEVERITY: CRITICAL**
- 20+ log files and PID files in version control
- Database files (synapse_dt.db, test.db) in repository
- Multiple worker logs and application logs
- **ACTION**: Immediate removal and .gitignore update

#### 2. Backup File Proliferation
**SEVERITY: CRITICAL**
- 100+ backup files across backend and frontend (.role_backup, .backup, .bak)
- Creates confusion and repository bloat
- **ACTION**: Mass cleanup of backup files

#### 3. Security Files
**SEVERITY: HIGH**
- `/master.key` file in repository (encryption key)
- **ACTION**: Remove from repository, add to .gitignore, regenerate key

### 🟡 HIGH PRIORITY ISSUES

#### 1. Documentation Proliferation
**SEVERITY: HIGH**
- 60+ markdown documentation files
- Potential maintenance burden and confusion
- **ACTION**: Consolidate and organize documentation

#### 2. Version Fragmentation
**SEVERITY: HIGH**
- Multiple versions of similar functionality throughout codebase
- _clean.py duplicates, v2 files, enhanced versions
- **ACTION**: Consolidate versions and remove duplicates

#### 3. Test Script Explosion
**SEVERITY: MEDIUM-HIGH**
- 150+ test scripts in root directory
- Many duplicates and legacy scripts
- **ACTION**: Organize into proper test directories

### 🟢 POSITIVE FINDINGS

#### 1. Architecture Quality
**EXCELLENT**: Clean architecture implementation with proper separation of concerns

#### 2. Prompt Management
**EXCELLENT**: Sophisticated LLM prompt organization by provider and regulation

#### 3. E2E Testing
**EXCELLENT**: Comprehensive Playwright test suite with good coverage

#### 4. API Organization
**GOOD**: Well-structured API layer with consistent patterns

### 📊 STATISTICS SUMMARY

- **Total Files Analyzed**: 1000+
- **Backup Files to Remove**: 100+
- **Log Files to Remove**: 20+
- **Documentation Files**: 60+
- **Test Scripts**: 150+
- **Migration Files**: 30+
- **Prompt Files**: 50+

### 🛠️ RECOMMENDED CLEANUP ACTIONS

#### Phase 1: Critical Cleanup (Immediate)
1. Remove all log files and database files
2. Remove all backup files (.role_backup, .backup, .bak)
3. Remove security files (master.key)
4. Update .gitignore to prevent future contamination

#### Phase 2: Version Consolidation (Week 1)
1. Consolidate _clean.py files with originals
2. Merge v2 versions with v1 where appropriate
3. Remove enhanced/fixed duplicates after verification

#### Phase 3: Organization (Week 2)
1. Move root-level test scripts to proper directories
2. Consolidate documentation files
3. Organize utility scripts in /scripts/

#### Phase 4: Architecture Refinement (Ongoing)
1. Complete temporal layer consolidation
2. Finalize clean architecture migration
3. Standardize naming conventions

This audit reveals a project with excellent architectural foundations but suffering from significant file management issues. The core functionality is solid, but maintenance burden is high due to file proliferation across multiple categories.