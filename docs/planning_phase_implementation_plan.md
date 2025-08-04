# Planning Phase Implementation Plan

## 📋 Executive Summary

This document outlines the comprehensive implementation plan for the new simplified Planning Phase system in SynapseDTE. The plan involves migrating from 7+ legacy tables to a clean 2-table architecture that follows the exact same pattern as sample selection, scoping, and data profiling, eliminating significant redundancy while maintaining all critical functionality for attribute planning, PDE mapping, and LLM-assisted data source configuration.

## 🎯 Objectives

1. **Simplify Database Architecture**: Reduce from 7+ tables to 3 core tables
2. **Eliminate Redundancy**: Consolidate multiple overlapping planning systems
3. **Improve Performance**: Eliminate complex joins and optimize queries
4. **Maintain Functionality**: Preserve all planning capabilities including multi-PDE mapping and LLM assistance
5. **Ensure Consistency**: Follow similar patterns as other phases with planning-specific adaptations
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

**Impact**: 7-8 tables → 3 tables (62% reduction)

#### Key Design Changes Based on Requirements Analysis

1. **Phase-Level Data Sources**: Separate `data_sources` table for multiple data sources per phase
2. **Multiple PDEs per Attribute**: Separate `pde_mappings` table supporting multiple PDE mappings per attribute
3. **Consolidated PDE Classification**: Classification data embedded within each PDE mapping (no separate table)
4. **Embedded Tester Decisions**: Tester decisions embedded in both attributes and PDE mappings (no separate review table)
5. **No Report Owner Review**: Planning phase uses only tester approval workflow
6. **Auto-Approval Rules**: Moved to application logic with configurable parameters

### New Simplified Architecture

#### 1. `cycle_report_planning_versions`
- **Purpose**: Version management and planning metadata (similar to other phases)
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
    
    -- Version Management (exact same as other phases)
    version_number INTEGER NOT NULL,
    version_status VARCHAR(50) NOT NULL DEFAULT 'draft' CHECK (version_status IN ('draft', 'pending_approval', 'approved', 'rejected', 'superseded')),
    parent_version_id UUID REFERENCES cycle_report_planning_versions(version_id),
    
    -- Temporal Workflow Context
    workflow_execution_id VARCHAR(255),
    workflow_run_id VARCHAR(255),
    
    -- Planning Summary
    total_attributes INTEGER DEFAULT 0,
    approved_attributes INTEGER DEFAULT 0,
    pk_attributes INTEGER DEFAULT 0,
    cde_attributes INTEGER DEFAULT 0,
    mandatory_attributes INTEGER DEFAULT 0,
    
    -- Data Source Configuration (embedded JSON)
    data_source_config JSONB,
    
    -- LLM Generation Summary
    llm_generation_summary JSONB,
    
    -- Approval Workflow
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

