# UUID Migration Strategy & Implementation Plan

## Migration Approach: Direct Cutover with Safety Nets

Based on the requirement for direct migration without parallel implementation, this strategy focuses on a phased cutover approach with comprehensive safety measures.

## Migration Phases Overview

### Phase 1: Foundation & Infrastructure (Week 1)
- Migration framework setup
- Backup and rollback procedures
- UUID generation utilities
- Validation tools

### Phase 2: Leaf Tables Migration (Week 2)
- Tables with no foreign key dependencies
- Audit logs, configuration tables
- Low-risk, high-learning value

### Phase 3: User & Core Entities (Week 3-4)
- User table (highest impact)
- LOB, Role, Permission tables
- Authentication system updates

### Phase 4: Workflow Core Migration (Week 5-6)
- TestCycle, Report tables
- WorkflowPhase consolidation
- CycleReport composite key resolution

### Phase 5: Attribute System Migration (Week 7-8)
- ReportAttribute to UUID
- Planning/Scoping consolidation
- Remove redundant keys

### Phase 6: Dependent Systems (Week 9)
- Test execution tables
- Observation management
- Sample selection

### Phase 7: Cleanup & Optimization (Week 10)
- Remove old columns
- Optimize indexes
- Performance tuning

## Detailed Phase Implementation

### Phase 1: Foundation & Infrastructure

#### 1.1 Migration Framework
```python
# migration_framework.py
class UUIDMigrator:
    def __init__(self, connection):
        self.conn = connection
        self.mapping_table = "uuid_migration_mapping"
        
    def create_mapping_table(self):
        """Create table to track ID mappings during migration"""
        sql = """
        CREATE TABLE IF NOT EXISTS uuid_migration_mapping (
            table_name VARCHAR(100),
            old_id INTEGER,
            new_id UUID,
            migrated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (table_name, old_id)
        );
        """
        
    def add_uuid_column(self, table, column="uuid_id"):
        """Add UUID column to existing table"""
        sql = f"""
        ALTER TABLE {table} 
        ADD COLUMN {column} UUID DEFAULT gen_random_uuid();
        """
        
    def migrate_foreign_keys(self, table, fk_column, ref_table):
        """Update foreign keys to use UUIDs"""
        sql = f"""
        UPDATE {table} t
        SET {fk_column}_uuid = m.new_id
        FROM uuid_migration_mapping m
        WHERE m.table_name = '{ref_table}'
        AND t.{fk_column} = m.old_id;
        """
```

#### 1.2 Backup Strategy
```bash
#!/bin/bash
# backup_before_migration.sh

# Full database backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_$(date +%Y%m%d_%H%M%S).sql

# Table-specific backups
for table in users reports test_cycles workflow_phases; do
    pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -t $table > backup_${table}_$(date +%Y%m%d_%H%M%S).sql
done
```

#### 1.3 Rollback Procedures
```sql
-- Rollback script template
BEGIN;
-- Restore from mapping table
UPDATE users 
SET user_id = m.old_id
FROM uuid_migration_mapping m
WHERE users.uuid_id = m.new_id
AND m.table_name = 'users';

-- Drop UUID columns
ALTER TABLE users DROP COLUMN uuid_id;

-- Restore foreign keys
-- ... (automated by rollback script)
COMMIT;
```

### Phase 2: Leaf Tables Migration

#### Target Tables
1. audit_logs
2. llm_audit_logs  
3. configuration tables
4. lookup tables

#### Migration Script Example
```sql
-- Migrate audit_logs table
BEGIN;
-- Add UUID column
ALTER TABLE audit_logs ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();

-- Create unique index
CREATE UNIQUE INDEX idx_audit_logs_uuid ON audit_logs(uuid_id);

-- Store mapping
INSERT INTO uuid_migration_mapping (table_name, old_id, new_id)
SELECT 'audit_logs', audit_id, uuid_id FROM audit_logs;

-- Make UUID primary key
ALTER TABLE audit_logs DROP CONSTRAINT audit_logs_pkey;
ALTER TABLE audit_logs ADD PRIMARY KEY (uuid_id);
ALTER TABLE audit_logs ALTER COLUMN audit_id DROP NOT NULL;

COMMIT;
```

