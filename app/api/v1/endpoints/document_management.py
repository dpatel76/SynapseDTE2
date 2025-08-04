"""
Document Management API Endpoints
RESTful API for document upload, download, versioning, and management
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import io

from app.core.dependencies import get_db, get_current_user
from app.services.document_management_service import create_document_management_service
from app.schemas.document_management import (
    # Request schemas
    DocumentUploadRequest, DocumentUpdateRequest, DocumentSearchRequest, 
    DocumentListRequest, DocumentApprovalRequest, DocumentVersionCreateRequest,
    DocumentVersionRestoreRequest, DocumentVersionCompareRequest,
    DocumentStatisticsRequest, BulkDocumentUploadRequest, BulkDocumentDeleteRequest,
    
    # Response schemas
    DocumentResponse, DocumentListResponse, DocumentSearchResponse,
    DocumentUploadResponse, DocumentUpdateResponse, DocumentDeleteResponse,
    DocumentDownloadResponse, DocumentMetricsResponse, DocumentVersionCreateResponse,
    DocumentVersionListResponse, DocumentVersionRestoreResponse, DocumentVersionCompareResponse,
    BulkOperationResponse, ErrorResponse
)

router = APIRouter(prefix="/documents", tags=["Document Management"])


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    cycle_id: int = Form(...),
    report_id: int = Form(...),
    phase_id: int = Form(...),
    test_case_id: Optional[str] = Form(None),
    document_type: str = Form(...),
    document_title: str = Form(...),
    document_description: Optional[str] = Form(None),
    document_category: str = Form("general"),
    access_level: str = Form("phase_restricted"),
    required_for_completion: bool = Form(False),
    approval_required: bool = Form(False),
    workflow_stage: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload a new document"""
    
    try:
        service = create_document_management_service(db)
        
        # Create file object
        file_obj = io.BytesIO(await file.read())
        
        result = await service.upload_document(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_id=phase_id,
            test_case_id=test_case_id,
            document_type=document_type,
            file_obj=file_obj,
            original_filename=file.filename,
            document_title=document_title,
            uploaded_by=current_user.user_id,
            document_description=document_description,
            document_category=document_category,
            access_level=access_level,
            required_for_completion=required_for_completion,
            approval_required=approval_required,
            workflow_stage=workflow_stage
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return DocumentUploadResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    cycle_id: Optional[int] = Query(None),
    report_id: Optional[int] = Query(None),
    phase_id: Optional[int] = Query(None),
    test_case_id: Optional[str] = Query(None),
    document_type: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    latest_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List documents with filtering and pagination"""
    
    try:
        service = create_document_management_service(db)
        
        result = await service.get_documents(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_id=phase_id,
            test_case_id=test_case_id,
            document_type=document_type,
            user_id=current_user.user_id,
            include_archived=include_archived,
            latest_only=latest_only,
            page=page,
            page_size=page_size
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return DocumentListResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get document details"""
    
    try:
        service = create_document_management_service(db)
        
        result = await service.get_documents(page=1, page_size=1)
        documents = [doc for doc in result.get("documents", []) if doc["id"] == document_id]
        
        if not documents:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(**documents[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    track_download: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Download a document"""
    
    try:
        service = create_document_management_service(db)
        
        file_data, metadata = await service.download_document(
            document_id=document_id,
            user_id=current_user.user_id,
            track_download=track_download
        )
        
        if file_data is None:
            raise HTTPException(status_code=404, detail=metadata.get("error", "Document not found"))
        
        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=metadata["mime_type"],
            headers={
                "Content-Disposition": f"attachment; filename={metadata['filename']}",
                "Content-Length": str(metadata["file_size"])
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{document_id}", response_model=DocumentUpdateResponse)
async def update_document(
    document_id: int,
    request: DocumentUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update document metadata"""
    
    try:
        service = create_document_management_service(db)
        
        result = await service.update_document_metadata(
            document_id=document_id,
            user_id=current_user.user_id,
            **request.dict(exclude_none=True)
        )
        
        if not result.get("success"):
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail=result.get("error"))
            elif "permission" in result.get("error", "").lower():
                raise HTTPException(status_code=403, detail=result.get("error"))
            else:
                raise HTTPException(status_code=400, detail=result.get("error"))
        
        return DocumentUpdateResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: int,
    permanent: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete or archive a document"""
    
    try:
        service = create_document_management_service(db)
        
        result = await service.delete_document(
            document_id=document_id,
            user_id=current_user.user_id,
            permanent=permanent
        )
        
        if not result.get("success"):
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail=result.get("error"))
            elif "permission" in result.get("error", "").lower():
                raise HTTPException(status_code=403, detail=result.get("error"))
            else:
                raise HTTPException(status_code=400, detail=result.get("error"))
        
        return DocumentDeleteResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Search documents with full-text search"""
    
    try:
        service = create_document_management_service(db)
        
        result = await service.search_documents(
            search_query=request.search_query,
            cycle_id=request.cycle_id,
            report_id=request.report_id,
            phase_id=request.phase_id,
            document_type=request.document_type,
            user_id=current_user.user_id,
            page=request.page,
            page_size=request.page_size
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return DocumentSearchResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/summary", response_model=DocumentMetricsResponse)
async def get_document_statistics(
    cycle_id: Optional[int] = Query(None),
    report_id: Optional[int] = Query(None),
    phase_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get document statistics"""
    
    try:
        service = create_document_management_service(db)
        
        result = await service.get_document_statistics(
            cycle_id=cycle_id,
            report_id=report_id,
            phase_id=phase_id
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return DocumentMetricsResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Document Versioning Endpoints
@router.post("/{document_id}/versions", response_model=DocumentVersionCreateResponse)
async def create_document_version(
    document_id: int,
    document_title: str = Form(...),
    document_description: Optional[str] = Form(None),
    version_notes: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new version of an existing document"""
    
    try:
        service = create_document_management_service(db)
        
        # Create file object
        file_obj = io.BytesIO(await file.read())
        
        result = await service.create_document_version(
            parent_document_id=document_id,
            file_obj=file_obj,
            original_filename=file.filename,
            document_title=document_title,
            uploaded_by=current_user.user_id,
            document_description=document_description,
            version_notes=version_notes
        )
        
        if not result.get("success"):
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail=result.get("error"))
            elif "permission" in result.get("error", "").lower():
                raise HTTPException(status_code=403, detail=result.get("error"))
            else:
                raise HTTPException(status_code=400, detail=result.get("error"))
        
        return DocumentVersionCreateResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}/versions", response_model=DocumentVersionListResponse)
async def get_document_versions(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all versions of a document"""
    
    try:
        service = create_document_management_service(db)
        
        result = await service.get_document_versions(
            document_id=document_id,
            user_id=current_user.user_id
        )
        
        if "error" in result:
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail=result["error"])
            elif "access denied" in result.get("error", "").lower():
                raise HTTPException(status_code=403, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])
        
        return DocumentVersionListResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/{version_id}/restore", response_model=DocumentVersionRestoreResponse)
async def restore_document_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Restore a specific version as the latest version"""
    
    try:
        service = create_document_management_service(db)
        
        result = await service.restore_document_version(
            version_document_id=version_id,
            user_id=current_user.user_id
        )
        
        if not result.get("success"):
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail=result.get("error"))
            elif "permission" in result.get("error", "").lower():
                raise HTTPException(status_code=403, detail=result.get("error"))
            else:
                raise HTTPException(status_code=400, detail=result.get("error"))
        
        return DocumentVersionRestoreResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/versions/compare", response_model=DocumentVersionCompareResponse)
async def compare_document_versions(
    request: DocumentVersionCompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Compare two versions of a document"""
    
    try:
        service = create_document_management_service(db)
        
        result = await service.compare_document_versions(
            version1_id=request.version1_id,
            version2_id=request.version2_id,
            user_id=current_user.user_id
        )
        
        if "error" in result:
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail=result["error"])
            elif "access denied" in result.get("error", "").lower():
                raise HTTPException(status_code=403, detail=result["error"])
            else:
                raise HTTPException(status_code=400, detail=result["error"])
        
        return DocumentVersionCompareResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Bulk Operations
@router.post("/bulk/delete", response_model=BulkOperationResponse)
async def bulk_delete_documents(
    request: BulkDocumentDeleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Bulk delete or archive documents"""
    
    try:
        service = create_document_management_service(db)
        
        successes = []
        failures = []
        
        for document_id in request.document_ids:
            result = await service.delete_document(
                document_id=document_id,
                user_id=current_user.user_id,
                permanent=request.permanent
            )
            
            if result.get("success"):
                successes.append(document_id)
            else:
                failures.append({
                    "document_id": document_id,
                    "error": result.get("error", "Unknown error")
                })
        
        return BulkOperationResponse(
            success_count=len(successes),
            failure_count=len(failures),
            total_count=len(request.document_ids),
            successes=successes,
            failures=failures
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Document Approval Endpoints (for approval workflow)
@router.post("/{document_id}/approve", response_model=DocumentUpdateResponse)
async def approve_document(
    document_id: int,
    request: DocumentApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Approve or reject a document"""
    
    try:
        # This would integrate with the approval workflow
        # For now, we'll update the document metadata to reflect approval
        service = create_document_management_service(db)
        
        # Update approval status in metadata
        # This could be enhanced to integrate with workflow management
        result = await service.update_document_metadata(
            document_id=document_id,
            user_id=current_user.user_id,
            # Add approval-related fields to the update
        )
        
        if not result.get("success"):
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail=result.get("error"))
            elif "permission" in result.get("error", "").lower():
                raise HTTPException(status_code=403, detail=result.get("error"))
            else:
                raise HTTPException(status_code=400, detail=result.get("error"))
        
        return DocumentUpdateResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))