# Audit Fields Implementation Guide

This guide explains the implementation of `created_by` and `updated_by` audit fields across the SynapseDTE system.

## Overview

We've implemented a comprehensive audit system that automatically tracks which user created or last updated each record in the database. This is done through:

1. **AuditMixin** - A SQLAlchemy mixin that adds audit fields to models
2. **Context Management** - Tracks the current user throughout the request
3. **Middleware** - Automatically extracts user information from JWT tokens
4. **Event Listeners** - Automatically populate audit fields on insert/update

## Implementation Components

### 1. AuditMixin (`app/models/audit_mixin.py`)

Provides two fields and their relationships:
- `created_by_id` - Foreign key to users table
- `updated_by_id` - Foreign key to users table
- `created_by` - Relationship to User model
- `updated_by` - Relationship to User model

### 2. Enhanced Base Models (`app/models/base.py`)

Two new base classes that include audit fields:
- `AuditableBaseModel` - For models with auto-generated integer IDs
- `AuditableCustomPKModel` - For models with custom primary keys

### 3. Context Management (`app/core/context.py`)

Manages request-scoped user context using Python's `contextvars`.

### 4. Audit Middleware (`app/middleware/audit_middleware.py`)

Extracts user information from JWT tokens and sets it in the context.

### 5. Database Migration

- **Alembic Migration**: `012_add_audit_fields_to_all_tables.py`
- **Manual Script**: `scripts/deployment/add_audit_fields_migration.py`

## How to Update Models

### Option 1: For New Models

Use the auditable base classes:

```python
from app.models.base import AuditableBaseModel, AuditableCustomPKModel

# For models with auto-generated IDs
class NewModel(AuditableBaseModel):
    __tablename__ = "new_models"
    
    name = Column(String(255))
    # ... other fields

# For models with custom primary keys
class NewCustomModel(AuditableCustomPKModel):
    __tablename__ = "new_custom_models"
    
    custom_id = Column(String(50), primary_key=True)
    # ... other fields
```

### Option 2: For Existing Models

Add the AuditMixin to existing models:

```python
from app.models.base import CustomPKModel
from app.models.audit_mixin import AuditMixin

class Report(CustomPKModel, AuditMixin):  # Add AuditMixin
    __tablename__ = "reports"
    
    report_id = Column(Integer, primary_key=True)
    # ... existing fields remain unchanged
```

## Running the Migration

### Using Alembic (Recommended)

```bash
# Check current migration status
alembic current

# Run the migration
alembic upgrade head

# Or specifically run the audit fields migration
alembic upgrade 012_add_audit_fields_to_all_tables
```

### Using Manual Script (Alternative)

```bash
# Run the migration
python scripts/deployment/add_audit_fields_migration.py

# Rollback if needed
python scripts/deployment/add_audit_fields_migration.py --rollback
```

## Automatic Population

Once implemented, the audit fields are automatically populated:

1. **On Insert**: Both `created_by_id` and `updated_by_id` are set to the current user
2. **On Update**: Only `updated_by_id` is updated to the current user

This happens automatically through SQLAlchemy event listeners - no changes to CRUD operations are needed!

## Accessing Audit Information

```python
# In your code, you can access the audit information
report = session.query(Report).first()

# Get who created the record
creator = report.created_by  # User object
creator_email = report.created_by.email if report.created_by else None

# Get who last updated the record
updater = report.updated_by  # User object
updater_email = report.updated_by.email if report.updated_by else None
```

## Backend-Only Implementation

The audit fields are completely handled in the backend:

1. **No Frontend Changes Required** - The frontend doesn't need to send user information
2. **Automatic from JWT** - User info is extracted from the authentication token
3. **Transparent to API** - No changes to API endpoints or schemas needed
4. **Database Level** - All tracking happens at the database level

## Important Considerations

### 1. Nullable Fields

The audit fields are nullable to:
- Avoid breaking existing records
- Handle system operations (migrations, scripts)
- Support unauthenticated operations (if any)

### 2. Existing User Tracking Fields

Many models already have specific user tracking fields like:
- `assigned_by`
- `submitted_by`
- `approved_by`
- `executed_by`

These fields are preserved as they provide specific context about actions. The new `created_by` and `updated_by` fields provide general record-level tracking.

### 3. Performance

Indexes are created on both audit fields for efficient querying:
- `idx_<table>_created_by`
- `idx_<table>_updated_by`

### 4. Scripts and Background Jobs

For operations outside of HTTP requests (scripts, background jobs), the audit fields will be NULL unless you manually set the user context:

```python
from app.core.context import set_current_user_context

# Set user context for scripts
set_current_user_context({"user_id": 1, "email": "system@example.com"})

# Now database operations will use this user
```

## Testing the Implementation

### 1. Check Migration Status

```sql
-- Check if audit columns exist
SELECT 
    table_name,
    COUNT(CASE WHEN column_name = 'created_by_id' THEN 1 END) as has_created_by,
    COUNT(CASE WHEN column_name = 'updated_by_id' THEN 1 END) as has_updated_by
FROM information_schema.columns
WHERE table_schema = 'public'
AND column_name IN ('created_by_id', 'updated_by_id')
GROUP BY table_name
ORDER BY table_name;
```

### 2. Test Audit Tracking

```python
# Create a new record (as authenticated user)
POST /api/v1/reports
{
    "report_name": "Test Report",
    "regulation": "SOX"
}

# Check the database
SELECT 
    report_name,
    created_by_id,
    updated_by_id,
    u1.email as created_by_email,
    u2.email as updated_by_email
FROM reports r
LEFT JOIN users u1 ON r.created_by_id = u1.user_id
LEFT JOIN users u2 ON r.updated_by_id = u2.user_id
WHERE report_name = 'Test Report';
```

## Troubleshooting

### Issue: Audit fields not being populated

1. Check middleware is registered in `main.py`
2. Verify JWT token is being sent in requests
3. Check user context is being set properly

### Issue: Migration fails

1. Check foreign key constraints
2. Ensure users table exists
3. Review migration logs for specific errors

### Issue: Performance degradation

1. Ensure indexes were created
2. Consider batch updates for large tables
3. Monitor query performance

## Summary

This implementation provides comprehensive audit tracking with:
- ✅ Automatic user tracking on all database operations
- ✅ No frontend changes required
- ✅ Backward compatible with existing data
- ✅ Performance optimized with indexes
- ✅ Consistent across entire system
- ✅ Easy to implement on new and existing models