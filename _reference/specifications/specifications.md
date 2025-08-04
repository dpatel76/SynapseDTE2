# End-to-End Data Testing System - Functional & Design Specifications

## 1. Executive Summary

The End-to-End Data Testing System is a comprehensive full-stack Python application designed to manage the complete lifecycle of regulatory and risk management report testing. The system supports six distinct roles through a structured workflow encompassing planning, scoping, sampling, data provider coordination, testing execution, and observation management.

## 2. System Architecture

### 2.1 High-Level Architecture
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

### 2.2 Technology Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL 14+
- **Frontend**: React 18+ or Vue 3+
- **Authentication**: JWT with role-based access control
- **File Storage**: Local filesystem with versioning
- **LLM Integration**: Claude API, Gemini API with provider switching
- **Email Service**: SMTP integration for notifications
- **Task Queue**: Celery with Redis for background tasks

## 3. User Roles and Permissions

### 3.1 Role Definitions

| Role | Primary Responsibilities | Access Level |
|------|-------------------------|--------------|
| **Tester** | Execute testing workflow steps, manage attributes, conduct testing | Report-level assignment |
| **Test Manager** | Create test cycles, assign reports, monitor team progress | Read-only aggregated view of team testing |
| **Report Owner** | Approve scoping, sampling, and observations | Own reports across multiple LOBs |
| **Report Owner Executive** | Portfolio oversight, executive reporting | View all reports under their report owners |
| **Data Provider** | Provide source documents, confirm data sources | Attribute-level assignments |
| **CDO** | Assign data providers, manage escalations | LOB-level assignment (one per LOB) |

### 3.2 Permission Matrix

| Action | Tester | Test Manager | Report Owner | Report Owner Executive | Data Provider | CDO |
|--------|--------|--------------|--------------|----------------------|---------------|-----|
| Create Test Cycle | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Assign Reports to Cycle | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Assign Testers to Reports | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Execute Planning Phase | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Upload Planning Documents | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Generate LLM Attribute Lists | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Modify Attribute Lists | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Complete Planning Phase | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Execute Scoping Phase | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Generate LLM Scoping Recommendations | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Accept/Decline Scoping Recommendations | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Submit Scoping for Approval | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve/Decline Scoping | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Execute Data Provider Identification | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Assign LOBs to Attributes | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Assign Data Providers to Attributes | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Generate Escalation Emails | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Execute Sample Selection | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Generate LLM Samples | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Upload Sample Files | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Submit Samples for Approval | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve/Decline Samples | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Upload Source Documents | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Provide Data Source Information | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Submit Information to Tester | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Execute Testing | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Submit Test Results to Data Provider | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Review Test Results | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Accept/Reject Test Results | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Create Observations | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Submit Observations for Approval | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve/Decline Observations | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Override Observations to Non-Issue | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| View Team Progress | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| View Own Reports Progress | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| View Portfolio Reports | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| View Assigned Attributes | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| View LOB Data Provider Assignments | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

## 4. Data Model

### 4.1 Core Entities

#### 4.1.1 User Management
```sql
-- Lines of Business
CREATE TABLE lobs (
    lob_id SERIAL PRIMARY KEY,
    lob_name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Management
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL CHECK (role IN ('Tester', 'Test Manager', 'Report Owner', 'Report Owner Executive', 'Data Provider', 'CDO')),
    lob_id INTEGER REFERENCES lobs(lob_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Report Owner to Executive Mapping
CREATE TABLE report_owner_executives (
    executive_id INTEGER REFERENCES users(user_id),
    report_owner_id INTEGER REFERENCES users(user_id),
    PRIMARY KEY (executive_id, report_owner_id)
);
```

