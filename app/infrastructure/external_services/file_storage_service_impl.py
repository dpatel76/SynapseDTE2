"""Production implementation of File Storage service"""
from typing import Optional, List, Dict, Any
import os
import uuid
import logging
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import hashlib
from urllib.parse import quote

from app.application.interfaces.external_services import IFileStorageService
from app.core.config import settings

logger = logging.getLogger(__name__)


class FileStorageServiceImpl(IFileStorageService):
    """Production implementation of file storage service"""
    
    def __init__(self):
        # Set up storage directories
        self.base_path = Path(settings.upload_dir if hasattr(settings, 'upload_dir') else './uploads')
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.samples_path = self.base_path / 'samples'
        self.documents_path = self.base_path / 'documents'
        self.evidence_path = self.base_path / 'evidence'
        self.reports_path = self.base_path / 'reports'
        self.temp_path = self.base_path / 'temp'
        
        for path in [self.samples_path, self.documents_path, self.evidence_path, 
                     self.reports_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    async def upload_file(self, file_data: bytes, file_name: str, 
                         folder: str) -> str:
        """Upload a file and return its URL/path"""
        try:
            # Determine target directory
            target_dir = self._get_folder_path(folder)
            
            # Generate unique filename
            file_ext = Path(file_name).suffix
            unique_name = f"{uuid.uuid4().hex}{file_ext}"
            file_path = target_dir / unique_name
            
            # Write file asynchronously
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            
            # Generate file metadata
            file_hash = hashlib.sha256(file_data).hexdigest()
            metadata_path = file_path.with_suffix('.meta')
            
            metadata = {
                'original_name': file_name,
                'unique_name': unique_name,
                'folder': folder,
                'size': len(file_data),
                'hash': file_hash,
                'uploaded_at': datetime.utcnow().isoformat(),
                'content_type': self._guess_content_type(file_name)
            }
            
            # Write metadata
            import json
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata, indent=2))
            
            # Return relative path from base
            relative_path = file_path.relative_to(self.base_path)
            return str(relative_path)
        
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            raise
    
    async def download_file(self, file_path: str) -> bytes:
        """Download a file"""
        try:
            # Construct full path
            full_path = self.base_path / file_path
            
            # Security check - ensure path is within base directory
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                raise ValueError("Invalid file path - access denied")
            
            # Check if file exists
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Read file asynchronously
            async with aiofiles.open(full_path, 'rb') as f:
                data = await f.read()
            
            return data
        
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            raise
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        try:
            # Construct full path
            full_path = self.base_path / file_path
            
            # Security check
            if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
                raise ValueError("Invalid file path - access denied")
            
            # Delete file and metadata if they exist
            if full_path.exists():
                full_path.unlink()
            
            metadata_path = full_path.with_suffix('.meta')
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
        
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return False
    
    async def get_file_url(self, file_path: str, expiry_hours: int = 24) -> str:
        """Get a temporary URL for file access"""
        try:
            # In a production environment, this would generate a signed URL
            # For local storage, we'll create a time-limited access token
            
            # Generate access token
            import secrets
            token = secrets.token_urlsafe(32)
            expiry_time = datetime.utcnow() + timedelta(hours=expiry_hours)
            
            # Store token (in production, this would be in Redis or similar)
            token_path = self.temp_path / f"token_{token}.json"
            token_data = {
                'file_path': file_path,
                'token': token,
                'expires_at': expiry_time.isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
            
            import json
            async with aiofiles.open(token_path, 'w') as f:
                await f.write(json.dumps(token_data))
            
            # Generate URL (in production, this would be the actual server URL)
            base_url = os.getenv('FILE_SERVER_URL', 'http://localhost:8001/files')
            encoded_path = quote(file_path, safe='')
            url = f"{base_url}/download/{encoded_path}?token={token}"
            
            return url
        
        except Exception as e:
            logger.error(f"Error generating file URL: {str(e)}")
            raise
    
    async def copy_file(self, source_path: str, dest_folder: str) -> str:
        """Copy a file to a new location"""
        try:
            # Download the source file
            file_data = await self.download_file(source_path)
            
            # Get original filename from metadata
            source_full_path = self.base_path / source_path
            metadata_path = source_full_path.with_suffix('.meta')
            
            original_name = source_path.split('/')[-1]  # Default
            if metadata_path.exists():
                import json
                async with aiofiles.open(metadata_path, 'r') as f:
                    metadata = json.loads(await f.read())
                    original_name = metadata.get('original_name', original_name)
            
            # Upload to new location
            new_path = await self.upload_file(file_data, original_name, dest_folder)
            
            return new_path
        
        except Exception as e:
            logger.error(f"Error copying file: {str(e)}")
            raise
    
    async def list_files(self, folder: str, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """List files in a folder"""
        try:
            target_dir = self._get_folder_path(folder)
            files = []
            
            # List all files (excluding metadata files)
            for file_path in target_dir.glob(pattern or '*'):
                if file_path.suffix == '.meta':
                    continue
                
                # Get file info
                stat = file_path.stat()
                relative_path = file_path.relative_to(self.base_path)
                
                file_info = {
                    'path': str(relative_path),
                    'name': file_path.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
                }
                
                # Try to load metadata
                metadata_path = file_path.with_suffix('.meta')
                if metadata_path.exists():
                    try:
                        import json
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            file_info['original_name'] = metadata.get('original_name')
                            file_info['content_type'] = metadata.get('content_type')
                            file_info['hash'] = metadata.get('hash')
                    except:
                        pass
                
                files.append(file_info)
            
            # Sort by modified time, newest first
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            return files
        
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []
    
    def _get_folder_path(self, folder: str) -> Path:
        """Get the path for a specific folder"""
        folder_map = {
            'samples': self.samples_path,
            'documents': self.documents_path,
            'evidence': self.evidence_path,
            'reports': self.reports_path,
            'temp': self.temp_path
        }
        
        return folder_map.get(folder, self.base_path / folder)
    
    def _guess_content_type(self, filename: str) -> str:
        """Guess content type from filename"""
        ext = Path(filename).suffix.lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.zip': 'application/zip'
        }
        
        return content_types.get(ext, 'application/octet-stream')