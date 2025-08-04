# Planning Phase Implementation Plan (Corrected)

## 📋 Executive Summary

This document outlines the comprehensive implementation plan for the new simplified Planning Phase system in SynapseDTE. The plan involves migrating from 7+ legacy tables to a clean **4-table architecture** that properly addresses the requirements for phase-level data sources, multiple PDE mappings per attribute, and tester-only approval workflow.

## 🎯 Objectives

1. **Simplify Database Architecture**: Reduce from 7+ tables to 4 core tables
2. **Eliminate Redundancy**: Consolidate multiple overlapping planning systems
3. **Improve Performance**: Eliminate complex joins and optimize queries
4. **Maintain Functionality**: Preserve all planning capabilities including multi-PDE mapping and LLM assistance
5. **Ensure Proper Architecture**: Phase-level data sources and separate PDE mappings table
6. **Reduce Technical Debt**: Simplify codebase and maintenance overhead

## 🏗️ Database Design

### Current State Analysis

#### Legacy Tables to be Consolidated
- `cycle_report_planning_attributes` → `cycle_report_planning_attributes` (enhanced with tester decisions)
- `cycle_report_planning_attribute_version_history` → eliminated (use versions pattern)
- `cycle_report_planning_data_sources` → `cycle_report_planning_data_sources` (kept as separate table for phase-level management)
- `cycle_report_planning_pde_mappings` → `cycle_report_planning_pde_mappings` (kept as separate table with tester decisions)
- `cycle_report_planning_pde_classifications` → `cycle_report_planning_pde_mappings.classification` (embedded JSON)
- `cycle_report_planning_pde_mapping_reviews` → `cycle_report_planning_pde_mappings.tester_decision` (embedded fields)
- `cycle_report_planning_pde_mapping_review_history` → eliminated (use existing audit infrastructure)
- `cycle_report_planning_pde_mapping_approval_rules` → eliminated (use application logic)

**Impact**: 7-8 tables → 4 tables (50% reduction)

#### Key Design Changes Based on Requirements

1. **Phase-Level Data Sources**: Separate `data_sources` table for multiple data sources per phase
2. **Multiple PDEs per Attribute**: Separate `pde_mappings` table supporting multiple PDE mappings per attribute
3. **Consolidated PDE Classification**: Classification data embedded within each PDE mapping (no separate table)
4. **Embedded Tester Decisions**: Tester decisions embedded in both attributes and PDE mappings (no separate review table)
5. **No Report Owner Review**: Planning phase uses only tester approval workflow
6. **Auto-Approval Rules**: Moved to application logic with configurable parameters

### New Simplified Architecture

#### 1. `cycle_report_planning_versions`
- **Purpose**: Version management and planning metadata
- **Key Features**: 
  - Version lifecycle management (draft → pending_approval → approved/rejected → superseded)
  - Temporal workflow integration
  - Planning summary statistics
  - Tester-only approval workflow (no report owner review)

#### 2. `cycle_report_planning_data_sources`
- **Purpose**: Phase-level data source definitions (supports multiple data sources per phase)
- **Key Features**:
  - Multiple data sources per planning phase
  - Connection configuration and credentials
  - Data source validation and testing
  - Tester approval for each data source

#### 3. `cycle_report_planning_attributes`
- **Purpose**: Individual planning attributes with basic metadata
- **Key Features**:
  - Attribute definitions and characteristics
  - LLM assistance metadata (embedded JSON)
  - Tester decision workflow (no report owner review)
  - Single record per attribute per version

#### 4. `cycle_report_planning_pde_mappings`
- **Purpose**: PDE mappings for attributes (supports multiple PDEs per attribute)
- **Key Features**:
  - Multiple PDE mappings per attribute
  - Data source, table, and column information
  - PDE classification (embedded JSON)
  - Tester decision workflow for each PDE mapping
  - LLM assistance and auto-approval support

## 🔄 Implementation Details

### Database Schema