-- Table 2: Individual Planning Attributes
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
    
    -- Data Source Mapping (embedded JSON)
    data_source_mapping JSONB,
    /* Example structure:
    {
        "source_name": "Financial_Database",
        "source_type": "database",
        "source_table": "customer_transactions",
        "source_column": "transaction_amount",
        "transformation_rule": "CAST(amount AS DECIMAL(15,2))",
        "connection_config": {...}
    }
    */
    
    -- PDE Mappings (embedded JSON array - supports multiple PDEs per attribute)
    pde_mappings JSONB,
    /* Example structure:
    [
        {
            "pde_name": "Transaction Amount",
            "pde_code": "TXN_AMT_001",
            "mapping_type": "direct",
            "source_field": "schema.transactions.amount",
            "source_table": "transactions",
            "source_column": "amount",
            "column_data_type": "DECIMAL(15,2)",
            "transformation_rule": "CAST(amount AS DECIMAL(15,2))",
            "is_primary": true,
            
            // Combined PDE Classification (no separate table needed)
            "classification": {
                "criticality": "high",
                "risk_level": "medium",
                "information_security": "confidential",
                "regulatory_flag": true,
                "pii_flag": false,
                "data_category": "financial_data",
                "evidence_type": "regulatory_mapping",
                "evidence_reference": "Basel III requirements"
            },
            
            // LLM Assistance for this specific mapping
            "llm_metadata": {
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
            },
            
            // Tester decision for this specific PDE mapping (no separate review table)
            "tester_decision": {
                "decision": "approve",
                "decided_by": 123,
                "decided_at": "2024-01-15T10:30:00Z",
                "notes": "Verified mapping against source system",
                "auto_approved": false
            },
            
            // Report owner decision for this specific PDE mapping
            "report_owner_decision": {
                "decision": "approve", 
                "decided_by": 456,
                "decided_at": "2024-01-15T14:20:00Z",
                "notes": "Approved for regulatory compliance"
            }
        },
        {
            "pde_name": "Transaction Amount Backup",
            "pde_code": "TXN_AMT_002", 
            "mapping_type": "conditional",
            "source_field": "schema.backup.txn_amount",
            "condition": "WHEN primary_amount IS NULL",
            "is_primary": false,
            "classification": {
                "criticality": "medium",
                "risk_level": "low",
                "information_security": "confidential",
                "regulatory_flag": true
            },
            "tester_decision": {
                "decision": "approve",
                "decided_by": 123,
                "decided_at": "2024-01-15T10:35:00Z",
                "notes": "Backup mapping for data quality",
                "auto_approved": true
            }
        }
    ]
    */
    
    -- LLM Assistance Metadata (embedded JSON)
    llm_metadata JSONB,
    /* Example structure:
    {
        "provider": "openai",
        "model": "gpt-4",
        "generated_mapping": true,
        "confidence_score": 0.95,
        "suggested_transformations": [...],
        "regulatory_recommendations": [...],
        "rationale": "Based on regulatory requirements...",
        "auto_approved": false
    }
    */
    
    -- Dual Decision Model (same as other phases)
    tester_decision VARCHAR(50) CHECK (tester_decision IN ('approve', 'reject', 'request_changes')),
    tester_decided_by INTEGER REFERENCES users(user_id),
    tester_decided_at TIMESTAMP WITH TIME ZONE,
    tester_notes TEXT,
    
    report_owner_decision VARCHAR(50) CHECK (report_owner_decision IN ('approve', 'reject', 'request_changes')),
    report_owner_decided_by INTEGER REFERENCES users(user_id),
    report_owner_decided_at TIMESTAMP WITH TIME ZONE,
    report_owner_notes TEXT,
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'submitted', 'approved', 'rejected')),
    
    -- Audit Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER NOT NULL REFERENCES users(user_id),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by_id INTEGER NOT NULL REFERENCES users(user_id),
    
    -- Constraints
    UNIQUE(version_id, attribute_name)
);

-- Indexes for Performance
CREATE INDEX idx_cycle_report_planning_versions_phase ON cycle_report_planning_versions(phase_id);
CREATE INDEX idx_cycle_report_planning_versions_status ON cycle_report_planning_versions(version_status);
CREATE INDEX idx_cycle_report_planning_versions_parent ON cycle_report_planning_versions(parent_version_id);

