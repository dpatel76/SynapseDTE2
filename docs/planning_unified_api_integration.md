# Unified Planning Phase API Integration Guide

## Overview

The unified planning phase API provides a streamlined 4-table architecture for managing planning phase workflows with tester-only approval processes. This replaces the previous 7+ table legacy architecture with improved performance and maintainability.

## Architecture Overview

### New 4-Table Architecture

1. **`cycle_report_planning_versions`** - Version management and planning metadata
2. **`cycle_report_planning_data_sources`** - Phase-level data source definitions  
3. **`cycle_report_planning_attributes`** - Individual planning attributes
4. **`cycle_report_planning_pde_mappings`** - PDE mappings for attributes

### Key Features

- **Phase-level data sources**: Multiple data sources per phase instead of per-attribute
- **Multiple PDE mappings per attribute**: Support for complex mapping scenarios
- **Tester-only approval workflow**: Streamlined approval process without report owner review
- **Auto-approval rules**: LLM-assisted approval for low-risk mappings
- **UUID primary keys**: Better scalability and distribution
- **JSONB metadata**: Flexible storage for LLM and classification data

## API Endpoints

### Base URL
```
/api/v1/planning-unified
```

### Version Management

#### Create Planning Version
```http
POST /versions
```

**Request Body:**
```json
{
  "phase_id": 123,
  "workflow_activity_id": 456,
  "parent_version_id": "uuid-string" // optional
}
```

#### Get Planning Version
```http
GET /versions/{version_id}
```

#### Submit for Approval
```http
POST /versions/{version_id}/submit
```

#### Approve/Reject Version
```http
POST /versions/{version_id}/approve
```

**Request Body:**
```json
{
  "action": "approve|reject",
  "notes": "Optional approval/rejection notes"
}
```

### Data Source Management

#### Create Data Source
```http
POST /versions/{version_id}/data-sources
```

**Request Body:**
```json
{
  "source_name": "CustomerDatabase",
  "source_type": "database",
  "description": "Main customer database",
  "connection_config": {
    "host": "db.example.com",
    "port": 5432,
    "database": "customers"
  },
  "auth_config": {
    "username": "app_user",
    "auth_type": "password"
  },
  "refresh_schedule": "0 0 * * *",
  "estimated_record_count": 1000000,
  "data_freshness_hours": 24
}
```

#### Update Data Source Decision
```http
PUT /data-sources/{data_source_id}/decision
```

**Request Body:**
```json
{
  "decision": "approve|reject|request_changes",
  "notes": "Decision rationale"
}
```

### Attribute Management

#### Create Attribute
```http
POST /versions/{version_id}/attributes
```

**Request Body:**
```json
{
  "attribute_name": "customer_id",
  "data_type": "string",
  "description": "Unique customer identifier",
  "business_definition": "Primary key for customer records",
  "is_mandatory": true,
  "is_cde": false,
  "is_primary_key": true,
  "max_length": 50,
  "information_security_classification": "internal",
  "llm_metadata": {
    "confidence_score": 0.95,
    "generated_by": "claude-3",
    "suggestions": []
  }
}
```

#### Update Attribute Decision
```http
PUT /attributes/{attribute_id}/decision
```

### PDE Mapping Management

#### Create PDE Mapping
```http
POST /attributes/{attribute_id}/pde-mappings
```

**Request Body:**
```json
{
  "data_source_id": "uuid-string",
  "pde_name": "Customer Identifier",
  "pde_code": "CUST_ID_001",
  "mapping_type": "direct",
  "source_table": "customers",
  "source_column": "customer_id",
  "source_field": "customers.customer_id",
  "column_data_type": "VARCHAR(50)",
  "transformation_rule": null,
  "condition_rule": null,
  "is_primary": true,
  "classification": {
    "risk_level": "low",
    "criticality": "high",
    "information_security": "internal"
  },
  "llm_metadata": {
    "confidence_score": 0.92,
    "auto_classified": true
  }
}
```

#### Update PDE Mapping Decision
```http
PUT /pde-mappings/{pde_mapping_id}/decision
```

### Bulk Operations

#### Bulk Tester Decision
```http
POST /bulk-decision
```

**Request Body:**
```json
{
  "item_ids": ["uuid1", "uuid2", "uuid3"],
  "item_type": "data_source|attribute|pde_mapping",
  "decision": "approve|reject|request_changes",
  "notes": "Bulk approval rationale"
}
```

### Dashboard and Analytics

#### Get Planning Dashboard
```http
GET /versions/{version_id}/dashboard
```

**Response includes:**
- Version details and status
- All data sources with approval status
- All attributes with approval status  
- All PDE mappings with approval status
- Completion percentage
- Pending decisions count
- Submission eligibility

## Frontend Integration

### Key Components to Update