#### Complete Schema Definitions
```sql
-- Table 1: Planning Version Management
CREATE TABLE cycle_report_planning_versions (
    -- Primary Key
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Phase Integration (only phase_id needed)
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    workflow_activity_id INTEGER REFERENCES workflow_activities(activity_id),
    
    -- Version Management (similar to other phases)
    version_number INTEGER NOT NULL,
    version_status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (version_status IN ('draft', 'pending_approval', 'approved', 'rejected', 'superseded')),
    parent_version_id UUID REFERENCES cycle_report_planning_versions(version_id),
    
    -- Temporal Workflow Context
    workflow_execution_id VARCHAR(255),
    workflow_run_id VARCHAR(255),
    
    -- Planning Summary Statistics
    total_attributes INTEGER DEFAULT 0,
    approved_attributes INTEGER DEFAULT 0,
    pk_attributes INTEGER DEFAULT 0,
    cde_attributes INTEGER DEFAULT 0,
    mandatory_attributes INTEGER DEFAULT 0,
    total_data_sources INTEGER DEFAULT 0,
    approved_data_sources INTEGER DEFAULT 0,
    total_pde_mappings INTEGER DEFAULT 0,
    approved_pde_mappings INTEGER DEFAULT 0,
    
    -- LLM Generation Summary
    llm_generation_summary JSONB,
    
    -- Tester-Only Approval Workflow (no report owner)
    submitted_by_id INTEGER REFERENCES users(user_id),
    submitted_at TIMESTAMP WITH TIME ZONE,
    approved_by_id INTEGER REFERENCES users(user_id),
    approved_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(phase_id, version_number)
);

-- Table 2: Phase-Level Data Sources (Multiple per Phase)
CREATE TABLE cycle_report_planning_data_sources (
    -- Primary Key
    data_source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Version Reference
    version_id UUID NOT NULL REFERENCES cycle_report_planning_versions(version_id) ON DELETE CASCADE,
    
    -- Phase Integration
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Data Source Definition
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('database', 'file', 'api', 'sftp', 's3', 'other')),
    description TEXT,
    
    -- Connection Configuration
    connection_config JSONB NOT NULL,
    /* Example structure:
    {
        "host": "database.company.com",
        "port": 5432,
        "database": "financial_data",
        "schema": "transactions",
        "connection_type": "postgresql",
        "ssl_enabled": true,
        "connection_pool_size": 10
    }
    */
    
    -- Authentication Configuration
    auth_config JSONB,
    /* Example structure:
    {
        "auth_type": "username_password",
        "username": "service_account",
        "password_secret_key": "db_password_secret",
        "additional_params": {...}
    }
    */
    
    -- Data Source Metadata
    refresh_schedule VARCHAR(100),
    validation_rules JSONB,
    estimated_record_count INTEGER,
    data_freshness_hours INTEGER,
    
    -- Tester Decision for Data Source
    tester_decision VARCHAR(50) CHECK (tester_decision IN ('approve', 'reject', 'request_changes')),
    tester_decided_by INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    tester_notes TEXT,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(version_id, source_name)
);

-- Table 3: Individual Planning Attributes
CREATE TABLE cycle_report_planning_attributes (
    -- Primary Key
    attribute_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Version Reference
    version_id UUID NOT NULL REFERENCES cycle_report_planning_versions(version_id) ON DELETE CASCADE,
    
    -- Phase Integration
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- Attribute Definition
    attribute_name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL CHECK (data_type IN ('string', 'integer', 'decimal', 'boolean', 'date', 'datetime', 'text')),
    description TEXT,
    business_definition TEXT,
    
    -- Attribute Characteristics
    is_mandatory BOOLEAN DEFAULT FALSE,
    is_cde BOOLEAN DEFAULT FALSE,
    is_primary_key BOOLEAN DEFAULT FALSE,
    max_length INTEGER,
    
    -- Information Security Classification
    information_security_classification VARCHAR(50) DEFAULT 'internal' CHECK (information_security_classification IN ('public', 'internal', 'confidential', 'restricted')),
    
    -- LLM Assistance Metadata (embedded JSON)
    llm_metadata JSONB,
    /* Example structure:
    {
        "provider": "openai",
        "model": "gpt-4",
        "attribute_generated": true,
        "confidence_score": 0.92,
        "generation_rationale": "Based on regulatory requirements and industry standards",
        "suggested_characteristics": {
            "is_mandatory": true,
            "is_cde": false,
            "data_type": "decimal",
            "max_length": 15
        }
    }
    */
    
    -- Tester Decision for Attribute (no report owner)
    tester_decision VARCHAR(50) CHECK (tester_decision IN ('approve', 'reject', 'request_changes')),
    tester_decided_by INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    tester_notes TEXT,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(version_id, attribute_name)
);

-- Table 4: PDE Mappings (Multiple per Attribute)
CREATE TABLE cycle_report_planning_pde_mappings (
    -- Primary Key
    pde_mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Version and Attribute References
    version_id UUID NOT NULL REFERENCES cycle_report_planning_versions(version_id) ON DELETE CASCADE,
    attribute_id UUID NOT NULL REFERENCES cycle_report_planning_attributes(attribute_id) ON DELETE CASCADE,
    data_source_id UUID NOT NULL REFERENCES cycle_report_planning_data_sources(data_source_id),
    
    -- Phase Integration
    phase_id INTEGER NOT NULL REFERENCES workflow_phases(phase_id),
    
    -- PDE Definition
    pde_name VARCHAR(255) NOT NULL,
    pde_code VARCHAR(100) NOT NULL,
    mapping_type VARCHAR(50) NOT NULL DEFAULT 'direct' CHECK (mapping_type IN ('direct', 'calculated', 'lookup', 'conditional')),
    
    -- Data Source Mapping
    source_table VARCHAR(255) NOT NULL,
    source_column VARCHAR(255) NOT NULL,
    source_field VARCHAR(500) NOT NULL, -- Full field path: schema.table.column
    column_data_type VARCHAR(100),
    transformation_rule TEXT,
    condition_rule TEXT, -- For conditional mappings
    is_primary BOOLEAN DEFAULT FALSE,
    
    -- PDE Classification (embedded JSON)
    classification JSONB,
    /* Example structure:
    {
        "criticality": "high",
        "risk_level": "medium",
        "information_security": "confidential",
        "regulatory_flag": true,
        "pii_flag": false,
        "data_category": "financial_data",
        "evidence_type": "regulatory_mapping",
        "evidence_reference": "Basel III requirements"
    }
    */
    
    -- LLM Assistance for this specific mapping
    llm_metadata JSONB,
    /* Example structure:
    {
        "confidence_score": 0.95,
        "generated_by": "gpt-4",
        "rationale": "Direct mapping based on regulatory requirements",
        "alternative_mappings": [
            {
                "source_field": "schema.accounting.transaction_amt",
                "confidence_score": 0.85,
                "notes": "Alternative source in accounting system"
            }
        ]
    }
    */
    
    -- Tester Decision for PDE Mapping (no report owner)
    tester_decision VARCHAR(50) CHECK (tester_decision IN ('approve', 'reject', 'request_changes')),
    tester_decided_by INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    tester_notes TEXT,
    auto_approved BOOLEAN DEFAULT FALSE,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(version_id, attribute_id, pde_code)
);

-- Indexes for Performance
CREATE INDEX idx_cycle_report_planning_versions_phase ON cycle_report_planning_versions(phase_id);
CREATE INDEX idx_cycle_report_planning_versions_status ON cycle_report_planning_versions(version_status);
CREATE INDEX idx_cycle_report_planning_versions_parent ON cycle_report_planning_versions(parent_version_id);

CREATE INDEX idx_cycle_report_planning_data_sources_version ON cycle_report_planning_data_sources(version_id);
CREATE INDEX idx_cycle_report_planning_data_sources_phase ON cycle_report_planning_data_sources(phase_id);
CREATE INDEX idx_cycle_report_planning_data_sources_status ON cycle_report_planning_data_sources(status);
CREATE INDEX idx_cycle_report_planning_data_sources_type ON cycle_report_planning_data_sources(source_type);

CREATE INDEX idx_cycle_report_planning_attributes_version ON cycle_report_planning_attributes(version_id);
CREATE INDEX idx_cycle_report_planning_attributes_phase ON cycle_report_planning_attributes(phase_id);
CREATE INDEX idx_cycle_report_planning_attributes_status ON cycle_report_planning_attributes(status);
CREATE INDEX idx_cycle_report_planning_attributes_cde ON cycle_report_planning_attributes(is_cde);
CREATE INDEX idx_cycle_report_planning_attributes_pk ON cycle_report_planning_attributes(is_primary_key);

CREATE INDEX idx_cycle_report_planning_pde_mappings_version ON cycle_report_planning_pde_mappings(version_id);
CREATE INDEX idx_cycle_report_planning_pde_mappings_attribute ON cycle_report_planning_pde_mappings(attribute_id);
CREATE INDEX idx_cycle_report_planning_pde_mappings_data_source ON cycle_report_planning_pde_mappings(data_source_id);
CREATE INDEX idx_cycle_report_planning_pde_mappings_phase ON cycle_report_planning_pde_mappings(phase_id);
CREATE INDEX idx_cycle_report_planning_pde_mappings_status ON cycle_report_planning_pde_mappings(status);
CREATE INDEX idx_cycle_report_planning_pde_mappings_code ON cycle_report_planning_pde_mappings(pde_code);
```