CREATE INDEX idx_cycle_report_planning_attributes_version ON cycle_report_planning_attributes(version_id);
CREATE INDEX idx_cycle_report_planning_attributes_phase ON cycle_report_planning_attributes(phase_id);
CREATE INDEX idx_cycle_report_planning_attributes_status ON cycle_report_planning_attributes(status);
CREATE INDEX idx_cycle_report_planning_attributes_cde ON cycle_report_planning_attributes(is_cde);
CREATE INDEX idx_cycle_report_planning_attributes_pk ON cycle_report_planning_attributes(is_primary_key);
```

### Data Consolidation Strategy
```python
async def migrate_planning_data():
    """Consolidate data from 7+ tables into unified 2-table structure"""
    
    # 1. Create versions from existing planning contexts
    async for phase in get_planning_phases():
        # Get existing attributes for this phase
        existing_attrs = await get_planning_attributes_for_phase(phase.phase_id)
        existing_data_sources = await get_data_sources_for_phase(phase.phase_id)
        
        if not existing_attrs:
            continue
            
        # Create new version
        new_version = PlanningVersion(
            phase_id=phase.phase_id,
            version_number=1,  # Start fresh
            version_status='approved',  # Assume existing data is approved
            data_source_config={
                "sources": [
                    {
                        "name": ds.name,
                        "type": ds.source_type,
                        "connection_config": ds.connection_config,
                        "auth_config": ds.auth_config,
                        "refresh_schedule": ds.refresh_schedule,
                        "validation_rules": ds.validation_rules
                    }
                    for ds in existing_data_sources
                ]
            },
            total_attributes=len(existing_attrs),
            approved_attributes=sum(1 for attr in existing_attrs if attr.status == 'approved'),
            pk_attributes=sum(1 for attr in existing_attrs if attr.is_primary_key),
            cde_attributes=sum(1 for attr in existing_attrs if attr.is_cde),
            mandatory_attributes=sum(1 for attr in existing_attrs if attr.is_mandatory),
            created_by_id=phase.created_by_id,
            created_at=phase.created_at
        )
        
        await db.add(new_version)
        await db.flush()  # Get version_id
        
        # 2. Migrate attributes with comprehensive metadata
        for old_attr in existing_attrs:
            # Get related data
            old_pde_mapping = await get_pde_mapping_for_attribute(old_attr.id)
            old_pde_classification = await get_pde_classification_for_mapping(old_pde_mapping.id) if old_pde_mapping else None
            old_reviews = await get_reviews_for_pde_mapping(old_pde_mapping.id) if old_pde_mapping else []
            
            # Build data source mapping
            data_source_mapping = None
            if old_attr.data_source_name:
                data_source_mapping = {
                    "source_name": old_attr.data_source_name,
                    "source_type": "database",  # Default assumption
                    "source_table": old_attr.source_table,
                    "source_column": old_attr.source_column,
                    "transformation_rule": old_attr.transformation_rule if hasattr(old_attr, 'transformation_rule') else None
                }
            
            # Build PDE mapping
            pde_mapping = None
            if old_pde_mapping:
                pde_mapping = {
                    "pde_name": old_pde_mapping.pde_name,
                    "pde_code": old_pde_mapping.pde_code,
                    "mapping_type": old_pde_mapping.mapping_type,
                    "criticality": old_pde_mapping.criticality,
                    "risk_level": old_pde_mapping.risk_level,
                    "regulatory_flag": old_pde_mapping.regulatory_flag,
                    "classification": {
                        "type": old_pde_classification.classification_type if old_pde_classification else None,
                        "value": old_pde_classification.classification_value if old_pde_classification else None,
                        "evidence_type": old_pde_classification.evidence_type if old_pde_classification else None,
                        "evidence_reference": old_pde_classification.evidence_reference if old_pde_classification else None
                    } if old_pde_classification else None
                }
            
            # Build LLM metadata
            llm_metadata = None
            if old_pde_mapping and old_pde_mapping.llm_suggested_mapping:
                llm_metadata = {
                    "provider": "openai",  # Default assumption
                    "model": "gpt-4",
                    "generated_mapping": True,
                    "confidence_score": old_pde_mapping.llm_confidence_score,
                    "suggested_transformations": old_pde_mapping.llm_suggested_mapping,
                    "auto_approved": any(review.auto_approved for review in old_reviews)
                }
            
            # Determine decisions from reviews
            tester_decision = None
            report_owner_decision = None
            if old_reviews:
                latest_review = max(old_reviews, key=lambda r: r.created_at)
                if latest_review.review_status == 'approved':
                    tester_decision = 'approve'
                    report_owner_decision = 'approve'
                elif latest_review.review_status == 'rejected':
                    tester_decision = 'reject'
                    report_owner_decision = 'reject'
            
            # Create new attribute
            new_attr = PlanningAttribute(
                version_id=new_version.version_id,
                phase_id=phase.phase_id,
                attribute_name=old_attr.attribute_name,
                data_type=old_attr.data_type,
                description=old_attr.description,
                business_definition=old_attr.business_definition if hasattr(old_attr, 'business_definition') else None,
                is_mandatory=old_attr.is_mandatory,
                is_cde=old_attr.is_cde,
                is_primary_key=old_attr.is_primary_key,
                max_length=old_attr.max_length if hasattr(old_attr, 'max_length') else None,
                information_security_classification=old_attr.information_security_classification,
                data_source_mapping=data_source_mapping,
                pde_mapping=pde_mapping,
                llm_metadata=llm_metadata,
                tester_decision=tester_decision,
                report_owner_decision=report_owner_decision,
                status='approved' if old_attr.status == 'approved' else 'pending',
                created_by_id=old_attr.created_by_id,
                created_at=old_attr.created_at
            )
            
            await db.add(new_attr)
        
        # Update version summary
        await update_version_summary(new_version.version_id)
    
    await db.commit()
```

### Model Implementation

#### Planning Version Model
```python
class PlanningVersion(VersionedEntity):
    __tablename__ = 'cycle_report_planning_versions'
    
    version_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    workflow_activity_id = Column(Integer, ForeignKey('workflow_activities.activity_id'))
    
    # Version Management (exact same as other phases)
    version_number = Column(Integer, nullable=False)
    version_status = Column(Enum(VersionStatus), default=VersionStatus.DRAFT)
    parent_version_id = Column(UUID, ForeignKey('cycle_report_planning_versions.version_id'))
    
    # Temporal Workflow Context
    workflow_execution_id = Column(String(255))
    workflow_run_id = Column(String(255))
    
    # Planning Summary
    total_attributes = Column(Integer, default=0)
    approved_attributes = Column(Integer, default=0)
    pk_attributes = Column(Integer, default=0)
    cde_attributes = Column(Integer, default=0)
    mandatory_attributes = Column(Integer, default=0)
    
    # Data Source Configuration (embedded JSON)
    data_source_config = Column(JSONB)
    
    # LLM Generation Summary
    llm_generation_summary = Column(JSONB)
    
    # Approval Workflow
    submitted_by_id = Column(Integer, ForeignKey('users.user_id'))
    submitted_at = Column(DateTime(timezone=True))
    approved_by_id = Column(Integer, ForeignKey('users.user_id'))
    approved_at = Column(DateTime(timezone=True))
    rejection_reason = Column(Text)
    
    # Relationships
    attributes = relationship("PlanningAttribute", back_populates="version")
    phase = relationship("WorkflowPhase")
    parent_version = relationship("PlanningVersion", remote_side=[version_id])

