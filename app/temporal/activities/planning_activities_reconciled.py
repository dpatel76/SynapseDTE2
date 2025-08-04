"""Planning Phase Activities - Reconciled with all existing steps

These activities match the pre-Temporal workflow exactly:
1. Start Planning Phase
2. Upload Documents (Regulatory Spec, CDE List, Historical Issues)
3. Import/Create Attributes
4. Review Planning Checklist
5. Complete Planning Phase
"""

from temporalio import activity
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import os
import hashlib

from sqlalchemy import select, and_, func
from app.core.database import get_db
from app.services.workflow_orchestrator import get_workflow_orchestrator
from app.models.report import Report
from app.models.cycle_report import CycleReport
from app.models.document import Document
from app.models.report_attribute import ReportAttribute
from app.models.workflow import WorkflowPhase
from app.schemas.planning import DocumentType, ReportAttributeCreate

logger = logging.getLogger(__name__)


@activity.defn
async def start_planning_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int
) -> Dict[str, Any]:
    """Step 1: Start planning phase"""
    try:
        async for db in get_db():
            # Don't need orchestrator for this simple operation
            
            # Start planning phase by creating/updating workflow phase
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
            result = await db.execute(phase_query)
            phase = result.scalar_one_or_none()
            
            if not phase:
                phase = WorkflowPhase(
                    cycle_id=cycle_id,
                    report_id=report_id,
                    phase_name="Planning",
                    status="In Progress",
                    state="In Progress",
                    actual_start_date=datetime.utcnow(),
                    started_by=user_id
                )
                db.add(phase)
            else:
                phase.status = "In Progress"
                phase.state = "In Progress"
                phase.actual_start_date = datetime.utcnow()
                phase.started_by = user_id
            
            await db.commit()
            
            # Initialize planning checklist items
            checklist = [
                {"item": "Upload regulatory specification", "required": True, "completed": False},
                {"item": "Upload CDE list", "required": True, "completed": False},
                {"item": "Upload historical issues list", "required": False, "completed": False},
                {"item": "Import or create attributes", "required": True, "completed": False},
                {"item": "Review and finalize attributes", "required": True, "completed": False}
            ]
            
            logger.info(f"Started planning phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "phase_id": phase.phase_id,
                "data": {
                    "phase_name": phase.phase_name,
                    "state": phase.state,
                    "status": phase.schedule_status,
                    "started_at": phase.actual_start_date.isoformat() if phase.actual_start_date else datetime.utcnow().isoformat(),
                    "checklist": checklist
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to start planning phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def upload_planning_documents_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    document_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 2: Upload planning documents
    
    This is a human-in-the-loop activity that waits for document uploads.
    Documents include:
    - Regulatory Specification (required)
    - CDE List (required)
    - Historical Issues List (optional)
    """
    try:
        async for db in get_db():
            if document_data and document_data.get('documents'):
                # Process uploaded documents
                uploaded_documents = []
                
                for doc in document_data['documents']:
                    # Generate file hash for the document
                    file_content = doc.get('content', '')
                    file_hash = hashlib.sha256(file_content.encode()).hexdigest() if isinstance(file_content, str) else hashlib.sha256(b'').hexdigest()
                    
                    document = Document(
                        cycle_id=cycle_id,
                        report_id=report_id,
                        document_name=doc.get('name', 'Untitled'),
                        document_type=doc.get('type', 'other'),
                        file_path=f"/tmp/{doc.get('name', 'temp')}",  # Temporary path
                        file_size=doc.get('size', 0),
                        mime_type=doc.get('mime_type', 'application/pdf'),
                        uploaded_by_user_id=user_id,
                        file_hash=file_hash,
                        version=1,
                        is_latest_version=True,
                        document_metadata={
                            "phase": "Planning",
                            "uploaded_via": "temporal_workflow"
                        }
                    )
                    db.add(document)
                    uploaded_documents.append({
                        "document_type": doc.get('type', 'other'),
                        "filename": doc.get('name', 'Untitled')
                    })
                
                await db.commit()
                
                # Check which documents have been uploaded
                has_regulatory_spec = any(d['document_type'] in ['regulatory', 'planning'] 
                                        for d in uploaded_documents)
                has_cde_list = any(d['document_type'] in ['cde_list', 'data_elements'] 
                                 for d in uploaded_documents)
                has_historical_issues = any(d['document_type'] in ['historical', 'issues'] 
                                          for d in uploaded_documents)
                
                return {
                    "success": True,
                    "data": {
                        "documents_uploaded": len(uploaded_documents),
                        "uploaded_documents": uploaded_documents,
                        "checklist_status": {
                            "regulatory_specification": has_regulatory_spec,
                            "cde_list": has_cde_list,
                            "historical_issues_list": has_historical_issues
                        },
                        "ready_for_attributes": has_regulatory_spec and has_cde_list
                    }
                }
            else:
                # Check current document status
                result = await db.execute(
                    select(Document).where(
                        and_(
                            Document.cycle_id == cycle_id,
                            Document.report_id == report_id,
                            Document.is_latest_version == True
                        )
                    )
                )
                documents = result.scalars().all()
                
                doc_types = [doc.document_type for doc in documents]
                
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_document_uploads",
                        "message": "Waiting for required documents to be uploaded",
                        "current_documents": doc_types,
                        "missing_required": []
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in document upload: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def import_create_attributes_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    attribute_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 3: Import or create attributes
    
    This activity handles:
    - Importing attributes from data dictionary
    - Creating manual attributes
    - LLM-assisted attribute generation (optional)
    """
    try:
        async for db in get_db():
            if attribute_data:
                created_attributes = []
                
                # Handle different attribute sources
                if attribute_data.get('import_from_dictionary'):
                    # Import from data dictionary
                    dictionary_attributes = attribute_data.get('dictionary_attributes', [])
                    for attr in dictionary_attributes:
                        new_attr = ReportAttribute(
                            cycle_id=cycle_id,
                            report_id=report_id,
                            attribute_name=attr.get('attribute_name'),
                            data_type=attr.get('data_type', 'String'),
                            description=attr.get('description'),
                            cde_flag=attr.get('cde_flag', False),
                            historical_issues_flag=attr.get('historical_issues_flag', False),
                            approval_status='pending',
                            llm_generated=False,
                            version_created_by=user_id
                        )
                        db.add(new_attr)
                        created_attributes.append(new_attr)
                
                if attribute_data.get('manual_attributes'):
                    # Create manual attributes
                    manual_attributes = attribute_data.get('manual_attributes', [])
                    for attr in manual_attributes:
                        new_attr = ReportAttribute(
                            cycle_id=cycle_id,
                            report_id=report_id,
                            attribute_name=attr.get('attribute_name'),
                            data_type=attr.get('data_type', 'String'),
                            description=attr.get('description'),
                            cde_flag=attr.get('cde_flag', False),
                            historical_issues_flag=attr.get('historical_issues_flag', False),
                            approval_status='pending',
                            llm_generated=False,
                            version_created_by=user_id
                        )
                        db.add(new_attr)
                        created_attributes.append(new_attr)
                
                if created_attributes:
                    await db.commit()
                
                # Get current attribute stats
                result = await db.execute(
                    select(ReportAttribute).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id
                        )
                    )
                )
                all_attributes = result.scalars().all()
                
                cde_count = sum(1 for attr in all_attributes if attr.cde_flag)
                historical_count = sum(1 for attr in all_attributes if attr.historical_issues_flag)
                
                return {
                    "success": True,
                    "data": {
                        "attributes_created": len(created_attributes),
                        "total_attributes": len(all_attributes),
                        "cde_attributes": cde_count,
                        "historical_issues_attributes": historical_count,
                        "ready_for_review": len(all_attributes) > 0
                    }
                }
            else:
                # Return current attribute status
                result = await db.execute(
                    select(func.count(ReportAttribute.attribute_id)).where(
                        and_(
                            ReportAttribute.cycle_id == cycle_id,
                            ReportAttribute.report_id == report_id
                        )
                    )
                )
                count = result.scalar()
                
                return {
                    "success": True,
                    "data": {
                        "status": "awaiting_attribute_creation",
                        "message": "Waiting for attributes to be imported or created",
                        "current_attribute_count": count
                    }
                }
                
    except Exception as e:
        logger.error(f"Failed in attribute creation: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def review_planning_checklist_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    checklist_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Step 4: Review planning checklist
    
    Verify all planning requirements are met before completion.
    """
    try:
        async for db in get_db():
            # Check document uploads
            doc_result = await db.execute(
                select(Document.document_type).where(
                    and_(
                        Document.cycle_id == cycle_id,
                        Document.report_id == report_id,
                        Document.is_latest_version == True
                    )
                )
            )
            doc_types = [row[0] for row in doc_result]
            
            has_regulatory_spec = any(dtype in ['regulatory', 'planning', 'regulatory_specification'] for dtype in doc_types)
            has_cde_list = any(dtype in ['cde_list', 'data_elements', 'cde'] for dtype in doc_types)
            has_historical_issues = any(dtype in ['historical', 'issues', 'historical_issues'] for dtype in doc_types)
            
            # Check attributes
            attr_result = await db.execute(
                select(func.count(ReportAttribute.attribute_id)).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id
                    )
                )
            )
            attribute_count = attr_result.scalar()
            
            # Build checklist status
            checklist = {
                "upload_regulatory_specification": {
                    "required": True,
                    "completed": has_regulatory_spec,
                    "status": "complete" if has_regulatory_spec else "pending"
                },
                "upload_cde_list": {
                    "required": True,
                    "completed": has_cde_list,
                    "status": "complete" if has_cde_list else "pending"
                },
                "upload_historical_issues_list": {
                    "required": False,
                    "completed": has_historical_issues,
                    "status": "complete" if has_historical_issues else "optional"
                },
                "create_attributes": {
                    "required": True,
                    "completed": attribute_count > 0,
                    "status": "complete" if attribute_count > 0 else "pending",
                    "details": f"{attribute_count} attributes created"
                }
            }
            
            # Check if all required items are complete
            all_required_complete = all(
                item["completed"] for item in checklist.values() 
                if item["required"]
            )
            
            return {
                "success": True,
                "data": {
                    "checklist": checklist,
                    "all_required_complete": all_required_complete,
                    "can_complete_phase": all_required_complete,
                    "summary": {
                        "documents_uploaded": len(doc_types),
                        "attributes_created": attribute_count
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"Failed in checklist review: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@activity.defn
async def complete_planning_phase_activity(
    cycle_id: int,
    report_id: int,
    user_id: int,
    phase_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Step 5: Complete planning phase and advance to scoping"""
    try:
        async for db in get_db():
            # Verify checklist is complete
            checklist = phase_data.get('checklist', {})
            if not checklist.get('can_complete_phase'):
                raise ValueError("Cannot complete planning phase - checklist requirements not met")
            
            # Get final attribute count
            attr_result = await db.execute(
                select(func.count(ReportAttribute.attribute_id)).where(
                    and_(
                        ReportAttribute.cycle_id == cycle_id,
                        ReportAttribute.report_id == report_id
                    )
                )
            )
            attribute_count = attr_result.scalar()
            
            # Complete planning phase
            phase_query = select(WorkflowPhase).where(
                and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.phase_name == "Planning"
                )
            )
            result = await db.execute(phase_query)
            phase = result.scalar_one_or_none()
            
            if phase:
                phase.state = "Complete"
                phase.status = "Complete"
                phase.actual_end_date = datetime.utcnow()
                phase.completed_by = user_id
                phase.notes = f"Completed with {attribute_count} attributes"
                await db.commit()
            
            # Create scoping phase
            scoping_phase = WorkflowPhase(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_name="Scoping",
                state="Not Started",
                status="pending",
                created_at=datetime.utcnow()
            )
            db.add(scoping_phase)
            await db.commit()
            
            logger.info(f"Completed planning phase for cycle {cycle_id}, report {report_id}")
            
            return {
                "success": True,
                "data": {
                    "phase_name": phase.phase_name,
                    "attribute_count": attribute_count,
                    "completed_at": datetime.utcnow().isoformat(),
                    "next_phase": "Scoping"
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to complete planning phase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }