"""
Encryption utilities for sensitive data storage
Handles encryption/decryption of connection details and other sensitive information
"""

import os
import base64
import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""
    
    def __init__(self):
        self._cipher_suite: Optional[Fernet] = None
        self._initialize_cipher()
    
    def _initialize_cipher(self):
        """Initialize the cipher suite from environment variables"""
        try:
            # Get encryption key from environment
            encryption_key = os.getenv('SYNAPSE_ENCRYPTION_KEY')
            
            if not encryption_key:
                # Generate a key from password if no direct key provided
                password = os.getenv('SYNAPSE_DB_ENCRYPTION_PASSWORD', 'default-dev-password').encode()
                salt = os.getenv('SYNAPSE_ENCRYPTION_SALT', 'default-salt-change-in-prod').encode()
                
                # Derive key from password
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(password))
            else:
                key = encryption_key.encode()
            
            self._cipher_suite = Fernet(key)
            logger.info("Encryption service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {str(e)}")
            # In development, use a default key (NOT for production)
            if os.getenv('ENVIRONMENT', 'development') == 'development':
                default_key = Fernet.generate_key()
                self._cipher_suite = Fernet(default_key)
                logger.warning("Using default encryption key for development")
            else:
                raise
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt a dictionary to an encrypted string"""
        if not self._cipher_suite:
            raise RuntimeError("Encryption service not initialized")
        
        try:
            # Convert dict to JSON string
            json_str = json.dumps(data, sort_keys=True)
            
            # Encrypt the JSON string
            encrypted_bytes = self._cipher_suite.encrypt(json_str.encode())
            
            # Return base64 encoded string
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {str(e)}")
            raise
    
    def decrypt_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt an encrypted string back to a dictionary"""
        if not self._cipher_suite:
            raise RuntimeError("Encryption service not initialized")
        
        try:
            # Decode from base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            
            # Decrypt
            decrypted_bytes = self._cipher_suite.decrypt(encrypted_bytes)
            
            # Parse JSON
            json_str = decrypted_bytes.decode()
            return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            raise
    
    def encrypt_string(self, data: str) -> str:
        """Encrypt a string"""
        if not self._cipher_suite:
            raise RuntimeError("Encryption service not initialized")
        
        try:
            encrypted_bytes = self._cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
        except Exception as e:
            logger.error(f"String encryption failed: {str(e)}")
            raise
    
    def decrypt_string(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        if not self._cipher_suite:
            raise RuntimeError("Encryption service not initialized")
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_bytes = self._cipher_suite.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"String decryption failed: {str(e)}")
            raise
    
    def is_encrypted(self, data: str) -> bool:
        """Check if a string appears to be encrypted (basic heuristic)"""
        try:
            # Try to decode as base64
            base64.urlsafe_b64decode(data.encode())
            # If it's valid base64 and longer than typical plaintext, likely encrypted
            return len(data) > 50 and '=' in data
        except:
            return False

    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        return Fernet.generate_key().decode()


# Global encryption service instance
_encryption_service: Optional[EncryptionService] = None

def get_encryption_service() -> EncryptionService:
    """Get the global encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service


# Convenience functions
def encrypt_connection_details(connection_details: Dict[str, Any]) -> str:
    """Encrypt database connection details"""
    service = get_encryption_service()
    return service.encrypt_dict(connection_details)


def decrypt_connection_details(encrypted_details: str) -> Dict[str, Any]:
    """Decrypt database connection details"""
    service = get_encryption_service()
    return service.decrypt_dict(encrypted_details)


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Mask sensitive fields in connection details for logging"""
    masked = data.copy()
    sensitive_fields = ['password', 'secret', 'key', 'token', 'auth']
    
    for field in masked:
        if any(sensitive in field.lower() for sensitive in sensitive_fields):
            if isinstance(masked[field], str) and len(masked[field]) > 0:
                masked[field] = '*' * min(len(masked[field]), 8)
    
    return masked