class PlanningAttribute(CustomPKModel, AuditMixin):
    __tablename__ = 'cycle_report_planning_attributes'
    
    attribute_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID, ForeignKey('cycle_report_planning_versions.version_id'), nullable=False)
    phase_id = Column(Integer, ForeignKey('workflow_phases.phase_id'), nullable=False)
    
    # Attribute Definition
    attribute_name = Column(String(255), nullable=False)
    data_type = Column(String(50), nullable=False)
    description = Column(Text)
    business_definition = Column(Text)
    
    # Attribute Characteristics
    is_mandatory = Column(Boolean, default=False)
    is_cde = Column(Boolean, default=False)
    is_primary_key = Column(Boolean, default=False)
    max_length = Column(Integer)
    
    # Information Security Classification
    information_security_classification = Column(String(50), default='internal')
    
    # Data Source Mapping (embedded JSON)
    data_source_mapping = Column(JSONB)
    
    # PDE Mapping and Classification (embedded JSON)
    pde_mapping = Column(JSONB)
    
    # LLM Assistance Metadata (embedded JSON)
    llm_metadata = Column(JSONB)
    
    # Dual Decision Model (same as other phases)
    tester_decision = Column(String(50))
    tester_decided_by = Column(Integer, ForeignKey('users.user_id'))
    tester_decided_at = Column(DateTime(timezone=True))
    tester_notes = Column(Text)
    
    report_owner_decision = Column(String(50))
    report_owner_decided_by = Column(Integer, ForeignKey('users.user_id'))
    report_owner_decided_at = Column(DateTime(timezone=True))
    report_owner_notes = Column(Text)
    
    # Status
    status = Column(String(50), default='pending')
    
    # Relationships
    version = relationship("PlanningVersion", back_populates="attributes")
    phase = relationship("WorkflowPhase")
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
    PlanningAttribute,
    VersionStatus
)
from app.core.database import get_async_session
from app.core.exceptions import ResourceNotFoundError, ValidationError
from app.tasks.planning_tasks import generate_planning_attributes_task


