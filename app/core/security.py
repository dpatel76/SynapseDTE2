"""
Enterprise Security Module
Provides AES-256 encryption, secure key management, and enhanced security features
"""

import os
import base64
import secrets
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import logging
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# Role-Based Access Control Implementation
ROLE_PERMISSIONS = {
    "Admin": ["*"],  # Admin has access to everything
    "Test Executive": [
        "cycles.*", "reports.read", "users.read", "lobs.read", 
        "planning.read", "scoping.read", "assignments.*"
    ],
    "Tester": [
        "planning.*", "scoping.*", "testing.*", "attributes.*",
        "cycles.read", "reports.read"
    ],
    "Report Owner": [
        "reports.*", "scoping.approve", "observations.review",
        "cycles.read", "planning.read"
    ],
    "Report Owner Executive": [
        "reports.read", "observations.read", "dashboard.*",
        "cycles.read", "portfolio.*"
    ],
    "Data Owner": [
        "request-info.*", "submissions.*", "documents.upload",
        "data-owner.submit"
    ],
    "Data Executive": [
        "data-owner.*", "lobs.*", "assignments.cdo",
        "escalations.*", "compliance.*"
    ]
}

def check_permission(user_role: str, required_permission: str) -> bool:
    """Check if a user role has the required permission"""
    if not user_role or user_role not in ROLE_PERMISSIONS:
        return False
    
    user_permissions = ROLE_PERMISSIONS[user_role]
    
    # Admin has access to everything
    if "*" in user_permissions:
        return True
    
    # Check exact match
    if required_permission in user_permissions:
        return True
    
    # Check wildcard patterns
    for permission in user_permissions:
        if permission.endswith(".*"):
            permission_prefix = permission[:-2]
            if required_permission.startswith(permission_prefix):
                return True
    
    return False

