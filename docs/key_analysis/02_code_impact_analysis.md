# Code Impact Analysis: UUID Migration & Key Consolidation

## Overview

This document analyzes the code-level impact of migrating to UUID primary keys and consolidating redundant keys across the SynapseDTE application stack.

## Impact by Layer

### 1. Database Models Layer

#### High Impact Models (Core Business Logic)
| Model | Current PK | Foreign Keys | Impact Level | Notes |
|-------|------------|--------------|--------------|--------|
| User | user_id (INT) | 50+ relationships | CRITICAL | Central to all operations |
| TestCycle | cycle_id (INT) | 20+ relationships | HIGH | Core workflow driver |
| Report | report_id (INT) | 30+ relationships | HIGH | Core entity |
| WorkflowPhase | phase_id (INT) | All phase tables | HIGH | Central to workflow |
| ReportAttribute | id (INT) | Referenced by scoping | HIGH | Planning/scoping dependency |

#### Medium Impact Models (Feature-Specific)
| Model | Current PK | Foreign Keys | Impact Level | Notes |
|-------|------------|--------------|--------------|--------|
| DataSource | data_source_id (INT) | 10+ relationships | MEDIUM | Configuration data |
| LOB | lob_id (INT) | User assignments | MEDIUM | Organizational data |
| UniversalAssignment | assignment_id (UUID) | Already UUID | LOW | New pattern |

#### Key Redundancy Examples
```python
# Current: ScopingAttribute creates new UUID but references planning INT
class ScopingAttribute:
    attribute_id = Column(UUID, primary_key=True)  # New UUID
    planning_attribute_id = Column(Integer, ForeignKey("...id"))  # References INT

# Target: Use planning_id directly
class ScopingAttribute:
    planning_id = Column(UUID, primary_key=True)  # Reuse planning UUID
```

### 2. Service Layer Impact

#### High Impact Services
1. **Planning Services** (~15 files)
   - `PlanningService`: Creates initial attributes with INT IDs
   - `AttributeMappingService`: Maps between planning/scoping IDs
   - Impact: Complete refactor of ID handling

2. **Scoping Services** (~10 files)
   - `ScopingService`: Currently creates duplicate IDs
   - `DualModeQueryService`: Complex joins on mixed key types
   - Impact: Simplification opportunity

3. **Workflow Services** (~20 files)
   - `WorkflowPhaseService`: Manages phase transitions
   - `ActivityManagementService`: Tracks phase activities
   - Impact: Update all phase_id references

#### Query Pattern Changes
```python
# Current: Complex join due to key mismatch
query = (
    db.query(ScopingAttribute)
    .join(ReportAttribute, ScopingAttribute.planning_attribute_id == ReportAttribute.id)
    .filter(ReportAttribute.phase_id == phase_id)
)

# Target: Simplified with consistent UUIDs
query = (
    db.query(ScopingAttribute)
    .filter(ScopingAttribute.phase_id == phase_id)
)
```

### 3. API Layer Impact

#### Endpoint Changes Required
1. **ID Parameters**: All endpoints accepting IDs need updates
   ```python
   # Current
   @router.get("/users/{user_id}")
   def get_user(user_id: int):
   
   # Target
   @router.get("/users/{user_id}")
   def get_user(user_id: UUID):
   ```

2. **Response Models**: Pydantic schemas need UUID fields
   ```python
   # Current
   class UserResponse(BaseModel):
       user_id: int
   
   # Target
   class UserResponse(BaseModel):
       user_id: UUID
   ```

3. **Validation**: UUID validation in request/response models

### 4. Frontend Impact

#### Component Updates Required
1. **ID Display**: UUIDs are longer, UI adjustments needed
2. **Routing**: URL patterns with UUIDs
3. **State Management**: Redux/Context storing UUIDs
4. **Form Handling**: UUID validation and display

#### TypeScript Interface Changes
```typescript
// Current
interface User {
  user_id: number;
}

// Target
interface User {
  user_id: string; // UUID as string
}
```

### 5. Database Queries & Performance

#### Raw SQL Updates
- **Count**: ~50+ raw SQL queries identified
- **Complexity**: JOIN conditions need UUID handling
- **Performance**: UUID indexes are larger

#### ORM Query Updates
```python
# Integer comparison
.filter(User.user_id == 123)

# UUID comparison (string representation)
.filter(User.user_id == "550e8400-e29b-41d4-a716-446655440000")
```

## File-Level Impact Analysis

### Critical Files (Must Update)
1. `/app/models/base.py` - Base model classes
2. `/app/core/database.py` - Database configuration
3. `/app/models/*.py` - All model files (~60 files)
4. `/app/services/*.py` - All service files (~40 files)
5. `/app/api/v1/endpoints/*.py` - All endpoints (~30 files)

### High Impact Files
1. `/app/schemas/*.py` - Pydantic models (~30 files)
2. `/frontend/src/types/*.ts` - TypeScript interfaces
3. `/frontend/src/services/*.ts` - API service calls
4. `/migrations/versions/*.py` - Migration scripts

### Medium Impact Files
1. `/tests/*.py` - Test fixtures and assertions
2. `/scripts/*.py` - Utility scripts
3. `/docs/*.md` - Documentation updates

## Key Consolidation Impact

### Planning → Scoping Consolidation
**Current Flow:**
1. Planning creates attribute with `id` (INT)
2. Scoping creates new `attribute_id` (UUID)
3. Links via `planning_attribute_id`

**Target Flow:**
1. Planning creates attribute with `planning_id` (UUID)
2. Scoping uses same `planning_id`
3. No duplicate keys

**Benefits:**
- Removes ~15% of database columns
- Simplifies ~30 service methods
- Eliminates mapping complexity

### Estimated Code Changes

| Component | Files | Lines | Complexity |
|-----------|-------|-------|------------|
| Models | 60 | 1,500 | High |
| Services | 40 | 2,000 | High |
| APIs | 30 | 800 | Medium |
| Schemas | 30 | 600 | Low |
| Frontend | 50 | 1,000 | Medium |
| Tests | 100 | 2,500 | Medium |
| **Total** | **310** | **8,400** | **High** |

## Migration Complexity Factors

### 1. Circular Dependencies
- User ↔ Assignment tables
- Report ↔ Attribute ↔ Scoping
- Resolution: Migrate in dependency order

### 2. Composite Keys
- CycleReport uses (cycle_id, report_id)
- Migration: Create surrogate UUID key

### 3. External References
- Temporal workflow IDs
- External system integrations
- Migration: Maintain mapping tables

### 4. Data Volume
- Users: ~1,000 records
- Reports: ~10,000 records
- Attributes: ~100,000 records
- Migration time: ~2-4 hours estimated

## Risk Assessment

### High Risk Areas
1. **User Authentication**: Session/token management
2. **Workflow State**: In-progress workflows
3. **Data Integrity**: Foreign key constraints

### Medium Risk Areas
1. **Performance**: UUID index performance
2. **Storage**: 4x larger keys
3. **Compatibility**: External integrations

### Low Risk Areas
1. **New Features**: Already using UUIDs
2. **Audit Tables**: Standalone design
3. **Configuration**: Rarely referenced

## Recommendations

1. **Phased Approach**: Migrate in 5-7 phases
2. **Parallel Keys**: Maintain both during transition
3. **Feature Flags**: Enable UUID usage gradually
4. **Rollback Plan**: Keep mapping tables
5. **Performance Testing**: Benchmark before/after

## Next Steps

1. Create detailed migration plan by phase
2. Design rollback procedures
3. Set up test environment
4. Create migration scripts
5. Plan validation strategy