## Service Layer Implementation

### Unified Planning Service
```python
# app/services/planning_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.planning import (
    PlanningVersion, 
    PlanningDataSource,
    PlanningAttribute,
    PlanningPDEMapping,
    VersionStatus
)
from app.core.database import get_async_session
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.tasks.planning_tasks import generate_planning_attributes_task


class PlanningService:
    """Service for managing planning attributes, data sources, and PDE mappings"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    # Version Management
    async def create_version(
        self, 
        phase_id: int,
        created_by: int,
        version_description: Optional[str] = None
    ) -> PlanningVersion:
        """Create a new planning version"""
        
        # Check if draft version already exists
        existing_draft = await self.db.execute(
            select(PlanningVersion)
            .where(
                and_(
                    PlanningVersion.phase_id == phase_id,
                    PlanningVersion.version_status == VersionStatus.DRAFT
                )
            )
        )
        
        if existing_draft.scalar_one_or_none():
            raise ValidationError("A draft version already exists for this phase")
        
        version = PlanningVersion(
            phase_id=phase_id,
            version_number=1,  # Will be auto-calculated
            version_status=VersionStatus.DRAFT,
            created_by_id=created_by
        )
        
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        
        return version
    
    # Data Source Management
    async def add_data_source(
        self,
        version_id: str,
        data_source_data: Dict[str, Any],
        created_by: int
    ) -> PlanningDataSource:
        """Add a data source to a version"""
        
        # Verify version exists and is editable
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Can only add data sources to draft versions")
        
        data_source = PlanningDataSource(
            version_id=version_id,
            phase_id=version.phase_id,
            source_name=data_source_data["source_name"],
            source_type=data_source_data["source_type"],
            description=data_source_data.get("description"),
            connection_config=data_source_data["connection_config"],
            auth_config=data_source_data.get("auth_config"),
            refresh_schedule=data_source_data.get("refresh_schedule"),
            validation_rules=data_source_data.get("validation_rules"),
            estimated_record_count=data_source_data.get("estimated_record_count"),
            data_freshness_hours=data_source_data.get("data_freshness_hours"),
            status='pending',
            created_by_id=created_by
        )
        
        self.db.add(data_source)
        await self.db.commit()
        await self.db.refresh(data_source)
        
        # Update version summary
        await self.update_version_summary(version_id)
        
        return data_source
    
    async def update_data_source_tester_decision(
        self, 
        data_source_id: str, 
        decision: str,
        notes: Optional[str],
        user_id: int
    ) -> PlanningDataSource:
        """Update tester decision on a data source"""
        
        data_source = await self._get_data_source_by_id(data_source_id)
        
        # Verify version is editable
        version = await self._get_version_by_id(data_source.version_id)
        if version.version_status not in [VersionStatus.DRAFT, VersionStatus.PENDING_APPROVAL]:
            raise ValidationError("Cannot update decisions on finalized versions")
        
        data_source.tester_decision = decision
        data_source.tester_notes = notes
        data_source.tester_decided_by = user_id
        data_source.tester_decided_at = datetime.utcnow()
        
        # Update status based on decision
        if decision == 'approve':
            data_source.status = 'approved'
        elif decision == 'reject':
            data_source.status = 'rejected'
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(data_source.version_id)
        
        return data_source
    
    # Attribute Management
    async def add_attribute(
        self,
        version_id: str,
        attribute_data: Dict[str, Any],
        created_by: int
    ) -> PlanningAttribute:
        """Add a planning attribute to a version"""
        
        # Verify version exists and is editable
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Can only add attributes to draft versions")
        
        attribute = PlanningAttribute(
            version_id=version_id,
            phase_id=version.phase_id,
            attribute_name=attribute_data["attribute_name"],
            data_type=attribute_data["data_type"],
            description=attribute_data.get("description"),
            business_definition=attribute_data.get("business_definition"),
            is_mandatory=attribute_data.get("is_mandatory", False),
            is_cde=attribute_data.get("is_cde", False),
            is_primary_key=attribute_data.get("is_primary_key", False),
            max_length=attribute_data.get("max_length"),
            information_security_classification=attribute_data.get("information_security_classification", "internal"),
            llm_metadata=attribute_data.get("llm_metadata"),
            status='pending',
            created_by_id=created_by
        )
        
        self.db.add(attribute)
        await self.db.commit()
        await self.db.refresh(attribute)
        
        # Update version summary
        await self.update_version_summary(version_id)
        
        return attribute
    
    async def update_attribute_tester_decision(
        self, 
        attribute_id: str, 
        decision: str,
        notes: Optional[str],
        user_id: int
    ) -> PlanningAttribute:
        """Update tester decision on a planning attribute"""
        
        attribute = await self._get_attribute_by_id(attribute_id)
        
        # Verify version is editable
        version = await self._get_version_by_id(attribute.version_id)
        if version.version_status not in [VersionStatus.DRAFT, VersionStatus.PENDING_APPROVAL]:
            raise ValidationError("Cannot update decisions on finalized versions")
        
        attribute.tester_decision = decision
        attribute.tester_notes = notes
        attribute.tester_decided_by = user_id
        attribute.tester_decided_at = datetime.utcnow()
        
        # Update status based on decision
        if decision == 'approve':
            attribute.status = 'approved'
        elif decision == 'reject':
            attribute.status = 'rejected'
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(attribute.version_id)
        
        return attribute
    
    # PDE Mapping Management
    async def add_pde_mapping(
        self,
        attribute_id: str,
        data_source_id: str,
        pde_mapping_data: Dict[str, Any],
        user_id: int
    ) -> PlanningPDEMapping:
        """Add a PDE mapping to an attribute"""
        
        attribute = await self._get_attribute_by_id(attribute_id)
        
        # Verify version is editable
        version = await self._get_version_by_id(attribute.version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Can only add PDE mappings to draft versions")
        
        # Verify data source exists
        data_source = await self._get_data_source_by_id(data_source_id)
        if data_source.version_id != attribute.version_id:
            raise ValidationError("Data source must be from the same version")
        
        # Check if PDE code already exists for this attribute
        existing_pde = await self.db.execute(
            select(PlanningPDEMapping)
            .where(
                and_(
                    PlanningPDEMapping.attribute_id == attribute_id,
                    PlanningPDEMapping.pde_code == pde_mapping_data.get("pde_code")
                )
            )
        )
        
        if existing_pde.scalar_one_or_none():
            raise ValidationError(f"PDE code {pde_mapping_data.get('pde_code')} already exists for this attribute")
        
        # Create new PDE mapping
        pde_mapping = PlanningPDEMapping(
            version_id=attribute.version_id,
            attribute_id=attribute_id,
            data_source_id=data_source_id,
            phase_id=attribute.phase_id,
            pde_name=pde_mapping_data.get("pde_name"),
            pde_code=pde_mapping_data.get("pde_code"),
            mapping_type=pde_mapping_data.get("mapping_type", "direct"),
            source_table=pde_mapping_data.get("source_table"),
            source_column=pde_mapping_data.get("source_column"),
            source_field=pde_mapping_data.get("source_field"),
            column_data_type=pde_mapping_data.get("column_data_type"),
            transformation_rule=pde_mapping_data.get("transformation_rule"),
            condition_rule=pde_mapping_data.get("condition_rule"),
            is_primary=pde_mapping_data.get("is_primary", False),
            classification=pde_mapping_data.get("classification", {}),
            llm_metadata=pde_mapping_data.get("llm_metadata", {}),
            status='pending',
            created_by_id=user_id
        )
        
        # Check for auto-approval
        if self._should_auto_approve(pde_mapping_data):
            pde_mapping.tester_decision = "approve"
            pde_mapping.tester_decided_by = user_id
            pde_mapping.tester_decided_at = datetime.utcnow()
            pde_mapping.tester_notes = "Auto-approved based on approval rules"
            pde_mapping.auto_approved = True
            pde_mapping.status = 'approved'
        
        self.db.add(pde_mapping)
        await self.db.commit()
        await self.db.refresh(pde_mapping)
        
        # Update version summary
        await self.update_version_summary(attribute.version_id)
        
        return pde_mapping
    
    async def update_pde_mapping_tester_decision(
        self, 
        pde_mapping_id: str, 
        decision: str,
        notes: Optional[str],
        user_id: int
    ) -> PlanningPDEMapping:
        """Update tester decision on a PDE mapping"""
        
        pde_mapping = await self._get_pde_mapping_by_id(pde_mapping_id)
        
        # Verify version is editable
        version = await self._get_version_by_id(pde_mapping.version_id)
        if version.version_status not in [VersionStatus.DRAFT, VersionStatus.PENDING_APPROVAL]:
            raise ValidationError("Cannot update decisions on finalized versions")
        
        pde_mapping.tester_decision = decision
        pde_mapping.tester_notes = notes
        pde_mapping.tester_decided_by = user_id
        pde_mapping.tester_decided_at = datetime.utcnow()
        
        # Update status based on decision
        if decision == 'approve':
            pde_mapping.status = 'approved'
        elif decision == 'reject':
            pde_mapping.status = 'rejected'
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(pde_mapping.version_id)
        
        return pde_mapping
    
    # Version Management
    async def submit_for_approval(
        self, 
        version_id: str, 
        submitted_by: int
    ) -> PlanningVersion:
        """Submit planning version for tester approval"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Only draft versions can be submitted for approval")
        
        # Check if all components have been reviewed
        pending_data_sources = await self.db.execute(
            select(PlanningDataSource)
            .where(
                and_(
                    PlanningDataSource.version_id == version_id,
                    PlanningDataSource.tester_decision.is_(None)
                )
            )
        )
        
        pending_attributes = await self.db.execute(
            select(PlanningAttribute)
            .where(
                and_(
                    PlanningAttribute.version_id == version_id,
                    PlanningAttribute.tester_decision.is_(None)
                )
            )
        )
        
        pending_pde_mappings = await self.db.execute(
            select(PlanningPDEMapping)
            .where(
                and_(
                    PlanningPDEMapping.version_id == version_id,
                    PlanningPDEMapping.tester_decision.is_(None)
                )
            )
        )
        
        if (pending_data_sources.scalar_one_or_none() or 
            pending_attributes.scalar_one_or_none() or 
            pending_pde_mappings.scalar_one_or_none()):
            raise ValidationError("All components must have tester decisions before submission")
        
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.submitted_by_id = submitted_by
        version.submitted_at = datetime.utcnow()
        
        await self.db.commit()
        return version
    
    async def approve_version(
        self, 
        version_id: str, 
        approved_by: int
    ) -> PlanningVersion:
        """Approve planning version (tester action)"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.PENDING_APPROVAL:
            raise ValidationError("Only pending approval versions can be approved")
        
        # Mark previous versions as superseded
        await self.db.execute(
            update(PlanningVersion)
            .where(PlanningVersion.phase_id == version.phase_id)
            .where(PlanningVersion.version_status == VersionStatus.APPROVED)
            .values(version_status=VersionStatus.SUPERSEDED)
        )
        
        # Approve current version
        version.version_status = VersionStatus.APPROVED
        version.approved_by_id = approved_by
        version.approved_at = datetime.utcnow()
        
        await self.db.commit()
        return version
    
    # Helper Methods
    def _should_auto_approve(self, pde_mapping_data: Dict[str, Any]) -> bool:
        """Check if PDE mapping should be auto-approved based on rules"""
        
        # Auto-approval rules (configurable)
        auto_approval_rules = {
            "min_llm_confidence": 0.85,
            "auto_approve_cde": True,
            "auto_approve_primary_key": True,
            "auto_approve_public_classification": True,
            "max_risk_score_for_auto_approval": 5
        }
        
        # Check LLM confidence
        llm_confidence = pde_mapping_data.get("llm_metadata", {}).get("confidence_score", 0)
        if llm_confidence < auto_approval_rules["min_llm_confidence"]:
            return False
        
        # Check classification-based rules
        classification = pde_mapping_data.get("classification", {})
        
        # Auto-approve public classification
        if (auto_approval_rules["auto_approve_public_classification"] and 
            classification.get("information_security") == "public"):
            return True
        
        # Auto-approve primary keys
        if (auto_approval_rules["auto_approve_primary_key"] and 
            pde_mapping_data.get("is_primary", False)):
            return True
        
        # Check risk score
        risk_score = self._calculate_risk_score(classification)
        if risk_score <= auto_approval_rules["max_risk_score_for_auto_approval"]:
            return True
        
        return False
    
    def _calculate_risk_score(self, classification: Dict[str, Any]) -> int:
        """Calculate risk score for PDE mapping (0-10 scale)"""
        
        risk_score = 0
        
        # Risk level contribution
        risk_level = classification.get("risk_level", "medium")
        if risk_level == "high":
            risk_score += 4
        elif risk_level == "medium":
            risk_score += 2
        elif risk_level == "low":
            risk_score += 1
        
        # Criticality contribution
        criticality = classification.get("criticality", "medium")
        if criticality == "high":
            risk_score += 3
        elif criticality == "medium":
            risk_score += 2
        elif criticality == "low":
            risk_score += 1
        
        # Information security contribution
        info_security = classification.get("information_security", "internal")
        if info_security == "restricted":
            risk_score += 3
        elif info_security == "confidential":
            risk_score += 2
        elif info_security == "internal":
            risk_score += 1
        elif info_security == "public":
            risk_score += 0
        
        return min(risk_score, 10)  # Cap at 10
    
    async def update_version_summary(self, version_id: str):
        """Update version summary statistics"""
        
        # Get counts from each table
        data_sources = await self.db.execute(
            select(PlanningDataSource)
            .where(PlanningDataSource.version_id == version_id)
        )
        data_sources = data_sources.scalars().all()
        
        attributes = await self.db.execute(
            select(PlanningAttribute)
            .where(PlanningAttribute.version_id == version_id)
        )
        attributes = attributes.scalars().all()
        
        pde_mappings = await self.db.execute(
            select(PlanningPDEMapping)
            .where(PlanningPDEMapping.version_id == version_id)
        )
        pde_mappings = pde_mappings.scalars().all()
        
        # Update version summary
        version = await self._get_version_by_id(version_id)
        version.total_data_sources = len(data_sources)
        version.approved_data_sources = sum(1 for ds in data_sources if ds.status == 'approved')
        version.total_attributes = len(attributes)
        version.approved_attributes = sum(1 for attr in attributes if attr.status == 'approved')
        version.pk_attributes = sum(1 for attr in attributes if attr.is_primary_key)
        version.cde_attributes = sum(1 for attr in attributes if attr.is_cde)
        version.mandatory_attributes = sum(1 for attr in attributes if attr.is_mandatory)
        version.total_pde_mappings = len(pde_mappings)
        version.approved_pde_mappings = sum(1 for pde in pde_mappings if pde.status == 'approved')
        
        await self.db.commit()
    
    async def _get_version_by_id(self, version_id: str) -> PlanningVersion:
        """Get version by ID with error handling"""
        result = await self.db.execute(
            select(PlanningVersion)
            .where(PlanningVersion.version_id == version_id)
        )
        version = result.scalar_one_or_none()
        if not version:
            raise ResourceNotFoundError(f"Version {version_id} not found")
        return version
    
    async def _get_data_source_by_id(self, data_source_id: str) -> PlanningDataSource:
        """Get data source by ID with error handling"""
        result = await self.db.execute(
            select(PlanningDataSource)
            .where(PlanningDataSource.data_source_id == data_source_id)
        )
        data_source = result.scalar_one_or_none()
        if not data_source:
            raise ResourceNotFoundError(f"Data source {data_source_id} not found")
        return data_source
    
    async def _get_attribute_by_id(self, attribute_id: str) -> PlanningAttribute:
        """Get attribute by ID with error handling"""
        result = await self.db.execute(
            select(PlanningAttribute)
            .where(PlanningAttribute.attribute_id == attribute_id)
        )
        attribute = result.scalar_one_or_none()
        if not attribute:
            raise ResourceNotFoundError(f"Attribute {attribute_id} not found")
        return attribute
    
    async def _get_pde_mapping_by_id(self, pde_mapping_id: str) -> PlanningPDEMapping:
        """Get PDE mapping by ID with error handling"""
        result = await self.db.execute(
            select(PlanningPDEMapping)
            .where(PlanningPDEMapping.pde_mapping_id == pde_mapping_id)
        )
        pde_mapping = result.scalar_one_or_none()
        if not pde_mapping:
            raise ResourceNotFoundError(f"PDE mapping {pde_mapping_id} not found")
        return pde_mapping
```