### Phase 3: User Table Migration (Critical)

#### 3.1 Pre-Migration Validation
```python
def validate_user_migration_readiness():
    checks = []
    
    # Check for duplicate emails
    duplicates = db.query(User).group_by(User.email).having(func.count() > 1).all()
    checks.append(("Duplicate emails", len(duplicates) == 0))
    
    # Check active sessions
    active_sessions = get_active_sessions()
    checks.append(("Active sessions", len(active_sessions)))
    
    # Check in-progress workflows
    active_workflows = get_active_workflows()
    checks.append(("Active workflows", len(active_workflows)))
    
    return checks
```

#### 3.2 User Migration Script
```sql
-- Phase 3: User table migration
BEGIN;

-- Add UUID column
ALTER TABLE users ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();
CREATE UNIQUE INDEX idx_users_uuid ON users(uuid_id);

-- Store mapping
INSERT INTO uuid_migration_mapping (table_name, old_id, new_id)
SELECT 'users', user_id, uuid_id FROM users;

-- Update all foreign keys pointing to users
-- This is automated by migration script scanning information_schema

-- Update application code to use uuid_id (deployment required here)

-- After verification, swap primary key
ALTER TABLE users DROP CONSTRAINT users_pkey;
ALTER TABLE users ADD PRIMARY KEY (uuid_id);
ALTER TABLE users RENAME COLUMN user_id TO legacy_user_id;
ALTER TABLE users RENAME COLUMN uuid_id TO user_id;

COMMIT;
```

#### 3.3 Authentication System Updates
```python
# Update JWT token generation
def create_access_token(user_id: UUID):  # Changed from int
    payload = {
        "sub": str(user_id),  # UUID as string in JWT
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

### Phase 4: Workflow Core Migration

#### 4.1 Composite Key Resolution
```sql
-- CycleReport has composite PK (cycle_id, report_id)
-- Solution: Add surrogate UUID key

ALTER TABLE cycle_reports ADD COLUMN id UUID DEFAULT gen_random_uuid();
CREATE UNIQUE INDEX idx_cycle_reports_uuid ON cycle_reports(id);

-- Maintain composite unique constraint
ALTER TABLE cycle_reports ADD CONSTRAINT uq_cycle_report UNIQUE (cycle_id, report_id);

-- Update references to use new UUID
-- ... foreign key updates
```

#### 4.2 Phase Consolidation
```sql
-- Consolidate workflow_phases to use UUID
BEGIN;

ALTER TABLE workflow_phases ADD COLUMN uuid_id UUID DEFAULT gen_random_uuid();

-- Migrate all phase-specific tables to reference UUID
UPDATE cycle_report_planning_attributes 
SET phase_uuid = wp.uuid_id
FROM workflow_phases wp
WHERE cycle_report_planning_attributes.phase_id = wp.phase_id;

COMMIT;
```

### Phase 5: Attribute System & Key Consolidation

#### 5.1 Planning to Scoping Consolidation
```sql
-- Remove redundant scoping keys
BEGIN;

-- First, ensure planning attributes have UUIDs
ALTER TABLE cycle_report_planning_attributes 
ADD COLUMN planning_id UUID DEFAULT gen_random_uuid();

-- Update scoping to use planning UUIDs directly
UPDATE cycle_report_scoping_attributes sa
SET planning_id = pa.planning_id
FROM cycle_report_planning_attributes pa
WHERE sa.planning_attribute_id = pa.id;

-- Drop redundant columns
ALTER TABLE cycle_report_scoping_attributes 
DROP COLUMN attribute_id,
DROP COLUMN planning_attribute_id;