def role_required(required_permissions: List[str]):
    """Decorator to enforce role-based access control"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs (should be injected by FastAPI dependency)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            user_role = getattr(current_user, 'role', None)
            if not user_role:
                raise HTTPException(status_code=403, detail="User role not defined")
            
            # Check if user has any of the required permissions
            has_permission = False
            for permission in required_permissions:
                if check_permission(user_role, permission):
                    has_permission = True
                    break
            
            if not has_permission:
                SecurityAudit.log_security_event(
                    "RBAC_ACCESS_DENIED",
                    getattr(current_user, 'user_id', None),
                    {
                        "required_permissions": required_permissions,
                        "user_role": user_role,
                        "endpoint": func.__name__
                    }
                )
                raise HTTPException(
                    status_code=403, 
                    detail=f"Access denied. Required permissions: {required_permissions}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

async def check_lob_access(user_id: int, lob_id: int, db: AsyncSession) -> bool:
    """Check if user has access to specific LOB"""
    from app.models.user import User
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return False
    
    # Admin and CDO have access to all LOBs
    if user.role in ["Admin", "Data Executive"]:
        return True
    
    # Check if user's LOB matches the required LOB
    return user.lob_id == lob_id

async def check_report_ownership(user_id: int, report_id: int, db: AsyncSession) -> bool:
    """Check if user owns or has access to specific report"""
    from app.models.report import Report
    from app.models.user import User
    from sqlalchemy import select
    
    user_result = await db.execute(select(User).where(User.user_id == user_id))
    user = user_result.scalar_one_or_none()
    
    report_result = await db.execute(select(Report).where(Report.report_id == report_id))
    report = report_result.scalar_one_or_none()
    
    if not user or not report:
        return False
    
    # Admin has access to all reports
    if user.role == "Admin":
        return True
    
    # Report Owner has access to their own reports
    if user.role == "Report Owner" and report.report_owner_id == user_id:
        return True
    
    # Report Owner Executive has access to reports in their LOB
    if user.role == "Report Owner Executive" and report.lob_id == user.lob_id:
        return True
    
    # Test Manager and Tester have access through cycle assignments
    if user.role in ["Test Executive", "Tester"]:
        from app.models.cycle import Cycle, CycleReport
        cycle_reports_result = await db.execute(select(CycleReport).where(
            CycleReport.report_id == report_id
        ))
        cycle_reports = cycle_reports_result.scalars().all()
        for cycle_report in cycle_reports:
            cycle_result = await db.execute(select(Cycle).where(Cycle.cycle_id == cycle_report.cycle_id))
            cycle = cycle_result.scalar_one_or_none()
            if cycle and (cycle.test_manager_id == user_id or cycle_report.tester_id == user_id):
                return True
    
    return False

class AESEncryption:
    """AES-256 encryption implementation"""
    
    def __init__(self, master_key: Optional[bytes] = None):
        if master_key:
            self.master_key = master_key
        else:
            self.master_key = self._get_or_create_master_key()
    
    def _get_or_create_master_key(self) -> bytes:
        """Get existing master key or create new one"""
        key_file = "master.key"
        
        if os.path.exists(key_file):
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Generate new 256-bit key
            master_key = secrets.token_bytes(32)  # 32 bytes = 256 bits
            
            # Store securely (in production, use HSM or key management service)
            with open(key_file, "wb") as f:
                f.write(master_key)
            os.chmod(key_file, 0o600)  # Read-only for owner
            
            logger.info("Generated new AES-256 master key")
            return master_key
    
    def encrypt(self, plaintext: str, additional_data: Optional[str] = None) -> str:
        """Encrypt plaintext using AES-256-GCM"""
        try:
            # Generate random IV (12 bytes for GCM)
            iv = secrets.token_bytes(12)
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.master_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Add additional authenticated data if provided
            if additional_data:
                encryptor.authenticate_additional_data(additional_data.encode())
            
            # Encrypt the plaintext
            ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
            
            # Combine IV + ciphertext + tag
            encrypted_data = iv + ciphertext + encryptor.tag
            
            # Return base64 encoded result
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str, additional_data: Optional[str] = None) -> str:
        """Decrypt data encrypted with AES-256-GCM"""
        try:
            # Decode base64
            data = base64.b64decode(encrypted_data.encode())
            
            # Extract components
            iv = data[:12]  # First 12 bytes
            tag = data[-16:]  # Last 16 bytes
            ciphertext = data[12:-16]  # Everything in between
            
            # Create cipher
            cipher = Cipher(
                algorithms.AES(self.master_key),
                modes.GCM(iv, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            # Add additional authenticated data if provided
            if additional_data:
                decryptor.authenticate_additional_data(additional_data.encode())
            
            # Decrypt
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext.decode()
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise


class KeyManager:
    """Secure key management with rotation capability"""
    
    def __init__(self):
        self.encryption = AESEncryption()
        self.key_metadata: Dict[str, Any] = {}
    
    def store_key(self, key_id: str, key_value: str, metadata: Optional[Dict] = None) -> None:
        """Store a key with encryption and metadata"""
        try:
            # Encrypt the key value
            encrypted_key = self.encryption.encrypt(key_value, additional_data=key_id)
            
            # Store metadata
            self.key_metadata[key_id] = {
                "encrypted_value": encrypted_key,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "version": 1
            }
            
            logger.info(f"Stored encrypted key: {key_id}")
            
        except Exception as e:
            logger.error(f"Failed to store key {key_id}: {str(e)}")
            raise
    
    def retrieve_key(self, key_id: str) -> Optional[str]:
        """Retrieve and decrypt a stored key"""
        try:
            if key_id not in self.key_metadata:
                logger.warning(f"Key not found: {key_id}")
                return None
            
            key_data = self.key_metadata[key_id]
            encrypted_value = key_data["encrypted_value"]
            
            # Decrypt the key value
            decrypted_key = self.encryption.decrypt(encrypted_value, additional_data=key_id)
            
            logger.debug(f"Retrieved key: {key_id}")
            return decrypted_key
            
        except Exception as e:
            logger.error(f"Failed to retrieve key {key_id}: {str(e)}")
            return None
    
    def rotate_key(self, key_id: str, new_key_value: str) -> None:
        """Rotate a key to a new value"""
        try:
            if key_id not in self.key_metadata:
                raise ValueError(f"Key {key_id} does not exist")
            
            # Get current metadata
            current_metadata = self.key_metadata[key_id]["metadata"]
            current_version = self.key_metadata[key_id]["version"]
            
            # Store new version
            self.store_key(key_id, new_key_value, current_metadata)
            self.key_metadata[key_id]["version"] = current_version + 1
            self.key_metadata[key_id]["rotated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Rotated key: {key_id} to version {current_version + 1}")
            
        except Exception as e:
            logger.error(f"Failed to rotate key {key_id}: {str(e)}")
            raise


class SecureDataSource:
    """Secure data source credential management"""
    
    def __init__(self):
        self.key_manager = KeyManager()
    
    def store_credentials(self, data_source_id: int, credentials: Dict[str, str]) -> None:
        """Store data source credentials securely"""
        try:
            key_id = f"datasource_{data_source_id}"
            
            # Combine credentials into secure format
            credential_string = "|".join([
                f"{k}={v}" for k, v in credentials.items()
            ])
            
            metadata = {
                "data_source_id": data_source_id,
                "credential_types": list(credentials.keys()),
                "encrypted_at": datetime.utcnow().isoformat()
            }
            
            self.key_manager.store_key(key_id, credential_string, metadata)
            logger.info(f"Stored credentials for data source: {data_source_id}")
            
        except Exception as e:
            logger.error(f"Failed to store credentials for data source {data_source_id}: {str(e)}")
            raise
    
    def retrieve_credentials(self, data_source_id: int) -> Optional[Dict[str, str]]:
        """Retrieve and decrypt data source credentials"""
        try:
            key_id = f"datasource_{data_source_id}"
            credential_string = self.key_manager.retrieve_key(key_id)
            
            if not credential_string:
                return None
            
            # Parse credentials
            credentials = {}
            for item in credential_string.split("|"):
                if "=" in item:
                    key, value = item.split("=", 1)
                    credentials[key] = value
            
            logger.debug(f"Retrieved credentials for data source: {data_source_id}")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials for data source {data_source_id}: {str(e)}")
            return None


class SecurityAudit:
    """Security audit and monitoring"""
    
    @staticmethod
    def log_security_event(event_type: str, user_id: Optional[int], details: Dict[str, Any]) -> None:
        """Log security-related events"""
        security_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "severity": details.get("severity", "INFO")
        }
        
        logger.info(f"Security Event: {event_type} - {security_event}")
    
    @staticmethod
    def log_encryption_operation(operation: str, key_id: str, success: bool) -> None:
        """Log encryption/decryption operations"""
        SecurityAudit.log_security_event(
            "encryption_operation",
            None,
            {
                "operation": operation,
                "key_id": key_id,
                "success": success,
                "severity": "INFO" if success else "ERROR"
            }
        )
    
    @staticmethod
    def log_credential_access(data_source_id: int, user_id: Optional[int], access_type: str) -> None:
        """Log credential access events"""
        SecurityAudit.log_security_event(
            "credential_access",
            user_id,
            {
                "data_source_id": data_source_id,
                "access_type": access_type,
                "severity": "INFO"
            }
        )


# Global instances
encryption_service = AESEncryption()
key_manager = KeyManager()
secure_datasource = SecureDataSource()


def encrypt_data(plaintext: str) -> str:
    """Convenience function for data encryption"""
    return encryption_service.encrypt(plaintext)


def decrypt_data(encrypted_data: str) -> str:
    """Convenience function for data decryption"""
    return encryption_service.decrypt(encrypted_data) 