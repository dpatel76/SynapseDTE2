"""
Data masking and security utilities for HRCI/Confidential data
Implements field-level encryption and dynamic masking
"""
from typing import Dict, Any, List, Optional, Union
from functools import wraps
from cryptography.fernet import Fernet
from hashlib import sha256
import re
import json
from datetime import datetime
import logging

from app.models.data_source import SecurityClassification
from app.models.user import User
from app.core.permissions import has_permission

logger = logging.getLogger(__name__)


class DataMaskingService:
    """Service for masking and unmasking sensitive data"""
    
    # Masking patterns by data type
    MASKING_PATTERNS = {
        'ssn': lambda x: f"XXX-XX-{x[-4:]}",
        'ein': lambda x: f"XX-XXX{x[-4:]}",
        'account': lambda x: f"****{x[-4:]}",
        'phone': lambda x: f"XXX-XXX-{x[-4:]}",
        'email': lambda x: f"{x[0]}***@{x.split('@')[1]}",
        'name': lambda x: f"{x[0]}{'*' * (len(x) - 2)}{x[-1]}",
        'address': lambda x: f"{'*' * 10}",
        'date': lambda x: "XX/XX/XXXX",
        'amount': lambda x: "$***.**",
        'default': lambda x: "*" * min(len(str(x)), 10)
    }
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize masking service with encryption key"""
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate key from environment or config
            key = Fernet.generate_key()
            self.cipher = Fernet(key)
    
    def mask_value(self, value: Any, data_type: str = 'default') -> str:
        """Mask a single value based on its type"""
        if value is None:
            return None
        
        str_value = str(value)
        pattern_func = self.MASKING_PATTERNS.get(data_type, self.MASKING_PATTERNS['default'])
        return pattern_func(str_value)
    
    def mask_dict(self, data: Dict[str, Any], sensitive_fields: List[str], 
                  field_types: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Mask sensitive fields in a dictionary"""
        masked_data = data.copy()
        field_types = field_types or {}
        
        for field in sensitive_fields:
            if field in masked_data and masked_data[field] is not None:
                data_type = field_types.get(field, 'default')
                masked_data[field] = self.mask_value(masked_data[field], data_type)
        
        return masked_data
    
    def encrypt_value(self, value: Any) -> str:
        """Encrypt a value for storage"""
        if value is None:
            return None
        
        str_value = json.dumps(value) if not isinstance(value, str) else value
        return self.cipher.encrypt(str_value.encode()).decode()
    
    def decrypt_value(self, encrypted_value: str, target_type: type = str) -> Any:
        """Decrypt a value from storage"""
        if encrypted_value is None:
            return None
        
        decrypted = self.cipher.decrypt(encrypted_value.encode()).decode()
        
        if target_type == str:
            return decrypted
        else:
            return json.loads(decrypted)
    
    def hash_value(self, value: Any) -> str:
        """Create a one-way hash for comparison without storing actual value"""
        if value is None:
            return None
        
        str_value = str(value)
        return sha256(str_value.encode()).hexdigest()


class FieldLevelSecurity:
    """Manages field-level security policies"""
    
    def __init__(self, masking_service: DataMaskingService):
        self.masking_service = masking_service
        self._field_policies = {}
    
    def register_field_policy(self, table: str, field: str, 
                            classification: SecurityClassification,
                            data_type: str = 'default'):
        """Register a security policy for a field"""
        key = f"{table}.{field}"
        self._field_policies[key] = {
            'classification': classification,
            'data_type': data_type
        }
    
    def should_mask(self, table: str, field: str, user: User, 
                   context: str = 'view') -> bool:
        """Determine if a field should be masked for a user"""
        key = f"{table}.{field}"
        policy = self._field_policies.get(key)
        
        if not policy:
            return False
        
        classification = policy['classification']
        
        # HRCI and Confidential are always masked by default
        if classification in [SecurityClassification.HRCI, SecurityClassification.CONFIDENTIAL]:
            # Check if user has explicit permission to view
            if context == 'view':
                return not has_permission(user, f"view_{classification.value.lower()}_data")
            elif context == 'export':
                # Never allow bulk export of HRCI/Confidential
                return True
        
        return False
    
    def apply_field_masking(self, data: Union[Dict, List[Dict]], table: str, 
                          user: User, context: str = 'view') -> Union[Dict, List[Dict]]:
        """Apply masking to data based on field policies"""
        if isinstance(data, list):
            return [self._mask_record(record, table, user, context) for record in data]
        else:
            return self._mask_record(data, table, user, context)
    
    def _mask_record(self, record: Dict[str, Any], table: str, 
                    user: User, context: str) -> Dict[str, Any]:
        """Mask a single record"""
        masked_record = record.copy()
        
        for field, value in record.items():
            if self.should_mask(table, field, user, context):
                key = f"{table}.{field}"
                policy = self._field_policies.get(key, {})
                data_type = policy.get('data_type', 'default')
                masked_record[field] = self.masking_service.mask_value(value, data_type)
        
        return masked_record


def secure_data_access(classification: SecurityClassification):
    """Decorator for securing data access based on classification"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from request context
            user = kwargs.get('current_user')
            if not user:
                raise PermissionError("User context required for secure data access")
            
            # Check permission based on classification
            if classification in [SecurityClassification.HRCI, SecurityClassification.CONFIDENTIAL]:
                if not has_permission(user, f"view_{classification.value.lower()}_data"):
                    # Log access attempt
                    logger.warning(
                        f"Unauthorized access attempt to {classification.value} data",
                        extra={
                            'user_id': user.user_id,
                            'function': func.__name__,
                            'timestamp': datetime.utcnow()
                        }
                    )
                    raise PermissionError(f"Insufficient permissions to access {classification.value} data")
            
            # Log successful access
            logger.info(
                f"Secure data access granted",
                extra={
                    'user_id': user.user_id,
                    'classification': classification.value,
                    'function': func.__name__,
                    'timestamp': datetime.utcnow()
                }
            )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


class SecureQueryBuilder:
    """Builds secure queries with automatic masking for sensitive fields"""
    
    def __init__(self, field_security: FieldLevelSecurity):
        self.field_security = field_security
    
    def build_select_query(self, table: str, columns: List[str], 
                          user: User, where_clause: Optional[str] = None) -> str:
        """Build a SELECT query with masking applied"""
        masked_columns = []
        
        for column in columns:
            if self.field_security.should_mask(table, column, user, 'view'):
                # Apply SQL-level masking
                masked_columns.append(f"'***MASKED***' AS {column}")
            else:
                masked_columns.append(column)
        
        query = f"SELECT {', '.join(masked_columns)} FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        return query
    
    def build_profiling_query(self, table: str, columns: List[str], 
                            where_clause: Optional[str] = None) -> str:
        """Build a profiling query that can access data without exposing it"""
        # For profiling, we need actual data but return only statistics
        statistical_columns = []
        
        for column in columns:
            # Generate statistical queries that don't expose actual values
            statistical_columns.extend([
                f"COUNT({column}) AS {column}_count",
                f"COUNT(DISTINCT {column}) AS {column}_distinct",
                f"MIN(LENGTH(CAST({column} AS VARCHAR))) AS {column}_min_length",
                f"MAX(LENGTH(CAST({column} AS VARCHAR))) AS {column}_max_length"
            ])
        
        query = f"SELECT {', '.join(statistical_columns)} FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        return query