#### 4.1.2 Report Management
```sql
-- Report Inventory
CREATE TABLE reports (
    report_id SERIAL PRIMARY KEY,
    report_name VARCHAR(255) NOT NULL,
    regulation VARCHAR(255),
    report_owner_id INTEGER REFERENCES users(user_id),
    lob_id INTEGER REFERENCES lobs(lob_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data Sources
CREATE TABLE data_sources (
    data_source_id SERIAL PRIMARY KEY,
    data_source_name VARCHAR(255) NOT NULL,
    database_type VARCHAR(50) NOT NULL,
    database_url TEXT NOT NULL,
    database_user VARCHAR(255) NOT NULL,
    database_password_encrypted TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.3 Testing Workflow
```sql
-- Test Cycles
CREATE TABLE test_cycles (
    cycle_id SERIAL PRIMARY KEY,
    cycle_name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    test_manager_id INTEGER REFERENCES users(user_id),
    status VARCHAR(50) DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cycle Reports (Many-to-Many)
CREATE TABLE cycle_reports (
    cycle_id INTEGER REFERENCES test_cycles(cycle_id),
    report_id INTEGER REFERENCES reports(report_id),
    tester_id INTEGER REFERENCES users(user_id),
    status VARCHAR(50) DEFAULT 'Not Started',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    PRIMARY KEY (cycle_id, report_id)
);

-- Report Attributes
CREATE TABLE report_attributes (
    attribute_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    attribute_name VARCHAR(255) NOT NULL,
    description TEXT,
    data_type VARCHAR(50),
    mandatory_flag VARCHAR(20) CHECK (mandatory_flag IN ('Mandatory', 'Conditional', 'Optional')),
    cde_flag BOOLEAN DEFAULT FALSE,
    historical_issues_flag BOOLEAN DEFAULT FALSE,
    is_scoped BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id)
);
```

#### 4.1.4 Workflow Phases
```sql
-- Phase Tracking
CREATE TABLE workflow_phases (
    phase_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    phase_name VARCHAR(50) NOT NULL CHECK (phase_name IN ('Planning', 'Scoping', 'Data Provider ID', 'Sample Selection', 'Request Info', 'Testing', 'Observations')),
    status VARCHAR(50) DEFAULT 'Not Started' CHECK (status IN ('Not Started', 'In Progress', 'Pending Approval', 'Complete')),
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date TIMESTAMP,
    actual_end_date TIMESTAMP,
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id)
);

-- Document Management
CREATE TABLE documents (
    document_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('Regulatory Specification', 'CDE List', 'Historical Issues List', 'Sample File', 'Source Document')),
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    version_number INTEGER DEFAULT 1,
    uploaded_by INTEGER REFERENCES users(user_id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_latest BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id)
);
```

#### 4.1.5 Testing Execution
```sql
-- Sample Data
CREATE TABLE samples (
    sample_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    primary_key_name VARCHAR(100) NOT NULL,
    primary_key_value VARCHAR(255) NOT NULL,
    sample_data JSONB NOT NULL,
    llm_rationale TEXT,
    tester_rationale TEXT,
    status VARCHAR(50) DEFAULT 'Draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id)
);

-- Data Provider Assignments
CREATE TABLE data_provider_assignments (
    assignment_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    attribute_id INTEGER REFERENCES report_attributes(attribute_id),
    lob_id INTEGER REFERENCES lobs(lob_id),
    data_provider_id INTEGER REFERENCES users(user_id),
    assigned_by INTEGER REFERENCES users(user_id),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Assigned',
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id)
);

-- Test Executions
CREATE TABLE test_executions (
    execution_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    sample_id INTEGER REFERENCES samples(sample_id),
    attribute_id INTEGER REFERENCES report_attributes(attribute_id),
    test_run_number INTEGER DEFAULT 1,
    source_value TEXT,
    expected_value TEXT,
    test_result VARCHAR(20) CHECK (test_result IN ('Pass', 'Fail', 'Exception')),
    discrepancy_details TEXT,
    data_source_type VARCHAR(20) CHECK (data_source_type IN ('Document', 'Database')),
    data_source_id INTEGER REFERENCES data_sources(data_source_id),
    document_id INTEGER REFERENCES documents(document_id),
    table_name VARCHAR(255),
    column_name VARCHAR(255),
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_by INTEGER REFERENCES users(user_id),
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id)
);

