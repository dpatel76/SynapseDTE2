"""
Document Management Service
Handles document upload, download, validation, and lifecycle management for cycle reports
"""

import os
import hashlib
import uuid
import shutil
import mimetypes
from typing import List, Dict, Any, Optional, Union, BinaryIO, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text, select
from sqlalchemy.exc import IntegrityError

from app.models.cycle_report_documents import (
    CycleReportDocument, DocumentType, FileFormat, AccessLevel, 
    UploadStatus, ProcessingStatus, ValidationStatus,
    DocumentSummary, DocumentMetrics, DocumentSearchResult, DocumentVersionInfo
)
from app.models.user import User
from app.models.workflow import WorkflowPhase
from app.models.test_cycle import TestCycle
from app.models.report import Report


class DocumentManagementService:
    """Document management service with comprehensive functionality"""
    
    def __init__(self, db: AsyncSession, upload_base_path: str = None):
        self.db = db
        if upload_base_path is None:
            # Use environment variable or fallback to a writable temp directory
            upload_base_path = os.environ.get("DOCUMENT_UPLOAD_PATH", "/tmp/synapse_uploads")
        self.upload_base_path = Path(upload_base_path)
        try:
            self.upload_base_path.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to temp directory if original path is read-only
            self.upload_base_path = Path("/tmp/synapse_uploads")
            self.upload_base_path.mkdir(parents=True, exist_ok=True)
        
        # Supported file formats and MIME types
        self.mime_type_mapping = {
            'csv': 'text/csv',
            'pipe': 'text/plain',
            'excel': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'xls': 'application/vnd.ms-excel',
            'word': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'pdf': 'application/pdf',
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg',
            'png': 'image/png'
        }
        
        # Maximum file sizes (in bytes)
        self.max_file_sizes = {
            'csv': 100 * 1024 * 1024,  # 100MB
            'pipe': 100 * 1024 * 1024,  # 100MB
            'excel': 50 * 1024 * 1024,  # 50MB
            'xlsx': 50 * 1024 * 1024,  # 50MB
            'xls': 50 * 1024 * 1024,  # 50MB
            'word': 25 * 1024 * 1024,  # 25MB
            'docx': 25 * 1024 * 1024,  # 25MB
            'pdf': 50 * 1024 * 1024,  # 50MB
            'jpeg': 10 * 1024 * 1024,  # 10MB
            'jpg': 10 * 1024 * 1024,  # 10MB
            'png': 10 * 1024 * 1024  # 10MB
        }

    async def upload_document(
        self,
        cycle_id: int,
        report_id: int,
        phase_id: int,
        document_type: str,
        file_obj: BinaryIO,
        original_filename: str,
        document_title: str,
        uploaded_by: int,
        document_description: str = None,
        document_category: str = "general",
        access_level: str = "phase_restricted",
        allowed_roles: List[str] = None,
        allowed_users: List[int] = None,
        required_for_completion: bool = False,
        approval_required: bool = False,
        workflow_stage: str = None,
        test_case_id: str = None
    ) -> Dict[str, Any]:
        """Upload a new document"""
        
        try:
            # Validate inputs
            file_format = self._get_file_format(original_filename)
            self._validate_file_format(file_format)
            
            # Read file data
            file_data = file_obj.read()
            file_size = len(file_data)
            
            # Validate file size
            self._validate_file_size(file_format, file_size)
            
            # Generate file hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Check for duplicate files
            from sqlalchemy import select
            result = await self.db.execute(select(CycleReportDocument).filter(
                CycleReportDocument.file_hash == file_hash,
                CycleReportDocument.cycle_id == cycle_id,
                CycleReportDocument.report_id == report_id,
                CycleReportDocument.phase_id == phase_id,
                CycleReportDocument.test_case_id == test_case_id
            ))
            existing_doc = result.scalar_one_or_none()
            
            if existing_doc:
                return {
                    "success": False,
                    "error": "Duplicate file detected",
                    "existing_document_id": existing_doc.id
                }
            
            # Generate unique storage filename
            stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
            
            # Create directory structure
            storage_dir = self.upload_base_path / str(cycle_id) / str(report_id) / str(phase_id)
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Full file path
            file_path = storage_dir / stored_filename
            
            # Save file to disk
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(original_filename)
            if not mime_type:
                mime_type = self.mime_type_mapping.get(file_format, 'application/octet-stream')
            
            # Create document record
            document = CycleReportDocument(
                cycle_id=cycle_id,
                report_id=report_id,
                phase_id=phase_id,
                test_case_id=test_case_id,
                document_type=document_type,
                document_category=document_category,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=str(file_path),
                file_size=file_size,
                file_format=file_format,
                mime_type=mime_type,
                file_hash=file_hash,
                document_title=document_title,
                document_description=document_description,
                access_level=access_level,
                allowed_roles=allowed_roles,
                allowed_users=allowed_users,
                upload_status=UploadStatus.UPLOADED.value,
                required_for_completion=required_for_completion,
                approval_required=approval_required,
                workflow_stage=workflow_stage,
                uploaded_by=uploaded_by,
                created_by=uploaded_by,
                updated_by=uploaded_by
            )
            
            self.db.add(document)
            self.db.commit()
            
            # Process document asynchronously (extract metadata, generate preview, etc.)
            await self._process_document_async(document.id)
            
            return {
                "success": True,
                "document_id": document.id,
                "document": self._document_to_dict(document)
            }
            
        except Exception as e:
            self.db.rollback()
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            
            return {
                "success": False,
                "error": str(e)
            }

    async def download_document(
        self,
        document_id: int,
        user_id: int,
        track_download: bool = True
    ) -> Tuple[Optional[bytes], Optional[Dict[str, Any]]]:
        """Download a document"""
        
        try:
            # Get document
            document = self.db.query(CycleReportDocument).filter(
                CycleReportDocument.id == document_id
            ).first()
            
            if not document:
                return None, {"error": "Document not found"}
            
            # Check access permissions
            if not self._check_access_permission(document, user_id):
                return None, {"error": "Access denied"}
            
            # Check if file exists
            file_path = Path(document.file_path)
            if not file_path.exists():
                return None, {"error": "File not found on disk"}
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Track download if requested
            if track_download:
                document.download_count += 1
                document.last_downloaded_at = datetime.utcnow()
                document.last_downloaded_by = user_id
                self.db.commit()
            
            # Return file data and metadata
            return file_data, {
                "filename": document.original_filename,
                "mime_type": document.mime_type,
                "file_size": document.file_size
            }
            
        except Exception as e:
            return None, {"error": str(e)}

    async def get_documents(
        self,
        cycle_id: int = None,
        report_id: int = None,
        phase_id: int = None,
        test_case_id: str = None,
        document_type: str = None,
        user_id: int = None,
        include_archived: bool = False,
        latest_only: bool = True,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Get documents with filtering and pagination"""
        
        try:
            # Build query with join to WorkflowPhase if we need cycle_id or report_id filters
            if cycle_id or report_id:
                from app.models.workflow import WorkflowPhase
                query = select(CycleReportDocument).join(WorkflowPhase, CycleReportDocument.phase_id == WorkflowPhase.phase_id)
                
                # Apply cycle/report filters
                if cycle_id:
                    query = query.where(WorkflowPhase.cycle_id == cycle_id)
                if report_id:
                    query = query.where(WorkflowPhase.report_id == report_id)
            else:
                query = select(CycleReportDocument)
            
            # Apply other filters
            if phase_id:
                query = query.where(CycleReportDocument.phase_id == phase_id)
            if test_case_id:
                query = query.where(CycleReportDocument.test_case_id == test_case_id)
            if document_type:
                query = query.where(CycleReportDocument.document_type == document_type)
            
            if not include_archived:
                query = query.where(CycleReportDocument.is_archived == False)
            
            if latest_only:
                query = query.where(CycleReportDocument.is_latest_version == True)
            
            # Apply access control if user specified
            if user_id:
                query = await self._apply_access_control_async(query, user_id)
            
            # Get total count - build a separate simpler count query
            if cycle_id or report_id:
                from app.models.workflow import WorkflowPhase
                count_query = select(func.count(CycleReportDocument.id)).join(WorkflowPhase, CycleReportDocument.phase_id == WorkflowPhase.phase_id)
                
                if cycle_id:
                    count_query = count_query.where(WorkflowPhase.cycle_id == cycle_id)
                if report_id:
                    count_query = count_query.where(WorkflowPhase.report_id == report_id)
            else:
                count_query = select(func.count(CycleReportDocument.id))
            
            # Apply the same filters for counting
            if phase_id:
                count_query = count_query.where(CycleReportDocument.phase_id == phase_id)
            if test_case_id:
                count_query = count_query.where(CycleReportDocument.test_case_id == test_case_id)
            if document_type:
                count_query = count_query.where(CycleReportDocument.document_type == document_type)
            if not include_archived:
                count_query = count_query.where(CycleReportDocument.is_archived == False)
            if latest_only:
                count_query = count_query.where(CycleReportDocument.is_latest_version == True)
                
            total_count_result = await self.db.execute(count_query)
            total_count = total_count_result.scalar()
            
            # Apply pagination
            offset = (page - 1) * page_size
            query = query.order_by(desc(CycleReportDocument.uploaded_at)).offset(offset).limit(page_size)
            result = await self.db.execute(query)
            documents = result.scalars().all()
            
            # Convert to dictionaries
            document_list = [self._document_to_dict(doc) for doc in documents]
            
            return {
                "documents": document_list,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def update_document_metadata(
        self,
        document_id: int,
        user_id: int,
        document_title: str = None,
        document_description: str = None,
        document_category: str = None,
        access_level: str = None,
        allowed_roles: List[str] = None,
        allowed_users: List[int] = None,
        required_for_completion: bool = None,
        approval_required: bool = None,
        workflow_stage: str = None
    ) -> Dict[str, Any]:
        """Update document metadata"""
        
        try:
            document = self.db.query(CycleReportDocument).filter(
                CycleReportDocument.id == document_id
            ).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
            
            # Check write permissions
            if not self._check_write_permission(document, user_id):
                return {"success": False, "error": "Permission denied"}
            
            # Update fields
            if document_title is not None:
                document.document_title = document_title
            if document_description is not None:
                document.document_description = document_description
            if document_category is not None:
                document.document_category = document_category
            if access_level is not None:
                document.access_level = access_level
            if allowed_roles is not None:
                document.allowed_roles = allowed_roles
            if allowed_users is not None:
                document.allowed_users = allowed_users
            if required_for_completion is not None:
                document.required_for_completion = required_for_completion
            if approval_required is not None:
                document.approval_required = approval_required
            if workflow_stage is not None:
                document.workflow_stage = workflow_stage
            
            document.updated_by = user_id
            self.db.commit()
            
            return {
                "success": True,
                "document": self._document_to_dict(document)
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    async def delete_document(
        self,
        document_id: int,
        user_id: int,
        permanent: bool = False
    ) -> Dict[str, Any]:
        """Delete or archive a document"""
        
        try:
            document = self.db.query(CycleReportDocument).filter(
                CycleReportDocument.id == document_id
            ).first()
            
            if not document:
                return {"success": False, "error": "Document not found"}
            
            # Check delete permissions
            if not self._check_write_permission(document, user_id):
                return {"success": False, "error": "Permission denied"}
            
            if permanent:
                # Permanent deletion
                file_path = Path(document.file_path)
                if file_path.exists():
                    file_path.unlink()
                
                self.db.delete(document)
                self.db.commit()
                
                return {"success": True, "message": "Document permanently deleted"}
            
            else:
                # Archive document
                document.is_archived = True
                document.archived_at = datetime.utcnow()
                document.archived_by = user_id
                document.updated_by = user_id
                self.db.commit()
                
                return {"success": True, "message": "Document archived"}
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    async def search_documents(
        self,
        search_query: str,
        cycle_id: int = None,
        report_id: int = None,
        phase_id: int = None,
        document_type: str = None,
        user_id: int = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """Search documents with full-text search"""
        
        try:
            # Build base query
            query = self.db.query(CycleReportDocument)
            
            # Apply filters
            if cycle_id:
                query = query.filter(CycleReportDocument.cycle_id == cycle_id)
            if report_id:
                query = query.filter(CycleReportDocument.report_id == report_id)
            if phase_id:
                query = query.filter(CycleReportDocument.phase_id == phase_id)
            if document_type:
                query = query.filter(CycleReportDocument.document_type == document_type)
            
            query = query.filter(CycleReportDocument.is_archived == False)
            query = query.filter(CycleReportDocument.is_latest_version == True)
            
            # Apply access control
            if user_id:
                query = self._apply_access_control(query, user_id)
            
            # Apply full-text search
            search_vector = func.to_tsvector('english', 
                func.coalesce(CycleReportDocument.document_title, '') + ' ' +
                func.coalesce(CycleReportDocument.document_description, '') + ' ' +
                func.coalesce(CycleReportDocument.content_preview, '') + ' ' +
                func.coalesce(CycleReportDocument.content_summary, '')
            )
            
            search_query_formatted = func.plainto_tsquery('english', search_query)
            
            query = query.filter(search_vector.op('@@')(search_query_formatted))
            
            # Add relevance ranking
            rank = func.ts_rank(search_vector, search_query_formatted)
            query = query.add_columns(rank.label('relevance')).order_by(desc('relevance'))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            results = query.offset(offset).limit(page_size).all()
            
            # Convert to search results
            search_results = []
            for doc, relevance in results:
                search_results.append({
                    "document": self._document_to_dict(doc),
                    "relevance_score": float(relevance)
                })
            
            return {
                "search_results": search_results,
                "search_query": search_query,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size
                }
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def create_document_version(
        self,
        parent_document_id: int,
        file_obj: BinaryIO,
        original_filename: str,
        document_title: str,
        uploaded_by: int,
        document_description: str = None,
        version_notes: str = None
    ) -> Dict[str, Any]:
        """Create a new version of an existing document"""
        
        try:
            # Get parent document
            parent_doc = self.db.query(CycleReportDocument).filter(
                CycleReportDocument.id == parent_document_id
            ).first()
            
            if not parent_doc:
                return {"success": False, "error": "Parent document not found"}
            
            # Check write permissions
            if not self._check_write_permission(parent_doc, uploaded_by):
                return {"success": False, "error": "Permission denied"}
            
            # Generate new version number
            current_version_parts = parent_doc.document_version.split('.')
            if len(current_version_parts) >= 2:
                major, minor = int(current_version_parts[0]), int(current_version_parts[1])
                new_version = f"{major}.{minor + 1}"
            else:
                new_version = "2.0"
            
            # Validate inputs
            file_format = self._get_file_format(original_filename)
            self._validate_file_format(file_format)
            
            # Read file data
            file_data = file_obj.read()
            file_size = len(file_data)
            
            # Validate file size
            self._validate_file_size(file_format, file_size)
            
            # Generate file hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            # Generate unique storage filename
            stored_filename = f"{uuid.uuid4().hex}_{original_filename}"
            
            # Create directory structure (same as parent)
            storage_dir = self.upload_base_path / str(parent_doc.cycle_id) / str(parent_doc.report_id) / str(parent_doc.phase_id)
            storage_dir.mkdir(parents=True, exist_ok=True)
            
            # Full file path
            file_path = storage_dir / stored_filename
            
            # Save file to disk
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Detect MIME type
            mime_type, _ = mimetypes.guess_type(original_filename)
            if not mime_type:
                mime_type = self.mime_type_mapping.get(file_format, 'application/octet-stream')
            
            # Create new version document record
            new_document = CycleReportDocument(
                cycle_id=parent_doc.cycle_id,
                report_id=parent_doc.report_id,
                phase_id=parent_doc.phase_id,
                document_type=parent_doc.document_type,
                document_category=parent_doc.document_category,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_path=str(file_path),
                file_size=file_size,
                file_format=file_format,
                mime_type=mime_type,
                file_hash=file_hash,
                document_title=document_title,
                document_description=document_description,
                document_version=new_version,
                parent_document_id=parent_document_id,
                access_level=parent_doc.access_level,
                allowed_roles=parent_doc.allowed_roles,
                allowed_users=parent_doc.allowed_users,
                upload_status=UploadStatus.UPLOADED.value,
                required_for_completion=parent_doc.required_for_completion,
                approval_required=parent_doc.approval_required,
                workflow_stage=parent_doc.workflow_stage,
                uploaded_by=uploaded_by,
                created_by=uploaded_by,
                updated_by=uploaded_by
            )
            
            self.db.add(new_document)
            
            # Mark previous version as not latest (trigger will handle this automatically)
            # But we'll do it explicitly for clarity
            parent_doc.is_latest_version = False
            
            self.db.commit()
            
            # Process document asynchronously
            await self._process_document_async(new_document.id)
            
            return {
                "success": True,
                "document_id": new_document.id,
                "document": self._document_to_dict(new_document),
                "parent_document_id": parent_document_id,
                "version": new_version
            }
            
        except Exception as e:
            self.db.rollback()
            # Clean up file if it was created
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            
            return {"success": False, "error": str(e)}

    async def get_document_versions(
        self,
        document_id: int,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Get all versions of a document"""
        
        try:
            # Get the document
            document = self.db.query(CycleReportDocument).filter(
                CycleReportDocument.id == document_id
            ).first()
            
            if not document:
                return {"error": "Document not found"}
            
            # Check access permissions
            if user_id and not self._check_access_permission(document, user_id):
                return {"error": "Access denied"}
            
            # Find all versions (including parent and children)
            if document.parent_document_id:
                # This is a version, get the root document
                root_id = document.parent_document_id
            else:
                # This is the root document
                root_id = document.id
            
            # Get all versions
            versions = self.db.query(CycleReportDocument).filter(
                or_(
                    CycleReportDocument.id == root_id,
                    CycleReportDocument.parent_document_id == root_id
                )
            ).order_by(CycleReportDocument.created_at).all()
            
            # Convert to dictionaries
            version_list = [self._document_to_dict(doc) for doc in versions]
            
            return {
                "versions": version_list,
                "total_versions": len(version_list),
                "latest_version": max(version_list, key=lambda x: x['created_at']) if version_list else None
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def restore_document_version(
        self,
        version_document_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Restore a specific version as the latest version"""
        
        try:
            # Get the version to restore
            version_doc = self.db.query(CycleReportDocument).filter(
                CycleReportDocument.id == version_document_id
            ).first()
            
            if not version_doc:
                return {"success": False, "error": "Version document not found"}
            
            # Check write permissions
            if not self._check_write_permission(version_doc, user_id):
                return {"success": False, "error": "Permission denied"}
            
            # Find all documents in this version chain
            if version_doc.parent_document_id:
                root_id = version_doc.parent_document_id
            else:
                root_id = version_doc.id
            
            # Mark all versions as not latest
            self.db.query(CycleReportDocument).filter(
                or_(
                    CycleReportDocument.id == root_id,
                    CycleReportDocument.parent_document_id == root_id
                )
            ).update({"is_latest_version": False})
            
            # Mark the selected version as latest
            version_doc.is_latest_version = True
            version_doc.updated_by = user_id
            
            self.db.commit()
            
            return {
                "success": True,
                "message": f"Version {version_doc.document_version} restored as latest",
                "document": self._document_to_dict(version_doc)
            }
            
        except Exception as e:
            self.db.rollback()
            return {"success": False, "error": str(e)}

    async def compare_document_versions(
        self,
        version1_id: int,
        version2_id: int,
        user_id: int = None
    ) -> Dict[str, Any]:
        """Compare two versions of a document"""
        
        try:
            # Get both versions
            version1 = self.db.query(CycleReportDocument).filter(
                CycleReportDocument.id == version1_id
            ).first()
            
            version2 = self.db.query(CycleReportDocument).filter(
                CycleReportDocument.id == version2_id
            ).first()
            
            if not version1 or not version2:
                return {"error": "One or both versions not found"}
            
            # Check access permissions
            if user_id:
                if not self._check_access_permission(version1, user_id) or not self._check_access_permission(version2, user_id):
                    return {"error": "Access denied"}
            
            # Compare metadata
            differences = {}
            
            comparable_fields = [
                'document_title', 'document_description', 'file_size', 
                'document_version', 'file_hash', 'uploaded_by', 'uploaded_at'
            ]
            
            for field in comparable_fields:
                val1 = getattr(version1, field)
                val2 = getattr(version2, field)
                if val1 != val2:
                    differences[field] = {
                        'version1': val1,
                        'version2': val2
                    }
            
            return {
                "version1": self._document_to_dict(version1),
                "version2": self._document_to_dict(version2),
                "differences": differences,
                "has_differences": len(differences) > 0
            }
            
        except Exception as e:
            return {"error": str(e)}

    async def get_document_statistics(
        self,
        cycle_id: int = None,
        report_id: int = None,
        phase_id: int = None
    ) -> Dict[str, Any]:
        """Get document statistics"""
        
        try:
            # Build base query
            query = self.db.query(CycleReportDocument)
            
            # Apply filters
            if cycle_id:
                query = query.filter(CycleReportDocument.cycle_id == cycle_id)
            if report_id:
                query = query.filter(CycleReportDocument.report_id == report_id)
            if phase_id:
                query = query.filter(CycleReportDocument.phase_id == phase_id)
            
            query = query.filter(CycleReportDocument.is_archived == False)
            query = query.filter(CycleReportDocument.is_latest_version == True)
            
            # Total documents and size
            total_docs = query.count()
            total_size = query.with_entities(func.sum(CycleReportDocument.file_size)).scalar() or 0
            
            # Distribution by document type
            type_stats = self.db.query(
                CycleReportDocument.document_type,
                func.count(CycleReportDocument.id).label('count'),
                func.sum(CycleReportDocument.file_size).label('total_size')
            ).group_by(CycleReportDocument.document_type).all()
            
            # Distribution by upload status
            status_stats = self.db.query(
                CycleReportDocument.upload_status,
                func.count(CycleReportDocument.id).label('count')
            ).group_by(CycleReportDocument.upload_status).all()
            
            # Distribution by file format
            format_stats = self.db.query(
                CycleReportDocument.file_format,
                func.count(CycleReportDocument.id).label('count'),
                func.sum(CycleReportDocument.file_size).label('total_size')
            ).group_by(CycleReportDocument.file_format).all()
            
            return {
                "total_documents": total_docs,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "by_document_type": {row.document_type: {"count": row.count, "size_bytes": row.total_size or 0} for row in type_stats},
                "by_upload_status": {row.upload_status: row.count for row in status_stats},
                "by_file_format": {row.file_format: {"count": row.count, "size_bytes": row.total_size or 0} for row in format_stats}
            }
            
        except Exception as e:
            return {"error": str(e)}

    # Helper methods
    def _get_file_format(self, filename: str) -> str:
        """Extract file format from filename"""
        return filename.split('.')[-1].lower()

    def _validate_file_format(self, file_format: str):
        """Validate file format"""
        allowed_formats = list(self.mime_type_mapping.keys())
        if file_format not in allowed_formats:
            raise ValueError(f"Unsupported file format: {file_format}. Allowed formats: {', '.join(allowed_formats)}")

    def _validate_file_size(self, file_format: str, file_size: int):
        """Validate file size"""
        max_size = self.max_file_sizes.get(file_format, 10 * 1024 * 1024)  # Default 10MB
        if file_size > max_size:
            raise ValueError(f"File too large. Maximum size for {file_format} files: {max_size / (1024*1024):.1f}MB")

    def _check_access_permission(self, document: CycleReportDocument, user_id: int) -> bool:
        """Check if user has access to document"""
        # TODO: Implement comprehensive access control
        # For now, allow all access (placeholder)
        return True

    def _check_write_permission(self, document: CycleReportDocument, user_id: int) -> bool:
        """Check if user has write permission to document"""
        # TODO: Implement comprehensive write permission check
        # For now, allow owner and admin access
        return document.uploaded_by == user_id

    def _apply_access_control(self, query, user_id: int):
        """Apply access control filters to query"""
        # TODO: Implement comprehensive access control
        # For now, return query as-is
        return query
    
    async def _apply_access_control_async(self, query, user_id: int):
        """Apply access control filters to query (async version)"""
        # TODO: Implement comprehensive access control
        # For now, return query as-is
        return query

    def _document_to_dict(self, document: CycleReportDocument) -> Dict[str, Any]:
        """Convert document model to dictionary"""
        return {
            "id": document.id,
            "cycle_id": document.cycle_id,
            "report_id": document.report_id,
            "phase_id": document.phase_id,
            "test_case_id": document.test_case_id,
            "document_type": document.document_type,
            "document_category": document.document_category,
            "original_filename": document.original_filename,
            "file_size": document.file_size,
            "file_format": document.file_format,
            "mime_type": document.mime_type,
            "document_title": document.document_title,
            "document_description": document.document_description,
            "document_version": document.document_version,
            "is_latest_version": document.is_latest_version,
            "access_level": document.access_level,
            "upload_status": document.upload_status,
            "processing_status": document.processing_status,
            "validation_status": document.validation_status,
            "content_preview": document.content_preview,
            "quality_score": document.quality_score,
            "download_count": document.download_count,
            "view_count": document.view_count,
            "required_for_completion": document.required_for_completion,
            "approval_required": document.approval_required,
            "workflow_stage": document.workflow_stage,
            "uploaded_by": document.uploaded_by,
            "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
            "is_archived": document.is_archived
        }

    async def _process_document_async(self, document_id: int):
        """Process document asynchronously (extract metadata, generate preview, etc.)"""
        # TODO: Implement document processing
        # This could include:
        # - Extract text content for search
        # - Generate thumbnails for images
        # - Validate document structure
        # - Extract metadata
        # - Generate content summary
        pass


# Factory function for dependency injection
def create_document_management_service(db: AsyncSession) -> DocumentManagementService:
    """Create document management service instance"""
    return DocumentManagementService(db)