1. **Planning Version List**: Show unified versions instead of legacy tables
2. **Data Source Management**: Phase-level data source configuration
3. **Attribute Editor**: Enhanced attribute definition with LLM assistance
4. **PDE Mapping Interface**: Support for multiple mappings per attribute
5. **Tester Decision Interface**: Streamlined approval workflow
6. **Dashboard**: Real-time completion tracking

### State Management

```typescript
interface PlanningState {
  currentVersion: PlanningVersion | null;
  dataSources: PlanningDataSource[];
  attributes: PlanningAttribute[];
  pdeMappings: PlanningPDEMapping[];
  dashboardData: PlanningDashboard | null;
  loading: boolean;
  error: string | null;
}
```

### API Client Example

```typescript
class PlanningUnifiedClient {
  private baseUrl = '/api/v1/planning-unified';

  async createVersion(phaseId: number): Promise<PlanningVersion> {
    const response = await fetch(`${this.baseUrl}/versions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phase_id: phaseId })
    });
    return response.json();
  }

  async getVersionDashboard(versionId: string): Promise<PlanningDashboard> {
    const response = await fetch(`${this.baseUrl}/versions/${versionId}/dashboard`);
    return response.json();
  }

  async updateDataSourceDecision(
    dataSourceId: string, 
    decision: Decision, 
    notes?: string
  ): Promise<TesterDecisionResponse> {
    const response = await fetch(`${this.baseUrl}/data-sources/${dataSourceId}/decision`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, notes })
    });
    return response.json();
  }
}
```

## Migration Guide

### Database Migration

1. **Run migrations** to create new tables:
   ```bash
   alembic upgrade 2025_07_18_planning_phase
   ```

2. **Drop legacy tables** (after data migration if needed):
   ```bash
   alembic upgrade 2025_07_18_drop_legacy_planning_tables
   ```

### Code Migration

1. **Update imports** from legacy models to unified models:
   ```typescript
   // Old
   import { CycleReportAttributesPlanning } from '../models/legacy';
   
   // New  
   import { PlanningAttribute } from '../models/planning';
   ```

2. **Update API calls** to use new endpoints:
   ```typescript
   // Old
   GET /api/v1/planning/attributes
   
   // New
   GET /api/v1/planning-unified/versions/{versionId}/attributes
   ```

3. **Update data structures** for new architecture:
   ```typescript
   // Old: Attribute-level data sources
   interface LegacyAttribute {
     id: number;
     data_source_id: number;
     // ...
   }
   
   // New: Phase-level data sources with PDE mappings
   interface PlanningAttribute {
     attribute_id: string;
     version_id: string;
     pde_mappings: PlanningPDEMapping[];
     // ...
   }
   ```

## Auto-Approval Rules

The system includes intelligent auto-approval for low-risk PDE mappings:

### Criteria for Auto-Approval

1. **LLM Confidence Score** ≥ 0.85
2. **Public Information Classification**
3. **Primary Key Attributes**
4. **Risk Score** ≤ 5 (on 0-10 scale)

### Risk Score Calculation

- **Risk Level**: High (+4), Medium (+2), Low (+1)
- **Criticality**: High (+3), Medium (+2), Low (+1)  
- **Information Security**: Restricted (+3), Confidential (+2), Internal (+1), Public (+0)

## Error Handling

### Common Error Responses

```json
{
  "error": "ValidationException",
  "message": "Can only add attributes to draft versions",
  "details": {
    "field": "version_status",
    "current_value": "approved"
  },
  "timestamp": "2025-07-18T10:00:00Z"
}
```

### Error Types

- `ValidationException`: Input validation errors
- `NotFoundException`: Resource not found
- `ConflictError`: Duplicate data or state conflicts
- `BusinessLogicException`: Business rule violations

## Testing

### Unit Tests

Run syntax validation:
```bash
python3 test_planning_syntax.py
```

### Integration Tests

The API includes comprehensive test coverage in:
- `tests/test_planning_unified.py` - Service layer tests
- `tests/test_planning_unified_api.py` - API endpoint tests

### Health Check

```http
GET /planning-unified/health
```

Returns system health and version information.

## Performance Considerations

### Optimizations

1. **Database Indexes**: All foreign keys and frequently queried fields are indexed
2. **UUID Performance**: Uses `gen_random_uuid()` for better distribution
3. **JSONB Queries**: Efficient storage and querying of metadata
4. **Batch Operations**: Bulk decision APIs reduce database round trips

### Monitoring

- Track completion percentages per version
- Monitor auto-approval rates
- Alert on approval bottlenecks
- Dashboard performance metrics

## Security

### Authentication

All endpoints require valid user authentication via JWT tokens.

### Authorization

Granular permissions for planning operations:
- `planning_version_create`
- `planning_data_source_decision`
- `planning_attribute_decision`  
- `planning_pde_mapping_decision`
- `planning_dashboard_read`

### Data Protection

- Sensitive connection configs encrypted at rest
- Audit trails for all decisions
- Role-based access controls
- Secure credential handling