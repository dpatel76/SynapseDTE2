# Database Comparison Analysis: Standalone vs Container
## Date: 2025-08-06

## Executive Summary
This document provides a comprehensive comparison between the standalone database (port 5432) and the container database (port 5433), identifying significant data loss and structural differences that occurred during the containerization process.

## Critical Findings

### 1. MASSIVE DATA LOSS
The container database has lost significant amounts of data across all phases:

| Table | Standalone | Container | Missing Data | % Loss |
|-------|------------|-----------|--------------|--------|
| activity_definitions | 47 | 0 | 47 | 100% |
| cycle_report_data_profiling_results | 655 | 75 | 580 | 89% |
| cycle_report_data_profiling_rule_versions | 29 | 9 | 20 | 69% |
| cycle_report_data_profiling_rules | 1,548 | 610 | 938 | 61% |
| cycle_report_planning_attributes | 237 | 127 | 110 | 46% |
| cycle_report_planning_data_sources | 10 | 1 | 9 | 90% |
| cycle_report_planning_pde_mappings | 232 | 124 | 108 | 47% |
| cycle_report_sample_selection_samples | 63 | 10 | 53 | 84% |
| cycle_report_sample_selection_versions | 9 | 2 | 7 | 78% |
| cycle_report_scoping_versions | 34 | 2 | 32 | 94% |
| users | 26 | 8 | 18 | 69% |
| rbac_user_roles | 20 | 8 | 12 | 60% |
| test_cycles | 4 | 1 | 3 | 75% |

## Detailed Phase-by-Phase Analysis

### Planning Phase

#### 1. Planning Attributes
- **Standalone**: 237 attributes loaded
- **Container**: Only 127 attributes (46% loss)
- **Impact**: Missing critical data elements for testing

#### 2. PDE Mappings  
- **Standalone**: 232 mappings exist
- **Container**: Only 124 mappings (47% loss)
- **Impact**: Incomplete attribute-to-PDE relationships

#### 3. Data Sources
- **Standalone**: 10 data sources configured
- **Container**: Only 1 data source (90% loss)
- **Impact**: Cannot connect to multiple data sources for profiling

### Data Profiling Phase

#### 1. Profiling Rules
- **Standalone**: 1,548 rules generated
- **Container**: Only 610 rules (61% loss)
- **Impact**: Reduced data quality validation coverage

#### 2. Profiling Results
- **Standalone**: 655 execution results
- **Container**: Only 75 results (89% loss)
- **Impact**: Missing historical profiling data

#### 3. Rule Versions
- **Standalone**: 29 versions tracked
- **Container**: Only 9 versions (69% loss)
- **Impact**: Lost version history and approvals

### Scoping Phase

#### 1. Scoping Versions
- **Standalone**: 34 versions across phases
- **Container**: Only 2 versions (94% loss)
- **Impact**: Lost scoping decision history

#### 2. Scoping Decisions
- **Standalone**: Table exists with data
- **Container**: Table doesn't exist
- **Impact**: Cannot track scoping decisions

### Sample Selection Phase

#### 1. Sample Selection Samples
- **Standalone**: 63 samples across multiple versions
- **Container**: Only 10 samples (84% loss)
- **Impact**: Insufficient test samples

#### 2. Sample Versions
- **Standalone**: 9 versions
- **Container**: Only 2 versions (78% loss)
- **Impact**: Lost sample generation history

### Workflow Management

#### 1. Activity Definitions
- **Standalone**: 47 activity definitions
- **Container**: 0 definitions (100% loss)
- **Impact**: No activity templates available

#### 2. Workflow Activities
- **Standalone**: No activities (possibly different structure)
- **Container**: 42 activities loaded
- **Note**: Container has activities but missing definitions

### User & Access Control

#### 1. Users
- **Standalone**: 26 users
- **Container**: Only 8 users (69% loss)
- **Impact**: Missing user accounts

#### 2. User Roles
- **Standalone**: 20 role assignments
- **Container**: Only 8 assignments (60% loss)
- **Impact**: Incomplete permissions

## Root Causes Identified

### 1. Missing Migration Scripts
The container database appears to be missing several data migration scripts that should have:
- Loaded activity definitions
- Migrated existing planning attributes
- Copied profiling rules and results
- Transferred user accounts

### 2. Incomplete Seed Data
The container initialization only loads minimal seed data instead of copying existing production data.

### 3. Schema Differences
Some tables have different structures between versions:
- `cycle_report_scoping_decisions` doesn't exist in container
- Phase ID references are inconsistent

### 4. Lost Historical Data
Container database was initialized fresh without migrating historical data from standalone.

## Recommended Fixes

### Immediate Actions (Priority 1)