-- Rename for clarity
ALTER TABLE cycle_report_scoping_attributes 
RENAME COLUMN planning_id TO id;

COMMIT;
```

#### 5.2 Consolidation Benefits
- Removes 15% of columns
- Simplifies 30+ queries
- Eliminates mapping complexity

### Phase 6: Dependent Systems

#### Migration Order
1. Test execution tables
2. Observation tables
3. Sample selection tables
4. RFI (Request for Information) tables
5. Data profiling tables

### Phase 7: Cleanup & Optimization

#### 7.1 Remove Legacy Columns
```sql
-- After full verification
ALTER TABLE users DROP COLUMN legacy_user_id;
ALTER TABLE reports DROP COLUMN legacy_report_id;
-- ... etc for all tables
```

#### 7.2 Index Optimization
```sql
-- UUID indexes need different strategies
CREATE INDEX idx_users_uuid_hash ON users USING hash(user_id);
CREATE INDEX idx_reports_created_at ON reports(created_at) WHERE deleted_at IS NULL;
```

## Implementation Timeline

| Week | Phase | Description | Risk Level |
|------|-------|-------------|------------|
| 1 | Foundation | Setup migration framework | Low |
| 2 | Leaf Tables | Migrate standalone tables | Low |
| 3-4 | User System | Migrate user and auth | **Critical** |
| 5-6 | Workflow Core | Migrate cycles, reports, phases | High |
| 7-8 | Attributes | Consolidate planning/scoping | High |
| 9 | Dependent | Remaining tables | Medium |
| 10 | Cleanup | Remove old columns, optimize | Low |

## Code Deployment Strategy

### Deployment Checkpoints
1. **After Phase 1**: Deploy migration framework
2. **After Phase 2**: Validate leaf table migration
3. **Before Phase 3**: Full backup, maintenance window
4. **After Phase 3**: Extensive testing, possible rollback point
5. **After Phase 5**: Major consolidation complete
6. **After Phase 7**: Final cleanup

### Feature Flags
```python
# feature_flags.py
class FeatureFlags:
    USE_UUID_FOR_USERS = os.getenv("FF_UUID_USERS", "false") == "true"
    USE_UUID_FOR_REPORTS = os.getenv("FF_UUID_REPORTS", "false") == "true"
    USE_CONSOLIDATED_ATTRIBUTES = os.getenv("FF_CONSOLIDATED_ATTRS", "false") == "true"
```

## Validation Strategy

### Automated Validation
```python
class MigrationValidator:
    def validate_phase(self, phase_number):
        validations = {
            1: self.validate_framework,
            2: self.validate_leaf_tables,
            3: self.validate_user_system,
            # ...
        }
        return validations[phase_number]()
    
    def validate_user_system(self):
        # Check row counts match
        # Verify all FKs updated
        # Test authentication
        # Verify no orphaned records
        pass
```

### Manual Testing Checklist
- [ ] User login/logout
- [ ] Create new test cycle
- [ ] Complete workflow phase
- [ ] Generate reports
- [ ] API response validation

## Rollback Decision Points

### Criteria for Rollback
1. Data corruption detected
2. Performance degradation >20%
3. Critical feature failure
4. Authentication system issues

### Rollback Procedure
1. Stop application servers
2. Run phase-specific rollback script
3. Restore from mapping tables
4. Restart with previous code version
5. Validate system functionality

## Success Metrics

### Technical Metrics
- Zero data loss
- Query performance within 10% of baseline
- All foreign keys properly migrated
- No orphaned records

### Business Metrics
- No disruption to active workflows
- User authentication maintained
- Reports generate correctly
- API compatibility maintained

## Next Steps

1. Review and approve migration plan
2. Set up test environment
3. Create detailed migration scripts
4. Develop validation suite
5. Schedule maintenance windows
6. Begin Phase 1 implementation