-- Test Observations
CREATE TABLE observations (
    observation_id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL,
    report_id INTEGER NOT NULL,
    attribute_id INTEGER REFERENCES report_attributes(attribute_id),
    observation_type VARCHAR(50) CHECK (observation_type IN ('Data Quality', 'Documentation')),
    description TEXT NOT NULL,
    impact_level VARCHAR(20) CHECK (impact_level IN ('Low', 'Medium', 'High', 'Critical')),
    samples_impacted INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'Open',
    tester_comments TEXT,
    report_owner_comments TEXT,
    resolution_rationale TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (cycle_id, report_id) REFERENCES cycle_reports(cycle_id, report_id)
);
```

### 4.2 Configuration Tables
```sql
-- SLA Configuration
CREATE TABLE sla_configurations (
    sla_id SERIAL PRIMARY KEY,
    role_transition VARCHAR(100) NOT NULL,
    sla_hours INTEGER NOT NULL DEFAULT 24,
    escalation_level INTEGER DEFAULT 1,
    escalation_to_role VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- LLM Audit Trail
CREATE TABLE llm_audit_log (
    log_id SERIAL PRIMARY KEY,
    cycle_id INTEGER,
    report_id INTEGER,
    llm_provider VARCHAR(50) NOT NULL,
    prompt_template VARCHAR(255) NOT NULL,
    request_payload JSONB NOT NULL,
    response_payload JSONB NOT NULL,
    execution_time_ms INTEGER,
    token_usage JSONB,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_by INTEGER REFERENCES users(user_id)
);

-- System Audit Log
CREATE TABLE audit_log (
    audit_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(255)
);
```

## 5. Testing Workflow - 7-Phase Process

The testing workflow for each report follows a structured 7-phase process. Each phase has specific entry/exit criteria, role responsibilities, and deliverables.

### 5.1 Workflow Overview

```
Report Assignment → 1. Planning → 2. Scoping → 3. Data Provider ID ┐
                                                                    ├→ 5. Request for Info → 6. Testing → 7. Observations
                                            4. Sample Selection ────┘
```

**Key Workflow Rules**:
- Phases 1-2 are sequential and must be completed in order
- Phases 3-4 run in parallel after Phase 2 completion
- Phase 5 can only start after Phase 4 (Sample Selection) is complete
- Phase 5 can begin testing attributes where data providers are identified (Phase 3 not required to be 100% complete)
- Phases 6-7 are sequential
- Each phase has defined start/end dates set during planning

### 5.2 Phase 1: Planning

**Primary Actor**: Tester  
**Prerequisites**: Report assigned to tester in test cycle  
**Objective**: Create comprehensive attribute list for the report

#### 5.2.1 Entry Criteria
- Report assigned to tester in active test cycle
- Tester clicks "Start Testing" button
- System records testing start date

#### 5.2.2 Phase Activities

**Step 1: Document Upload**
- Tester uploads supporting documents:
  - Regulatory Specifications (required)
  - CDE List (optional)
  - Historical Issues Element List (optional)
- System validates file formats (PDF, images)
- Maximum file size: 20MB per document
- System maintains document versions

**Step 2: LLM Attribute Generation**
- System processes regulatory specification using configured LLM provider
- LLM generates attribute list with:
  - Attribute name
  - Description
  - Data type
  - Mandatory/Conditional/Optional flag
- System cross-references against CDE List and Historical Issues List
- Auto-sets CDE Flag if attribute matches CDE List
- Auto-sets Historical Issues Flag if attribute matches Historical Issues List

**Step 3: Manual Attribute Refinement**
- Tester reviews LLM-generated attribute list
- Can add new attributes manually
- Can edit existing attributes (name, description, type, flags)
- Can remove attributes from list
- System tracks all changes with audit trail

#### 5.2.3 Exit Criteria
- All required documents uploaded
- Attribute list finalized (minimum 1 attribute required)
- Tester marks planning phase as complete
- System auto-advances status to "Scoping - In Progress"

#### 5.2.4 Deliverables
- Finalized attribute list with all metadata
- Uploaded regulatory and reference documents
- LLM audit trail for attribute generation

### 5.3 Phase 2: Scoping

**Primary Actor**: Tester, Report Owner  
**Prerequisites**: Planning phase completed  
**Objective**: Determine which attributes require testing based on risk and regulatory requirements

#### 5.3.1 Entry Criteria
- Planning phase marked complete
- Attribute list exists with at least one attribute
- System auto-starts scoping phase

#### 5.3.2 Phase Activities

**Step 1: LLM Scoping Recommendations**
- Tester initiates LLM recommendation generation
- System provides LLM with context:
  - Regulatory specification document
  - Complete attribute list with all flags
  - Historical testing data (if available)
- LLM generates recommendations including:
  - Recommendation score (1-10 scale)
  - Testing recommendation (Test/Skip)
  - Detailed rationale
  - Expected source documents for testing
  - Keywords to search in source documents
  - Other reports that use same attributes
- LLM prioritizes attributes with:
  - CDE Flag = True (highest priority)
  - Historical Issues Flag = True (high priority)
  - Multi-report impact (medium-high priority)

**Step 2: Tester Review and Decision**
- Tester reviews each LLM recommendation
- Makes accept/decline decision for each attribute
- Can override LLM recommendations with justification
- Must record decision for all attributes before proceeding

**Step 3: Report Owner Approval Process**
- Tester submits scoping recommendations to Report Owner
- Report Owner receives notification with summary
- Report Owner reviews:
  - Scoping decisions and rationale
  - Resource impact assessment
  - Risk coverage evaluation
- Report Owner can:
  - Approve scoping recommendations
  - Decline with specific comments
  - Request modifications to specific attributes

**Step 4: Iterative Refinement**
- If declined, tester receives notification with comments
- Tester makes requested changes
- Resubmits for approval
- Process repeats until approval obtained

#### 5.3.3 Exit Criteria
- Report Owner approves scoping recommendations
- System has final list of attributes marked for testing (scoped attributes)
- Tester marks scoping phase as complete
- System triggers parallel phases (Data Provider ID + Sample Selection)

#### 5.3.4 Deliverables
- Final scoped attribute list
- LLM recommendation audit trail
- Report Owner approval documentation
- Testing justification for each scoped attribute

### 5.4 Phase 3: Data Provider Identification (Parallel)

**Primary Actor**: Tester, CDO  
**Prerequisites**: Scoping phase completed  
**Objective**: Identify and assign data providers for each scoped attribute

#### 5.4.1 Entry Criteria
- Scoping phase completed with approved attribute list
- At least one attribute scoped for testing
- System auto-starts phase in parallel with Sample Selection

#### 5.4.2 Phase Activities

**Step 1: LOB Assignment**
- Tester assigns one or more LOBs to each scoped attribute
- System validates LOB assignments
- Can assign multiple LOBs if attribute spans business units

**Step 2: CDO Notification and Assignment**
- System identifies CDOs for assigned LOBs
- Sends notification to relevant CDOs with:
  - Report details
  - Scoped attributes for their LOB
  - Assignment deadline (24-hour SLA)
- System tracks response status per CDO per attribute

**Step 3: Historical Knowledge Application**
- System suggests previous data provider assignments for same report/attribute combinations
- CDO can accept historical assignment or assign new data provider
- System maintains assignment history for future reference

**Step 4: Data Provider Assignment**
- CDO assigns specific data provider for each attribute
- System validates data provider belongs to correct LOB
- CDO can add assignment notes or special instructions

**Step 5: SLA Monitoring and Escalation**
- System tracks 24-hour SLA for each assignment
- Auto-generates escalation emails if SLA breached
- Escalation email goes to Report Owner (CC: CDO)
- Multiple CDO escalations combined in single daily digest
- Tester can manually generate escalation emails for past-due items

#### 5.4.3 Exit Criteria
- All scoped attributes have assigned data providers
- All CDO assignments completed
- System marks phase as complete

#### 5.4.4 Deliverables
- Complete data provider assignment matrix
- Historical assignment knowledge updated
- SLA compliance tracking
- Escalation audit trail

### 5.5 Phase 4: Sample Selection (Parallel)

**Primary Actor**: Tester, Report Owner  
**Prerequisites**: Scoping phase completed  
**Objective**: Generate or define sample data for testing scoped attributes

#### 5.5.1 Entry Criteria
- Scoping phase completed
- Scoped attribute list available
- System auto-starts phase in parallel with Data Provider Identification

#### 5.5.2 Phase Activities

**Step 1: Sample Generation Options**
- **Option A - LLM Generation**:
  - Tester initiates LLM sample generation
  - LLM creates sample data for all scoped attributes
  - LLM provides rationale for sample selection methodology
  - System validates sample completeness
- **Option B - Manual Upload**:
  - Tester uploads sample file (CSV, Excel)
  - System validates file contains all scoped attributes
  - System validates data types and completeness
  - Tester must provide rationale for sample selection

**Step 2: Sample Validation**
- System validates sample data:
  - All scoped attributes have values
  - Data types match attribute definitions
  - Primary key values are present and valid
  - No duplicate primary keys
  - Sample size is adequate for testing

**Step 3: Tester Rationale**
- Tester adds comprehensive rationale for sample selection:
  - Sample selection methodology
  - Coverage justification
  - Risk-based selection criteria
  - Time period coverage

**Step 4: Report Owner Approval Process**
- Tester submits samples and rationale to Report Owner
- Report Owner reviews:
  - Sample adequacy and coverage
  - Selection methodology
  - Risk coverage
  - Resource implications
- Report Owner can:
  - Approve samples
  - Decline with specific feedback
  - Request sample modifications

**Step 5: Iterative Refinement**
- If declined, tester modifies samples per feedback
- Can regenerate using LLM or upload new file
- Must update rationale
- Resubmits for approval until approved

#### 5.5.3 Exit Criteria
- Report Owner approves sample selection
- Sample data validated and stored
- Sample rationale documented
- System marks phase complete and triggers Request for Information

#### 5.5.4 Deliverables
- Validated sample dataset
- Sample selection rationale
- LLM generation audit (if applicable)
- Report Owner approval documentation

### 5.6 Phase 5: Request for Information

**Primary Actor**: Data Provider  
**Prerequisites**: Sample Selection completed, Data providers assigned (can be partial)  
**Objective**: Collect source information for testing from assigned data providers

#### 5.6.1 Entry Criteria
- Sample Selection phase completed
- At least one data provider assigned (can test subset while others pending)
- System auto-starts phase

#### 5.6.2 Phase Activities

**Step 1: Data Provider Notification**
- System notifies assigned data providers
- Notification includes:
  - Report and testing context
  - Assigned attributes for testing
  - Sample data they need to provide information for
  - Submission options and deadlines

**Step 2: Information Submission Options**
- **Option A - Source Document Upload**:
  - Data provider uploads supporting documents (PDF, images)
  - Maximum 20MB per file
  - System maintains document versions
  - Document should contain data for specified sample records
- **Option B - Database Information**:
  - Data provider selects data source from system inventory
  - Provides table name and column name for attribute
  - Specifies query parameters if needed
  - System validates connectivity

**Step 3: Sample-Level Submission**
- Data provider must provide information for each sample record
- Can mix submission types (some samples via documents, others via database)
- Must specify primary key mapping for each sample
- Can add notes or context for specific samples

**Step 4: Submission Tracking**
- System tracks submission status per data provider per attribute per sample
- Real-time progress dashboard for tester
- Automated reminders for pending submissions
- SLA monitoring with escalation capability

**Step 5: Tester Notification**
- System notifies tester as submissions are received
- Tester can begin testing as information becomes available
- No need to wait for all submissions before starting testing

#### 5.6.3 Exit Criteria
- All data providers submit required information for their assigned samples
- System validates submission completeness
- Information ready for testing phase

#### 5.6.4 Deliverables
- Complete source information for all samples
- Document library with version control
- Database query specifications
- Submission audit trail

### 5.7 Phase 6: Testing

**Primary Actor**: Tester, Data Provider, CDO  
**Prerequisites**: Request for Information completed (can be partial)  
**Objective**: Execute testing and validate data accuracy

#### 5.7.1 Entry Criteria
- Sample data available
- Source information provided by data providers
- System ready for test execution

#### 5.7.2 Phase Activities

**Step 1: Test Execution Methods**
- **Document-Based Testing**:
  - System uses LLM to extract attribute values from uploaded documents
  - Uses attribute context from planning phase for extraction
  - Compares extracted value to sample value
  - Records confidence score and extraction details
- **Database-Based Testing**:
  - System connects to specified data source
  - Executes query using table/column information
  - Retrieves actual value for sample record
  - Compares to sample value

**Step 2: Primary Key Validation**
- System validates primary key matching between sample and source
- Ensures testing the correct record (loan ID, account ID, transaction ID, etc.)
- Records any primary key discrepancies

**Step 3: Result Recording**
- System records comprehensive test results:
  - Expected value (from sample)
  - Actual value (from source)
  - Test result (Pass/Fail/Exception)
  - Discrepancy details if failed
  - Extraction confidence (for document-based tests)
  - Test execution timestamp
  - Run number (tracks retests)

**Step 4: Multi-Run Support**
- System tracks all test iterations, not just final results
- Each retest gets new run number
- Maintains history of why retests were needed
- Tracks frequency of retests per data provider

**Step 5: Review Process**
- **Tester to Data Provider Review**:
  - Tester submits test results to data provider
  - Data provider can:
    - Accept results as accurate
    - Provide new/corrected source document
    - Provide updated database information
    - Add explanatory notes
- **Data Provider to CDO Review**:
  - If data provider accepts, results go to CDO
  - CDO can:
    - Approve results
    - Reject with additional notes for tester
    - Request additional documentation
- **Iterative Process**:
  - If new information provided, tester reruns test
  - Process continues until CDO approval obtained
  - System tracks number of iterations per attribute/sample

#### 5.7.3 Exit Criteria
- All sample/attribute combinations tested
- All test results approved by CDOs
- Testing complete for all scoped attributes
- System advances to Observation Management

#### 5.7.4 Deliverables
- Complete test results database
- Multi-run test history
- CDO approval documentation
- Retest frequency metrics

### 5.8 Phase 7: Observation Management

**Primary Actor**: Tester, Report Owner  
**Prerequisites**: Testing phase completed  
**Objective**: Document, categorize, and resolve testing discrepancies

#### 5.8.1 Entry Criteria
- All testing completed for report
- Test results available for analysis
- System auto-starts observation management

#### 5.8.2 Phase Activities

**Step 1: Auto-Detection and Grouping**
- System automatically identifies failed tests
- Groups similar issues using algorithms:
  - Primary grouping: By attribute
  - Secondary grouping: By error pattern
  - Tertiary grouping: By affected samples
- Creates preliminary observations for each unique issue group

**Step 2: Observation Creation**
- System generates observations with:
  - Unique observation ID
  - Affected attribute(s)
  - Issue category (Data Quality vs Documentation)
  - Number of samples impacted
  - Sample IDs and test results
  - Source and target values
  - Initial system-generated description

**Step 3: Tester Review and Refinement**
- Tester reviews auto-generated observations
- Can combine similar observations
- Can split observations into separate issues
- Can create new observations manually
- Adds detailed commentary and analysis
- Categorizes each observation:
  - **Data Quality**: Issues with underlying data
  - **Documentation**: Issues with documentation or specifications

**Step 4: Impact Assessment**
- Tester assesses impact level:
  - Low: Minimal impact, few samples affected
  - Medium: Moderate impact, some samples affected
  - High: Significant impact, many samples affected
  - Critical: Severe impact, fundamental issues
- Documents affected sample count
- Provides remediation recommendations

**Step 5: Report Owner Approval Process**
- Tester submits observations to Report Owner
- Report Owner reviews:
  - Observation accuracy and completeness
  - Impact assessment
  - Categorization appropriateness
  - Remediation recommendations
- Report Owner can:
  - **Approve observations as-is**
  - **Override to non-issue**:
    - Must provide detailed rationale
    - Explains why observation doesn't represent actual issue
    - Tester updates observation status with rationale
    - Resubmits for final approval

**Step 6: Final Resolution**
- Once Report Owner approves all observations
- System marks testing complete for the report
- Generates final testing summary
- Archives all documentation and results

#### 5.8.3 Exit Criteria
- All observations reviewed and approved
- Report Owner final approval obtained
- Testing marked complete for report in test cycle
- Final documentation package created

#### 5.8.4 Deliverables
- Final observation report
- Impact assessment summary
- Resolution documentation
- Complete testing package for regulatory submission

### 5.9 Workflow Monitoring and Controls

#### 5.9.1 Phase Transition Controls
- Each phase has defined entry/exit criteria that must be met
- System enforces sequential completion where required
- Parallel phases can progress independently
- Automatic status updates based on completion criteria

#### 5.9.2 SLA Monitoring
- Each phase has configurable SLA (default 24 hours)
- Real-time SLA tracking with countdown timers
- Automatic escalation when SLA breached
- Management dashboard for SLA compliance

#### 5.9.3 Progress Tracking
- Real-time progress indicators for each phase
- Percentage completion tracking
- Bottleneck identification and alerts
- Resource allocation optimization

#### 5.9.4 Quality Gates
- Validation checkpoints at each phase transition
- Data quality checks before advancing phases
- Approval requirements clearly defined
- Audit trail for all decisions and approvals

## 6. Foundation Data Management

### 6.1 LOB Management
**Functionality**: Create, read, update, delete Lines of Business
**Access**: Administrative users only
**Features**:
- Auto-generated LOB ID
- Unique LOB name validation
- Soft delete capability
- Audit trail of changes

### 6.2 User Management
**Functionality**: Comprehensive user lifecycle management
**Features**:
- Role-based user creation with LOB assignment
- Email uniqueness validation
- Password management with security policies
- User activation/deactivation
- Report Owner to Executive hierarchy mapping

### 6.3 Report Inventory
**Functionality**: Central repository for all reports
**Features**:
- Report metadata management
- Report Owner assignment
- Regulation tagging
- Cross-LOB report ownership capability

### 6.4 Data Source Configuration
**Functionality**: Secure management of external data connections
**Features**:
- Multiple database type support (PostgreSQL, MySQL, Oracle, SQL Server)
- Encrypted credential storage
- Connection testing capability
- Version control for connection strings

## 7. LLM Integration ArchitectureTest Execution Methods**:
   - **Document-based**: LLM extraction + comparison
   - **Database-based**: Direct query + comparison
2. **Primary Key Validation**: Ensure sample identity matching
3. **Result Recording**: Pass/Fail with detailed discrepancies
4. **Multi-run Support**: Track all test iterations
5. **Review Process**:
   - Submit to Data Provider for verification
   - Data Provider can provide new information
   - CDO review and approval
   - Track rerun frequency

**Test Result Structure**:
```json
{
  "test_id": "unique_identifier",
  "sample_id": "sample_reference",
  "attribute": "attribute_name",
  "expected_value": "sample_value",
  "actual_value": "extracted_value",
  "result": "Pass/Fail/Exception",
  "discrepancy_details": "detailed_explanation",
  "extraction_confidence": 0.95,
  "run_number": 1
}
```

#### 5.2.8 Phase 6: Observation Management
**Primary Actor**: Tester, Report Owner
**Functionality**: Manage and resolve testing discrepancies

**Detailed Process**:
1. **Auto-grouping**: System groups similar issues by attribute
2. **Observation Creation**: Generate observations for unique discrepancies
3. **Categorization**: Data Quality vs Documentation issues
4. **Impact Assessment**: Count of affected samples
5. **Tester Review**: Add commentary and rationale
6. **Report Owner Approval**: 
   - Approve as-is
   - Override to non-issue with rationale
7. **Final Approval**: Complete testing for report

**Issue Grouping Logic**:
- Primary: Group by attribute
- Secondary: Group by error pattern
- Manual: Tester can combine or separate

### 5.3 LLM Integration Architecture

#### 5.3.1 Provider Management
**Supported Providers**: Claude, Gemini
**Features**:
- Runtime provider switching
- Provider-specific configuration
- Failover capabilities (future enhancement)
- Cost tracking per provider

#### 5.3.2 Prompt Management
**Architecture**: External prompt files (not embedded in code)
**Structure**:
```
prompts/
├── attribute_generation/
│   ├── claude_prompt.txt
│   └── gemini_prompt.txt
├── scoping_recommendations/
│   ├── claude_prompt.txt
│   └── gemini_prompt.txt
└── document_extraction/
    ├── claude_prompt.txt
    └── gemini_prompt.txt
```

#### 5.3.3 Audit Requirements
**Logging**: Complete request/response audit trail
**Storage**: PostgreSQL JSONB fields
**Retention**: 3 years for compliance
**Access**: Admin-level access for audit review

### 5.4 SLA and Escalation Management

#### 5.4.1 Configurable SLAs
**Default**: 24 hours for all role transitions
**Configuration**: Admin interface for SLA management
**Granularity**: Per role transition globally

**SLA Types**:
- CDO Data Provider Assignment: 24 hours
- Report Owner Approvals: 24 hours
- Data Provider Information Submission: 24 hours
- Custom configurable transitions

#### 5.4.2 Multi-level Escalation
**Level 1**: Role-specific escalation (24 hours)
**Level 2**: Management escalation (48 hours)
**Level 3**: Executive escalation (72 hours)

**Escalation Chain**:
```
CDO → Report Owner → Report Owner Executive
Data Provider → CDO → Report Owner
Tester → Test Manager → Report Owner
```

#### 5.4.3 Notification Management
**Frequency**: Maximum once per day per user
**Aggregation**: Multiple escalations in single email
**Timing**: End-of-day digest
**Content**: Actionable information with direct links

### 5.5 Metrics and Reporting

#### 5.5.1 Role-based Dashboards

**Test Manager Dashboard**:
- Cycle progress overview
- Report status by phase
- Team performance metrics
- SLA compliance rates
- Bottleneck identification

**Report Owner Dashboard**:
- Reports requiring approval
- Testing progress by report
- Historical testing results
- Issue trend analysis
- Approval turnaround times

**Report Owner Executive Dashboard**:
- Portfolio-wide progress
- Cross-LOB performance comparison
- Strategic metrics
- Executive-level KPIs
- Trend analysis across cycles

#### 5.5.2 Key Performance Indicators

**Operational KPIs**:
- Cycle completion rates
- Average time per phase
- SLA compliance percentage
- Issue recurrence rates
- Data provider response times

**Quality KPIs**:
- Test pass/fail rates
- Observation resolution time
- Retest frequency
- Documentation quality scores
- Attribute coverage rates

**Trend Analysis KPIs**:
- Performance improvement over time
- Seasonal patterns
- Resource utilization
- Efficiency gains
- Risk reduction metrics

#### 5.5.3 Historical Data Management
**Retention**: 3 years for trend analysis
**Archival**: Automated data archival process
**Comparison**: Cycle-over-cycle analysis
**Benchmarking**: Industry standard comparisons

## 6. Technical Design Specifications

### 10.1 Security Architecture

#### 10.1.1 Authentication & Authorization
**Method**: JWT-based authentication
**Session Management**: Stateless tokens with refresh capability
**Role-based Access Control**: Fine-grained permissions per role
**Password Policy**: Configurable complexity requirements

#### 10.1.2 Data Encryption
**At Rest**: AES-256 encryption for sensitive data
**In Transit**: TLS 1.3 for all communications
**Database Credentials**: Separate encryption key for data source passwords
**Key Management**: Secure key storage and rotation

#### 10.1.3 Audit Logging
**Scope**: All business process actions
**Storage**: Separate audit database
**Retention**: 7 years for compliance
**Access**: Administrative audit trail review

### 10.2 Scalability Design

#### 10.2.1 Database Architecture
**Primary Database**: PostgreSQL with read replicas
**Connection Pooling**: PgBouncer for connection management
**Indexing Strategy**: Optimized for workflow queries
**Partitioning**: Time-based partitioning for large tables

#### 10.2.2 Application Architecture
**Microservices**: Modular service architecture
**API Gateway**: Centralized routing and rate limiting
**Caching**: Redis for session and frequently accessed data
**Background Tasks**: Celery for asynchronous processing

#### 10.2.3 File Storage
**Local Storage**: Version-controlled file system
**Backup Strategy**: Automated backup and recovery
**Size Limits**: 20MB per file with validation
**Cleanup**: Automated cleanup of old versions

### 10.3 Integration Architecture

#### 10.3.1 External Database Connectivity
**Supported Types**: PostgreSQL, MySQL, Oracle, SQL Server
**Connection Pooling**: Per data source connection management
**Security**: Encrypted credential storage
**Testing**: Connection validation and health checks

#### 10.3.2 Email Integration
**SMTP Configuration**: Configurable email server settings
**Template Management**: HTML email templates
**Delivery Tracking**: Email delivery status monitoring
**Rate Limiting**: Anti-spam protection

#### 10.3.3 LLM Service Integration
**API Management**: RESTful integration with LLM providers
**Rate Limiting**: Provider-specific rate limit handling
**Error Handling**: Graceful degradation and retry logic
**Cost Monitoring**: Usage tracking and budget controls

### 10.4 Performance Specifications

#### 10.4.1 Response Time Requirements
**Interactive Operations**: < 2 seconds
**Report Generation**: < 30 seconds
**LLM Operations**: < 60 seconds
**File Upload**: < 10 seconds for 20MB files

#### 10.4.2 Throughput Requirements
**Concurrent Users**: 100+ simultaneous users
**API Requests**: 1000+ requests per minute
**Database Queries**: Sub-second response for 95% of queries
**File Processing**: 10+ concurrent file uploads

#### 10.4.3 Availability Requirements
**Uptime**: 99.9% availability
**Backup Strategy**: Daily automated backups
**Disaster Recovery**: 4-hour recovery time objective
**Monitoring**: Real-time system health monitoring

## 11. Implementation Roadmap

### 11.1 Phase 1: Foundation (Weeks 1-4)
- Database schema implementation
- User management and authentication
- Basic CRUD operations for foundational data
- Security framework setup

### 11.2 Phase 2: Core Workflow (Weeks 5-12)
- Test cycle management
- Planning and scoping phases
- Basic LLM integration
- File upload and management

### 11.3 Phase 3: Advanced Features (Weeks 13-20)
- Data provider coordination
- Testing execution engine
- Observation management
- SLA monitoring and escalation

### 11.4 Phase 4: Analytics & Optimization (Weeks 21-24)
- Metrics dashboards
- Trend analysis
- Performance optimization
- User acceptance testing

### 11.5 Phase 5: Production Deployment (Weeks 25-28)
- Production environment setup
- Data migration utilities
- Training and documentation
- Go-live support

## 12. Risk Assessment and Mitigation

### 12.1 Technical Risks
**LLM Provider Availability**: Implement multi-provider support
**Database Performance**: Implement read replicas and indexing
**File Storage Limits**: Implement cleanup and archival processes
**Integration Complexity**: Phased integration approach

### 12.2 Business Risks
**User Adoption**: Comprehensive training program
**Data Quality**: Robust validation and testing
**Compliance Requirements**: Regular compliance audits
**Change Management**: Stakeholder engagement throughout

### 12.3 Security Risks
**Data Breach**: Multi-layer security architecture
**Unauthorized Access**: Strong authentication and authorization
**Data Loss**: Comprehensive backup and recovery
**Compliance Violations**: Regular security assessments

## 13. Success Metrics

### 13.1 Implementation Success
- On-time delivery of phases
- Budget adherence
- User acceptance criteria met
- Performance benchmarks achieved

### 13.2 Business Success
- Reduced testing cycle time by 30%
- Improved compliance reporting accuracy
- Enhanced audit trail capability
- Increased user satisfaction scores

### 13.3 Technical Success
- System availability > 99.9%
- Response times within specifications
- Zero critical security vulnerabilities
- Successful integration with all required systems

## 14. Conclusion

This comprehensive specification provides the blueprint for implementing a robust, scalable End-to-End Data Testing System. The design emphasizes security, compliance, and user experience while maintaining flexibility for future enhancements. The phased implementation approach ensures manageable delivery while minimizing risk and maximizing stakeholder value.