#### 1. Create Data Migration Script
```python
# scripts/migrate_standalone_to_container.py
"""
Migrate all data from standalone DB to container DB
"""
import psycopg2
from psycopg2.extras import RealDictCursor

def migrate_table(table_name, source_conn, target_conn):
    """Generic table migration"""
    source_cur = source_conn.cursor(cursor_factory=RealDictCursor)
    target_cur = target_conn.cursor()
    
    # Get data from source
    source_cur.execute(f"SELECT * FROM {table_name}")
    rows = source_cur.fetchall()
    
    if rows:
        # Build insert statement
        columns = rows[0].keys()
        placeholders = ','.join(['%s'] * len(columns))
        insert_sql = f"""
            INSERT INTO {table_name} ({','.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """
        
        # Insert data
        for row in rows:
            target_cur.execute(insert_sql, list(row.values()))
    
    target_conn.commit()
    print(f"Migrated {len(rows)} rows to {table_name}")

# Tables to migrate in order (respecting foreign keys)
MIGRATION_ORDER = [
    'activity_definitions',
    'cycle_report_planning_attributes',
    'cycle_report_planning_data_sources',
    'cycle_report_planning_pde_mappings',
    'cycle_report_data_profiling_rules',
    'cycle_report_data_profiling_rule_versions',
    'cycle_report_data_profiling_results',
    'cycle_report_scoping_versions',
    'cycle_report_sample_selection_versions',
    'cycle_report_sample_selection_samples',
]
```

#### 2. Fix Activity Definitions
```sql
-- Alembic migration to load activity definitions
INSERT INTO activity_definitions (phase_name, sequence_order, activity_name, ...)
SELECT phase_name, sequence_order, activity_name, ...
FROM standalone_backup.activity_definitions;
```

#### 3. Restore Planning Data
```python
# Restore all planning phase data with proper phase_id mapping
def restore_planning_data():
    # Map old phase_ids to new phase_ids
    phase_mapping = get_phase_id_mapping()
    
    # Migrate attributes
    migrate_planning_attributes(phase_mapping)
    
    # Migrate data sources
    migrate_data_sources(phase_mapping)
    
    # Migrate PDE mappings
    migrate_pde_mappings(phase_mapping)
```

### Short-term Actions (Priority 2)

#### 1. Create Database Sync Tool
Build a tool to keep databases in sync during transition period:
```python
# scripts/sync_databases.py
class DatabaseSync:
    def __init__(self, source_conn, target_conn):
        self.source = source_conn
        self.target = target_conn
    
    def sync_incremental(self, table_name, key_column='id'):
        """Sync only new/updated records"""
        # Get max ID in target
        # Copy records with ID > max_id
        # Update modified records based on updated_at
```

#### 2. Add Data Validation
```python
# scripts/validate_container_data.py
def validate_data_completeness():
    checks = []
    
    # Check activity definitions
    if count_records('activity_definitions') == 0:
        checks.append("ERROR: No activity definitions loaded")
    
    # Check each phase has required data
    for phase in PHASES:
        if not phase_has_required_data(phase):
            checks.append(f"ERROR: Phase {phase} missing data")
    
    return checks
```

### Long-term Actions (Priority 3)

#### 1. Implement Proper Data Seeding
- Create comprehensive seed data scripts
- Include all reference data
- Add sample test data for each phase

#### 2. Add Database Health Checks
- Monitor data completeness
- Alert on missing critical data
- Regular validation of data integrity

#### 3. Version Control for Data
- Track data changes with migrations
- Implement data versioning
- Add rollback capabilities

## Testing Requirements

### 1. Data Migration Testing
- [ ] Verify all tables have correct row counts
- [ ] Validate foreign key relationships
- [ ] Check data integrity constraints
- [ ] Test application functionality with migrated data

### 2. Integration Testing
- [ ] Test Planning phase with full attribute set
- [ ] Execute Data Profiling with all rules
- [ ] Verify Scoping decisions are saved
- [ ] Validate Sample Selection generation

### 3. User Acceptance Testing
- [ ] All users can log in
- [ ] Permissions work correctly
- [ ] Historical data is accessible
- [ ] Workflows execute properly

## Implementation Timeline

### Week 1
- Create and test migration scripts
- Restore activity definitions
- Fix Planning phase data

### Week 2
- Migrate Data Profiling data
- Restore Scoping versions
- Fix Sample Selection data

### Week 3
- User and permission migration
- Testing and validation
- Documentation updates

## Conclusion

The container database has lost approximately 60-90% of data across critical tables. This is not a minor issue but a fundamental data loss problem that requires immediate attention. The recommended migration scripts and fixes should be implemented urgently to restore full functionality.

## Appendix: Quick Fix Commands

```bash
# Backup container database before fixes
pg_dump -h localhost -p 5433 -U synapse_user -d synapse_dt > container_backup.sql

# Run migration script
python scripts/migrate_standalone_to_container.py

# Validate migration
python scripts/validate_container_data.py

# Test application
python scripts/run_integration_tests.py
```