class PlanningService:
    """Service for managing planning attributes and data source configuration"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def create_version(
        self, 
        phase_id: int,
        data_source_config: Dict[str, Any],
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
            data_source_config=data_source_config,
            created_by_id=created_by
        )
        
        self.db.add(version)
        await self.db.commit()
        await self.db.refresh(version)
        
        return version
    
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
            data_source_mapping=attribute_data.get("data_source_mapping"),
            pde_mapping=attribute_data.get("pde_mapping"),
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
    
    async def generate_attributes_with_llm(
        self,
        version_id: str,
        data_source_config: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Generate planning attributes using LLM in background"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Can only generate attributes for draft versions")
        
        # Start background generation
        task = generate_planning_attributes_task.delay(
            version_id=version_id,
            data_source_config=data_source_config,
            user_id=user_id
        )
        
        return {
            "version_id": version_id,
            "background_job_id": task.id,
            "status": "generation_started"
        }
    
    async def update_tester_decision(
        self, 
        attribute_id: str, 
        decision: str,
        notes: Optional[str],
        user_id: int,
        pde_code: Optional[str] = None
    ) -> PlanningAttribute:
        """Update tester decision on a planning attribute or specific PDE mapping"""
        
        attribute = await self._get_attribute_by_id(attribute_id)
        
        # Verify version is editable
        version = await self._get_version_by_id(attribute.version_id)
        if version.version_status not in [VersionStatus.DRAFT, VersionStatus.PENDING_APPROVAL]:
            raise ValidationError("Cannot update decisions on finalized versions")
        
        if pde_code:
            # Update decision for specific PDE mapping
            pde_mappings = attribute.pde_mappings or []
            updated = False
            
            for pde_mapping in pde_mappings:
                if pde_mapping.get("pde_code") == pde_code:
                    pde_mapping["tester_decision"] = {
                        "decision": decision,
                        "decided_by": user_id,
                        "decided_at": datetime.utcnow().isoformat(),
                        "notes": notes,
                        "auto_approved": self._should_auto_approve(pde_mapping, decision)
                    }
                    updated = True
                    break
            
            if not updated:
                raise ValidationError(f"PDE mapping with code {pde_code} not found")
            
            attribute.pde_mappings = pde_mappings
        else:
            # Update decision for entire attribute (legacy behavior)
            attribute.tester_decision = decision
            attribute.tester_notes = notes
            attribute.tester_decided_by = user_id
            attribute.tester_decided_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(attribute.version_id)
        
        return attribute
    
    async def update_report_owner_decision(
        self, 
        attribute_id: str, 
        decision: str,
        notes: Optional[str],
        user_id: int,
        pde_code: Optional[str] = None
    ) -> PlanningAttribute:
        """Update report owner decision on a planning attribute or specific PDE mapping"""
        
        attribute = await self._get_attribute_by_id(attribute_id)
        
        # Verify version is in pending approval state
        version = await self._get_version_by_id(attribute.version_id)
        if version.version_status != VersionStatus.PENDING_APPROVAL:
            raise ValidationError("Can only make report owner decisions on pending approval versions")
        
        if pde_code:
            # Update decision for specific PDE mapping
            pde_mappings = attribute.pde_mappings or []
            updated = False
            
            for pde_mapping in pde_mappings:
                if pde_mapping.get("pde_code") == pde_code:
                    pde_mapping["report_owner_decision"] = {
                        "decision": decision,
                        "decided_by": user_id,
                        "decided_at": datetime.utcnow().isoformat(),
                        "notes": notes
                    }
                    updated = True
                    break
            
            if not updated:
                raise ValidationError(f"PDE mapping with code {pde_code} not found")
            
            attribute.pde_mappings = pde_mappings
        else:
            # Update decision for entire attribute (legacy behavior)
            attribute.report_owner_decision = decision
            attribute.report_owner_notes = notes
            attribute.report_owner_decided_by = user_id
            attribute.report_owner_decided_at = datetime.utcnow()
        
        # Update attribute status based on decision
        if decision == 'approve':
            attribute.status = 'approved'
        elif decision == 'reject':
            attribute.status = 'rejected'
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(attribute.version_id)
        
        return attribute
    
    async def add_pde_mapping(
        self,
        attribute_id: str,
        pde_mapping_data: Dict[str, Any],
        user_id: int
    ) -> PlanningAttribute:
        """Add a new PDE mapping to an attribute"""
        
        attribute = await self._get_attribute_by_id(attribute_id)
        
        # Verify version is editable
        version = await self._get_version_by_id(attribute.version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Can only add PDE mappings to draft versions")
        
        # Initialize pde_mappings if it doesn't exist
        if not attribute.pde_mappings:
            attribute.pde_mappings = []
        
        # Check if PDE code already exists
        existing_codes = [mapping.get("pde_code") for mapping in attribute.pde_mappings]
        if pde_mapping_data.get("pde_code") in existing_codes:
            raise ValidationError(f"PDE code {pde_mapping_data.get('pde_code')} already exists for this attribute")
        
        # Create new PDE mapping
        new_mapping = {
            "pde_name": pde_mapping_data.get("pde_name"),
            "pde_code": pde_mapping_data.get("pde_code"),
            "mapping_type": pde_mapping_data.get("mapping_type", "direct"),
            "source_field": pde_mapping_data.get("source_field"),
            "source_table": pde_mapping_data.get("source_table"),
            "source_column": pde_mapping_data.get("source_column"),
            "column_data_type": pde_mapping_data.get("column_data_type"),
            "transformation_rule": pde_mapping_data.get("transformation_rule"),
            "is_primary": pde_mapping_data.get("is_primary", False),
            "classification": pde_mapping_data.get("classification", {}),
            "llm_metadata": pde_mapping_data.get("llm_metadata", {}),
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Check for auto-approval
        if self._should_auto_approve(new_mapping, "approve"):
            new_mapping["tester_decision"] = {
                "decision": "approve",
                "decided_by": user_id,
                "decided_at": datetime.utcnow().isoformat(),
                "notes": "Auto-approved based on approval rules",
                "auto_approved": True
            }
        
        attribute.pde_mappings.append(new_mapping)
        
        await self.db.commit()
        
        # Update version summary
        await self.update_version_summary(attribute.version_id)
        
        return attribute
    
    def _should_auto_approve(self, pde_mapping: Dict[str, Any], decision: str) -> bool:
        """Check if PDE mapping should be auto-approved based on rules"""
        
        if decision != "approve":
            return False
        
        # Auto-approval rules (configurable)
        auto_approval_rules = {
            "min_llm_confidence": 0.85,
            "auto_approve_cde": True,
            "auto_approve_primary_key": True,
            "auto_approve_public_classification": True,
            "max_risk_score_for_auto_approval": 5
        }
        
        # Check LLM confidence
        llm_confidence = pde_mapping.get("llm_metadata", {}).get("confidence_score", 0)
        if llm_confidence < auto_approval_rules["min_llm_confidence"]:
            return False
        
        # Check classification-based rules
        classification = pde_mapping.get("classification", {})
        
        # Auto-approve public classification
        if (auto_approval_rules["auto_approve_public_classification"] and 
            classification.get("information_security") == "public"):
            return True
        
        # Auto-approve primary keys
        if (auto_approval_rules["auto_approve_primary_key"] and 
            pde_mapping.get("is_primary", False)):
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
    
    async def submit_for_approval(
        self, 
        version_id: str, 
        submitted_by: int
    ) -> PlanningVersion:
        """Submit planning version for report owner approval"""
        
        version = await self._get_version_by_id(version_id)
        if version.version_status != VersionStatus.DRAFT:
            raise ValidationError("Only draft versions can be submitted for approval")
        
        # Check if all attributes have tester decisions
        attributes = await self.get_attributes_by_version(version_id)
        pending_attributes = [attr for attr in attributes if not attr.tester_decision]
        
        if pending_attributes:
            raise ValidationError(f"{len(pending_attributes)} attributes still need tester decisions")
        
        version.version_status = VersionStatus.PENDING_APPROVAL
        version.submitted_by_id = submitted_by
        version.submitted_at = datetime.utcnow()
        
        # Update all attributes to submitted status
        await self.db.execute(
            update(PlanningAttribute)
            .where(PlanningAttribute.version_id == version_id)
            .values(status='submitted')
        )
        
        await self.db.commit()
        return version
    
    async def approve_version(
        self, 
        version_id: str, 
        approved_by: int
    ) -> PlanningVersion:
        """Approve planning version (report owner action)"""
        
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
    
    async def get_attributes_by_version(self, version_id: str) -> List[PlanningAttribute]:
        """Get all attributes for a version"""
        result = await self.db.execute(
            select(PlanningAttribute)
            .where(PlanningAttribute.version_id == version_id)
            .order_by(PlanningAttribute.attribute_name)
        )
        return result.scalars().all()
    
    async def get_current_version(self, phase_id: int) -> Optional[PlanningVersion]:
        """Get current approved version for a phase"""
        result = await self.db.execute(
            select(PlanningVersion)
            .where(
                and_(
                    PlanningVersion.phase_id == phase_id,
                    PlanningVersion.version_status == VersionStatus.APPROVED
                )
            )
            .order_by(PlanningVersion.version_number.desc())
        )
        return result.scalar_one_or_none()
    
    async def update_version_summary(self, version_id: str):
        """Update version summary statistics"""
        attributes = await self.get_attributes_by_version(version_id)
        
        version = await self._get_version_by_id(version_id)
        version.total_attributes = len(attributes)
        version.approved_attributes = sum(1 for attr in attributes if attr.status == 'approved')
        version.pk_attributes = sum(1 for attr in attributes if attr.is_primary_key)
        version.cde_attributes = sum(1 for attr in attributes if attr.is_cde)
        version.mandatory_attributes = sum(1 for attr in attributes if attr.is_mandatory)
        
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
```

## Background Tasks Implementation

```python
# app/tasks/planning_tasks.py
"""
Planning Background Tasks
Handles long-running planning operations without blocking the UI
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal
from app.services.llm_service import get_llm_service
from app.models.planning import PlanningVersion, PlanningAttribute
from sqlalchemy import select

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def generate_planning_attributes_task(
    self,
    version_id: str,
    data_source_config: Dict[str, Any],
    user_id: int
):
    """
    Generate planning attributes using LLM in background
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            _generate_planning_attributes_async(
                version_id, data_source_config, user_id
            )
        )
        loop.close()
        
        return result
        
    except Exception as exc:
        logger.error(f"Planning attribute generation failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _generate_planning_attributes_async(
    version_id: str,
    data_source_config: Dict[str, Any],
    user_id: int
) -> Dict[str, Any]:
    """Async helper for planning attribute generation"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get version
            version_result = await db.execute(
                select(PlanningVersion)
                .where(PlanningVersion.version_id == version_id)
            )
            version = version_result.scalar_one_or_none()
            
            if not version:
                raise ValueError(f"Version {version_id} not found")
            
            # Get LLM service
            llm_service = get_llm_service()
            
            # Generate attributes using LLM
            llm_result = await llm_service.generate_planning_attributes(
                data_source_config=data_source_config,
                regulatory_context=data_source_config.get("regulatory_context"),
                report_type=data_source_config.get("report_type")
            )
            
            generated_attributes = []
            
            # Create attribute records
            for attr_data in llm_result.get("attributes", []):
                attribute = PlanningAttribute(
                    version_id=version_id,
                    phase_id=version.phase_id,
                    attribute_name=attr_data.get("name"),
                    data_type=attr_data.get("data_type"),
                    description=attr_data.get("description"),
                    business_definition=attr_data.get("business_definition"),
                    is_mandatory=attr_data.get("is_mandatory", False),
                    is_cde=attr_data.get("is_cde", False),
                    is_primary_key=attr_data.get("is_primary_key", False),
                    max_length=attr_data.get("max_length"),
                    information_security_classification=attr_data.get("information_security_classification", "internal"),
                    data_source_mapping=attr_data.get("data_source_mapping"),
                    pde_mapping=attr_data.get("pde_mapping"),
                    llm_metadata={
                        "provider": llm_result.get("model_provider"),
                        "model": llm_result.get("model_used"),
                        "generated_mapping": True,
                        "confidence_score": attr_data.get("confidence_score"),
                        "rationale": attr_data.get("rationale"),
                        "regulatory_recommendations": attr_data.get("regulatory_recommendations", [])
                    },
                    status='pending',
                    created_by_id=user_id
                )
                
                db.add(attribute)
                generated_attributes.append(attribute)
            
            # Commit all attributes
            await db.commit()
            
            # Update version summary
            version.total_attributes = len(generated_attributes)
            version.llm_generation_summary = {
                "attributes_generated": len(generated_attributes),
                "model_used": llm_result.get("model_used"),
                "total_tokens": llm_result.get("total_tokens"),
                "generation_time_ms": llm_result.get("generation_time_ms"),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            await db.commit()
            
            return {
                "status": "success",
                "version_id": version_id,
                "attributes_generated": len(generated_attributes),
                "task_id": self.request.id
            }
            
        except Exception as e:
            logger.error(f"Error in planning attribute generation: {str(e)}")
            raise
```

## API Endpoints

```python
# app/api/v1/endpoints/planning.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.services.planning_service import PlanningService
from app.schemas.planning import (
    PlanningVersionResponse,
    PlanningAttributeResponse,
    CreatePlanningVersionRequest,
    CreatePlanningAttributeRequest,
    UpdateTesterDecisionRequest,
    UpdateReportOwnerDecisionRequest
)
from app.core.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/planning/versions", response_model=PlanningVersionResponse)
async def create_planning_version(
    request: CreatePlanningVersionRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Create initial planning version"""
    service = PlanningService(db)
    return await service.create_version(
        phase_id=request.phase_id,
        data_source_config=request.data_source_config,
        created_by=current_user.user_id
    )


@router.get("/planning/versions/{version_id}", response_model=PlanningVersionResponse)
async def get_planning_version(
    version_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get specific planning version with all attributes"""
    service = PlanningService(db)
    return await service.get_version_by_id(version_id)


@router.post("/planning/versions/{version_id}/attributes", response_model=PlanningAttributeResponse)
async def add_planning_attribute(
    version_id: str,
    request: CreatePlanningAttributeRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Add planning attribute to version"""
    service = PlanningService(db)
    return await service.add_attribute(
        version_id=version_id,
        attribute_data=request.dict(),
        created_by=current_user.user_id
    )


@router.post("/planning/versions/{version_id}/generate-attributes")
async def generate_planning_attributes(
    version_id: str,
    data_source_config: dict,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Generate planning attributes using LLM"""
    service = PlanningService(db)
    return await service.generate_attributes_with_llm(
        version_id=version_id,
        data_source_config=data_source_config,
        user_id=current_user.user_id
    )


@router.put("/planning/attributes/{attribute_id}/tester-decision", response_model=PlanningAttributeResponse)
async def update_tester_decision(
    attribute_id: str,
    request: UpdateTesterDecisionRequest,
    pde_code: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Update tester decision on planning attribute or specific PDE mapping"""
    service = PlanningService(db)
    return await service.update_tester_decision(
        attribute_id=attribute_id,
        decision=request.decision,
        notes=request.notes,
        user_id=current_user.user_id,
        pde_code=pde_code
    )


@router.put("/planning/attributes/{attribute_id}/report-owner-decision", response_model=PlanningAttributeResponse)
async def update_report_owner_decision(
    attribute_id: str,
    request: UpdateReportOwnerDecisionRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Update report owner decision on planning attribute"""
    service = PlanningService(db)
    return await service.update_report_owner_decision(
        attribute_id=attribute_id,
        decision=request.decision,
        notes=request.notes,
        user_id=current_user.user_id
    )


@router.post("/planning/versions/{version_id}/submit", response_model=PlanningVersionResponse)
async def submit_version_for_approval(
    version_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Submit planning version for report owner approval"""
    service = PlanningService(db)
    return await service.submit_for_approval(
        version_id=version_id,
        submitted_by=current_user.user_id
    )


@router.post("/planning/versions/{version_id}/approve", response_model=PlanningVersionResponse)
async def approve_version(
    version_id: str,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Approve planning version (report owner action)"""
    service = PlanningService(db)
    return await service.approve_version(
        version_id=version_id,
        approved_by=current_user.user_id
    )


@router.get("/planning/phases/{phase_id}/current", response_model=PlanningVersionResponse)
async def get_current_planning_version(
    phase_id: int,
    db: AsyncSession = Depends(get_async_session)
):
    """Get current approved planning version for a phase"""
    service = PlanningService(db)
    return await service.get_current_version(phase_id)


@router.get("/planning/versions/{version_id}/attributes", response_model=List[PlanningAttributeResponse])
async def get_planning_attributes(
    version_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get all planning attributes for a version"""
    service = PlanningService(db)
    return await service.get_attributes_by_version(version_id)
```

## 📅 Implementation Timeline

### Phase 1: Foundation (Week 1-2)
- [ ] Create database migration scripts
- [ ] Implement new table schemas
- [ ] Create SQLAlchemy models
- [ ] Set up basic unit tests
- [ ] Create JSON schema validation

### Phase 2: Data Migration (Week 3-4)
- [ ] Implement data consolidation logic
- [ ] Create migration scripts with rollback capability
- [ ] Test migration on staging environment
- [ ] Validate data integrity post-migration
- [ ] Create backup and restore procedures

### Phase 3: Service Layer (Week 5-6)
- [ ] Implement unified planning service
- [ ] Create attribute management service
- [ ] Build LLM integration service
- [ ] Implement background task processing
- [ ] Create data access layer

### Phase 4: API Layer (Week 7-8)
- [ ] Update existing API endpoints
- [ ] Create new simplified endpoints
- [ ] Implement request/response schemas
- [ ] Add authentication and authorization
- [ ] Update API documentation

### Phase 5: Frontend Integration (Week 9-10)
- [ ] Update React components
- [ ] Simplify data fetching logic
- [ ] Update state management
- [ ] Implement new UI workflows
- [ ] Update approval interfaces

### Phase 6: Testing & Validation (Week 11-12)
- [ ] Comprehensive testing
- [ ] Performance validation
- [ ] User acceptance testing
- [ ] Bug fixes and optimization
- [ ] Load testing and monitoring

## 🎯 Success Metrics

### Technical Metrics
- [ ] Database query performance improvement (target: 85% faster)
- [ ] Storage space reduction (target: 75% less space)
- [ ] Code complexity reduction (target: 80% fewer lines)
- [ ] Migration success rate (target: 100% data integrity)

### Business Metrics
- [ ] User adoption rate (target: 90% within 2 weeks)
- [ ] Planning workflow efficiency (target: 60% faster completion)
- [ ] Error rate reduction (target: 70% fewer support tickets)
- [ ] System reliability (target: 99.9% uptime)

## 📋 Summary

This implementation plan provides a comprehensive blueprint for simplifying the Planning Phase system from 7-8 tables to 2 tables (75% reduction) while maintaining all functionality through strategic use of JSON fields and the dual decision model. The plan ensures perfect consistency with the patterns successfully implemented in sample selection, scoping, and data profiling phases.

**Key Benefits:**
- **Architectural Consistency**: Same 2-table pattern across all phases
- **Reduced Complexity**: 75% fewer tables to manage
- **Enhanced Performance**: Fewer JOINs and better query optimization
- **Improved Maintainability**: Consistent patterns and reduced technical debt
- **Better Workflow Integration**: Native temporal workflow support

The simplified architecture maintains all critical functionality including PDE mapping, LLM assistance, data source configuration, and the dual decision model while significantly reducing complexity and improving system maintainability.

---

*This implementation plan serves as a comprehensive guide for the Planning Phase system consolidation, focusing on reducing complexity by 75% while maintaining all critical functionality and ensuring perfect alignment with established patterns.*