## 📋 Summary

This corrected implementation plan properly addresses all the user's requirements:

### ✅ **Key Requirements Addressed**

1. **Phase-Level Data Sources**: Separate `cycle_report_planning_data_sources` table supports multiple data sources per phase
2. **Multiple PDEs per Attribute**: Separate `cycle_report_planning_pde_mappings` table supports multiple PDE mappings per attribute 
3. **No Report Owner Review**: Planning phase uses only tester approval workflow
4. **Tester Decisions**: Both attributes and PDE mappings include tester decision fields
5. **PDE Classification**: Combined with PDE mapping (no separate table)
6. **Auto-Approval Rules**: Implemented in application logic with configurable parameters

### 🏗️ **Architecture Benefits**

- **50% reduction** in table count (7-8 → 4 tables)
- **Proper separation of concerns** between data sources, attributes, and PDE mappings
- **Scalable design** supporting multiple PDEs per attribute and multiple data sources per phase
- **Consistent tester approval workflow** across all components
- **Enhanced performance** with proper indexing and optimized queries

### 🔄 **Migration Impact**

The migration consolidates the complex planning phase architecture into a clean, maintainable system while preserving all existing functionality and supporting the specific requirements for regulatory compliance and PDE mapping workflows.

---

**Location**: `/Users/dineshpatel/code/projects/SynapseDTE/docs/planning_phase_implementation_plan_corrected.md`