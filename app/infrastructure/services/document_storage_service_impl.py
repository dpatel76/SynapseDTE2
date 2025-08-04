"""Implementation of DocumentStorageService"""
from typing import Dict, Any, Optional
import os
import uuid
from datetime import datetime
from pathlib import Path
import json
import hashlib

from app.application.interfaces.services import DocumentStorageService
from app.core.config import settings


class DocumentStorageServiceImpl(DocumentStorageService):
    """Implementation of document storage service using file system"""
    
    def __init__(self):
        # Set up storage directory
        self.storage_root = Path(settings.upload_dir)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        self.documents_dir = self.storage_root / "documents"
        self.documents_dir.mkdir(exist_ok=True)
        
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
    
    async def store_document(
        self,
        file_content: bytes,
        filename: str,
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a document and return its ID"""
        try:
            # Generate unique document ID
            document_id = str(uuid.uuid4())
            
            # Calculate file hash for integrity
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Create document directory
            doc_dir = self.documents_dir / document_id
            doc_dir.mkdir(exist_ok=True)
            
            # Store the file
            file_path = doc_dir / filename
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Store metadata
            doc_metadata = {
                "document_id": document_id,
                "filename": filename,
                "content_type": content_type,
                "size": len(file_content),
                "hash": file_hash,
                "created_at": datetime.utcnow().isoformat(),
                "storage_path": str(file_path.relative_to(self.storage_root)),
                "custom_metadata": metadata or {}
            }
            
            metadata_path = self.metadata_dir / f"{document_id}.json"
            with open(metadata_path, 'w') as f:
                json.dump(doc_metadata, f, indent=2)
            
            return document_id
            
        except Exception as e:
            raise Exception(f"Failed to store document: {str(e)}")
    
    async def retrieve_document(self, document_id: str) -> Dict[str, Any]:
        """Retrieve a document by ID"""
        try:
            # Load metadata
            metadata_path = self.metadata_dir / f"{document_id}.json"
            if not metadata_path.exists():
                raise FileNotFoundError(f"Document {document_id} not found")
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Load file content
            file_path = self.storage_root / metadata['storage_path']
            if not file_path.exists():
                raise FileNotFoundError(f"Document file not found: {document_id}")
            
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Verify integrity
            current_hash = hashlib.sha256(content).hexdigest()
            if current_hash != metadata['hash']:
                raise Exception(f"Document integrity check failed: {document_id}")
            
            return {
                "document_id": document_id,
                "filename": metadata['filename'],
                "content_type": metadata['content_type'],
                "content": content,
                "size": metadata['size'],
                "created_at": metadata['created_at'],
                "metadata": metadata.get('custom_metadata', {})
            }
            
        except Exception as e:
            raise Exception(f"Failed to retrieve document: {str(e)}")
    
    async def delete_document(self, document_id: str) -> None:
        """Delete a document"""
        try:
            # Load metadata to get file path
            metadata_path = self.metadata_dir / f"{document_id}.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Delete file
                file_path = self.storage_root / metadata['storage_path']
                if file_path.exists():
                    file_path.unlink()
                
                # Delete document directory if empty
                doc_dir = file_path.parent
                if doc_dir.exists() and not list(doc_dir.iterdir()):
                    doc_dir.rmdir()
                
                # Delete metadata
                metadata_path.unlink()
            
        except Exception as e:
            raise Exception(f"Failed to delete document: {str(e)}")
    
    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Get document metadata without retrieving content"""
        try:
            # Load metadata
            metadata_path = self.metadata_dir / f"{document_id}.json"
            if not metadata_path.exists():
                raise FileNotFoundError(f"Document {document_id} not found")
            
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Return metadata without file content
            return {
                "document_id": document_id,
                "filename": metadata['filename'],
                "content_type": metadata['content_type'],
                "size": metadata['size'],
                "created_at": metadata['created_at'],
                "metadata": metadata.get('custom_metadata', {})
            }
            
        except Exception as e:
            raise Exception(f"Failed to get document metadata: {str(e)}")