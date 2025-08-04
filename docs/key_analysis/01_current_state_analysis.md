# Current State Analysis: Database Schema & Key Patterns

## Executive Summary

The SynapseDTE application currently uses a mixed approach to primary keys:
- **Integer primary keys**: Most tables use auto-incrementing integers
- **UUID primary keys**: Only newer versioning tables (ScopingVersion, PlanningVersion) use UUIDs
- **Key redundancy**: Several instances of duplicate keys (e.g., planning_id vs scoping_key pattern)

## Current Schema Analysis

### 1. Primary Key Types Distribution

#### Integer-Based Primary Keys (Legacy Pattern)
```sql
-- User table
user_id INTEGER PRIMARY KEY

-- Report and cycle tables  
cycle_id INTEGER PRIMARY KEY
report_id INTEGER PRIMARY KEY

-- Workflow tracking
phase_id INTEGER PRIMARY KEY
activity_id INTEGER PRIMARY KEY

-- Planning attributes
id INTEGER PRIMARY KEY (cycle_report_planning_attributes)

-- Data sources
data_source_id INTEGER PRIMARY KEY
```

#### UUID-Based Primary Keys (New Pattern)
```sql
-- Version management tables
version_id UUID PRIMARY KEY (cycle_report_planning_versions)
version_id UUID PRIMARY KEY (cycle_report_scoping_versions)
attribute_id UUID PRIMARY KEY (cycle_report_scoping_attributes)
```

#### Composite Primary Keys
```sql
-- CycleReport junction table
PRIMARY KEY (cycle_id, report_id)
```

### 2. Key Redundancy Patterns

#### Pattern 1: Planning ID → Scoping Key
**Current Implementation:**
- Planning phase creates attributes with `id` (integer)
- Scoping phase references `planning_attribute_id` but creates new `attribute_id` (UUID)
- This creates unnecessary duplication and complexity

**Example from models:**
```python
# In ScopingAttribute model
planning_attribute_id = Column(Integer, ForeignKey("cycle_report_planning_attributes.id"), nullable=False)
attribute_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
```

#### Pattern 2: Phase-Specific IDs
Multiple tables create their own IDs when they could reference a common phase_id:
- Data profiling creates separate profiling IDs
- Sample selection creates separate sample IDs
- Each phase maintains its own versioning

### 3. Foreign Key Relationships

#### Current Cascading Rules
- Most relationships use `CASCADE` on delete
- Some use `SET NULL` for optional relationships
- No consistent pattern across the application

#### Circular Dependencies
Several circular reference patterns exist:
- User ↔ Various assignment tables
- WorkflowPhase ↔ Version tables
- Report ↔ Attribute ↔ PDE mappings

### 4. Model Inheritance Hierarchy

```
Base
├── BaseModel (id: Integer)
├── CustomPKModel (no default PK)
├── AuditableBaseModel (BaseModel + AuditMixin)
└── AuditableCustomPKModel (CustomPKModel + AuditMixin)
```

## Key Usage Patterns

### 1. Workflow Progression
Each workflow phase creates its own records with references back:
```
TestCycle (cycle_id) → CycleReport (cycle_id, report_id) → WorkflowPhase (phase_id)
                                                         ↓
                                          PlanningVersion (version_id, phase_id)
                                                         ↓
                                          ReportAttribute (id, phase_id)
                                                         ↓
                                          ScopingAttribute (attribute_id, planning_attribute_id)
```

### 2. Version Management Pattern
Newer tables implement versioning:
- PlanningVersion: UUID-based versioning
- ScopingVersion: UUID-based versioning
- Each maintains parent_version_id for history

### 3. Assignment Pattern
Multiple assignment tables with similar structure:
- UniversalAssignment (attempting to consolidate)
- Legacy specific assignment tables still referenced

## Database Statistics

### Table Count by Key Type
- Integer PK tables: ~40 tables
- UUID PK tables: ~5 tables
- Composite PK tables: ~3 tables

### Relationship Complexity
- Average foreign keys per table: 3-5
- Maximum foreign keys in a table: 8 (User table)
- Circular dependencies: 5+ patterns identified

## Impact Analysis Summary

### High Impact Areas
1. **User Management**: Central to all operations, 50+ relationships
2. **Workflow Phases**: Core to application flow, referenced everywhere
3. **Report Attributes**: Planning/Scoping/Testing all depend on this

### Medium Impact Areas
1. **Version Management**: Already uses UUIDs, easier to migrate
2. **Assignment Tables**: Being consolidated already
3. **Audit Tables**: Standalone, easier to migrate

### Low Impact Areas
1. **Configuration Tables**: Few relationships
2. **Lookup Tables**: Minimal foreign key usage
3. **Log Tables**: Often standalone

## Key Consolidation Opportunities

### 1. Planning → Scoping Attribute Consolidation
- Remove `scoping_key` concept entirely
- Use `planning_id` throughout the workflow
- Estimated impact: 15+ files, 50+ queries

### 2. Phase-Based ID Consolidation
- Use `phase_id` as primary reference
- Remove phase-specific IDs
- Estimated impact: 20+ files, 100+ queries

### 3. Assignment Table Consolidation
- Complete migration to UniversalAssignment
- Remove legacy assignment tables
- Already in progress

## Technical Debt Assessment

### Critical Issues
1. **Mixed key types**: Complicates joins and queries
2. **Redundant keys**: Increases complexity and storage
3. **Inconsistent patterns**: Makes code harder to maintain

### Performance Implications
1. **Integer vs UUID joins**: UUID joins are slightly slower
2. **Index size**: UUID indexes are 4x larger
3. **Query complexity**: Redundant keys require more joins

### Maintenance Burden
1. **Developer confusion**: Which key to use when?
2. **Bug potential**: Wrong key references
3. **Migration complexity**: Future changes harder

## Next Steps

1. Complete code impact analysis across all layers
2. Design target schema with UUID standardization
3. Create detailed migration plan with phases
4. Develop rollback procedures
5. Plan performance testing strategy