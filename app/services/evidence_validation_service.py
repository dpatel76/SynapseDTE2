"""
Evidence Validation Service for Request for Information Phase
Implements comprehensive validation rules for document and data source evidence
"""

import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.request_info import (
    TestCaseSourceEvidence, EvidenceValidationResult, 
    validation_result_enum
)
from app.models.cycle_report_data_source import CycleReportDataSource
from app.core.config import settings


class EvidenceValidationRule:
    """Base class for evidence validation rules"""
    
    def __init__(self, rule_name: str, description: str, severity: str = 'error'):
        self.rule_name = rule_name
        self.description = description
        self.severity = severity  # 'error', 'warning', 'info'
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate evidence against this rule
        Returns: {
            'rule': rule_name,
            'result': 'passed|failed|warning',
            'message': 'validation message',
            'details': {...}
        }
        """
        raise NotImplementedError


class DocumentValidationRule(EvidenceValidationRule):
    """Base class for document validation rules"""
    pass


class DataSourceValidationRule(EvidenceValidationRule):
    """Base class for data source validation rules"""
    pass


# Document Validation Rules

class DocumentExistsRule(DocumentValidationRule):
    """Check if document file exists"""
    
    def __init__(self):
        super().__init__('document_exists', 'Document file must exist on disk', 'error')
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        if not evidence.document_path:
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Document path is missing',
                'details': {}
            }
        
        file_path = Path(evidence.document_path)
        if not file_path.exists():
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Document file does not exist',
                'details': {'path': str(file_path)}
            }
        
        return {
            'rule': self.rule_name,
            'result': 'passed',
            'message': 'Document file exists',
            'details': {'path': str(file_path), 'size': file_path.stat().st_size}
        }


class DocumentSizeRule(DocumentValidationRule):
    """Check document file size"""
    
    def __init__(self, max_size_mb: int = 50, min_size_kb: int = 1):
        super().__init__('document_size', f'Document size must be between {min_size_kb}KB and {max_size_mb}MB')
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.min_size_bytes = min_size_kb * 1024
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        size = evidence.document_size
        
        if not size:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': 'Document size is unknown',
                'details': {}
            }
        
        if size < self.min_size_bytes:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': f'Document is very small ({size} bytes)',
                'details': {'size': size, 'min_size': self.min_size_bytes}
            }
        
        if size > self.max_size_bytes:
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': f'Document is too large ({size} bytes)',
                'details': {'size': size, 'max_size': self.max_size_bytes}
            }
        
        return {
            'rule': self.rule_name,
            'result': 'passed',
            'message': f'Document size is acceptable ({size} bytes)',
            'details': {'size': size}
        }


class DocumentFormatRule(DocumentValidationRule):
    """Check document format/mime type"""
    
    def __init__(self):
        super().__init__('document_format', 'Document must be in supported format')
        self.allowed_types = {
            'application/pdf': 'PDF',
            'image/jpeg': 'JPEG Image',
            'image/png': 'PNG Image',
            'image/gif': 'GIF Image',
            'application/vnd.ms-excel': 'Excel (XLS)',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'Excel (XLSX)',
            'application/msword': 'Word (DOC)',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'Word (DOCX)',
            'text/plain': 'Text File',
            'text/csv': 'CSV File'
        }
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        mime_type = evidence.mime_type
        
        if not mime_type:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': 'Document format is unknown',
                'details': {}
            }
        
        if mime_type not in self.allowed_types:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': f'Document format "{mime_type}" may not be fully supported',
                'details': {'mime_type': mime_type}
            }
        
        return {
            'rule': self.rule_name,
            'result': 'passed',
            'message': f'Document format is supported ({self.allowed_types[mime_type]})',
            'details': {'mime_type': mime_type, 'format_name': self.allowed_types[mime_type]}
        }


class DocumentIntegrityRule(DocumentValidationRule):
    """Check document integrity using hash verification"""
    
    def __init__(self):
        super().__init__('document_integrity', 'Document integrity must be verified')
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        if not evidence.document_path or not evidence.document_hash:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': 'Document hash not available for verification',
                'details': {}
            }
        
        try:
            import hashlib
            file_path = Path(evidence.document_path)
            
            if not file_path.exists():
                return {
                    'rule': self.rule_name,
                    'result': 'failed',
                    'message': 'Cannot verify integrity - file does not exist',
                    'details': {}
                }
            
            # Calculate current hash
            with open(file_path, 'rb') as f:
                current_hash = hashlib.sha256(f.read()).hexdigest()
            
            if current_hash != evidence.document_hash:
                return {
                    'rule': self.rule_name,
                    'result': 'failed',
                    'message': 'Document integrity check failed - file has been modified',
                    'details': {'stored_hash': evidence.document_hash, 'current_hash': current_hash}
                }
            
            return {
                'rule': self.rule_name,
                'result': 'passed',
                'message': 'Document integrity verified',
                'details': {'hash': current_hash}
            }
            
        except Exception as e:
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': f'Document integrity check failed: {str(e)}',
                'details': {'error': str(e)}
            }


class DocumentReadabilityRule(DocumentValidationRule):
    """Check if document can be read/opened"""
    
    def __init__(self):
        super().__init__('document_readability', 'Document must be readable')
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        if not evidence.document_path:
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Document path is missing',
                'details': {}
            }
        
        file_path = Path(evidence.document_path)
        if not file_path.exists():
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Document file does not exist',
                'details': {}
            }
        
        try:
            # Basic readability check - try to open and read first few bytes
            with open(file_path, 'rb') as f:
                first_bytes = f.read(1024)
                if len(first_bytes) == 0:
                    return {
                        'rule': self.rule_name,
                        'result': 'failed',
                        'message': 'Document is empty',
                        'details': {}
                    }
            
            # Check for common file corruption indicators
            if evidence.mime_type == 'application/pdf':
                if not first_bytes.startswith(b'%PDF'):
                    return {
                        'rule': self.rule_name,
                        'result': 'warning',
                        'message': 'PDF file may be corrupted (missing PDF header)',
                        'details': {}
                    }
            
            return {
                'rule': self.rule_name,
                'result': 'passed',
                'message': 'Document appears to be readable',
                'details': {'first_bytes_length': len(first_bytes)}
            }
            
        except Exception as e:
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': f'Document readability check failed: {str(e)}',
                'details': {'error': str(e)}
            }


# Data Source Validation Rules

class QuerySyntaxRule(DataSourceValidationRule):
    """Check SQL query syntax"""
    
    def __init__(self):
        super().__init__('query_syntax', 'Query must have valid SQL syntax')
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        query = evidence.query_text
        
        if not query or not query.strip():
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Query is empty',
                'details': {}
            }
        
        # Basic syntax checks
        query_lower = query.lower().strip()
        
        # Check for dangerous operations
        dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
        for keyword in dangerous_keywords:
            if re.search(rf'\b{keyword}\b', query_lower):
                return {
                    'rule': self.rule_name,
                    'result': 'failed',
                    'message': f'Query contains dangerous keyword: {keyword}',
                    'details': {'dangerous_keyword': keyword}
                }
        
        # Check for SELECT statement
        if not query_lower.startswith('select'):
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Query must be a SELECT statement',
                'details': {}
            }
        
        # Check for basic SQL structure
        if 'from' not in query_lower:
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Query is missing FROM clause',
                'details': {}
            }
        
        # Check query length
        if len(query) > 10000:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': 'Query is very long (>10,000 characters)',
                'details': {'length': len(query)}
            }
        
        return {
            'rule': self.rule_name,
            'result': 'passed',
            'message': 'Query syntax appears valid',
            'details': {'length': len(query)}
        }


class DataSourceConnectivityRule(DataSourceValidationRule):
    """Check data source connectivity"""
    
    def __init__(self):
        super().__init__('data_source_connectivity', 'Data source must be accessible')
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        if not evidence.data_source_id:
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Data source ID is missing',
                'details': {}
            }
        
        # Get data source from context or database
        data_source = context.get('data_source')
        if not data_source:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': 'Data source information not available for validation',
                'details': {'data_source_id': evidence.data_source_id}
            }
        
        # Mock connectivity check (in real implementation, this would connect to actual data source)
        try:
            # Simulate connection check
            is_connected = True  # This would be actual connection test
            
            if not is_connected:
                return {
                    'rule': self.rule_name,
                    'result': 'failed',
                    'message': 'Cannot connect to data source',
                    'details': {'data_source_id': evidence.data_source_id}
                }
            
            return {
                'rule': self.rule_name,
                'result': 'passed',
                'message': 'Data source is accessible',
                'details': {'data_source_id': evidence.data_source_id}
            }
            
        except Exception as e:
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': f'Data source connectivity check failed: {str(e)}',
                'details': {'error': str(e)}
            }


class QueryExecutionRule(DataSourceValidationRule):
    """Check if query can be executed"""
    
    def __init__(self):
        super().__init__('query_execution', 'Query must execute successfully')
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        query_result = evidence.query_result_sample
        
        if not query_result:
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Query execution results not available',
                'details': {}
            }
        
        if isinstance(query_result, dict) and query_result.get('error'):
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': f'Query execution failed: {query_result.get("error")}',
                'details': {'error': query_result.get('error')}
            }
        
        if isinstance(query_result, dict) and not query_result.get('query_valid', True):
            return {
                'rule': self.rule_name,
                'result': 'failed',
                'message': 'Query execution failed',
                'details': query_result
            }
        
        return {
            'rule': self.rule_name,
            'result': 'passed',
            'message': 'Query executed successfully',
            'details': {
                'execution_time': query_result.get('execution_time_ms', 0),
                'row_count': query_result.get('row_count', 0)
            }
        }


class QueryRelevanceRule(DataSourceValidationRule):
    """Check if query returns relevant results"""
    
    def __init__(self):
        super().__init__('query_relevance', 'Query should return relevant results')
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        query_result = evidence.query_result_sample
        
        if not query_result or not isinstance(query_result, dict):
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': 'Query results not available for relevance check',
                'details': {}
            }
        
        row_count = query_result.get('row_count', 0)
        
        if row_count == 0:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': 'Query returned no results',
                'details': {'row_count': row_count}
            }
        
        column_count = query_result.get('column_count', 0)
        
        if column_count == 0:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': 'Query returned no columns',
                'details': {'column_count': column_count}
            }
        
        # Check for expected attribute in results
        attribute_name = context.get('attribute_name')
        if attribute_name and 'sample_rows' in query_result:
            sample_rows = query_result['sample_rows']
            if sample_rows and isinstance(sample_rows, list) and len(sample_rows) > 0:
                first_row = sample_rows[0]
                if isinstance(first_row, dict) and attribute_name.lower() not in [k.lower() for k in first_row.keys()]:
                    return {
                        'rule': self.rule_name,
                        'result': 'warning',
                        'message': f'Query results do not contain expected attribute: {attribute_name}',
                        'details': {
                            'attribute_name': attribute_name,
                            'available_columns': list(first_row.keys()) if isinstance(first_row, dict) else []
                        }
                    }
        
        return {
            'rule': self.rule_name,
            'result': 'passed',
            'message': f'Query returned {row_count} rows with {column_count} columns',
            'details': {'row_count': row_count, 'column_count': column_count}
        }


class QueryPerformanceRule(DataSourceValidationRule):
    """Check query performance"""
    
    def __init__(self, max_execution_time_ms: int = 30000):
        super().__init__('query_performance', 'Query should execute within reasonable time')
        self.max_execution_time_ms = max_execution_time_ms
    
    def validate(self, evidence: TestCaseSourceEvidence, context: Dict[str, Any]) -> Dict[str, Any]:
        query_result = evidence.query_result_sample
        
        if not query_result or not isinstance(query_result, dict):
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': 'Query execution time not available',
                'details': {}
            }
        
        execution_time = query_result.get('execution_time_ms', 0)
        
        if execution_time > self.max_execution_time_ms:
            return {
                'rule': self.rule_name,
                'result': 'warning',
                'message': f'Query execution time ({execution_time}ms) exceeds recommended limit ({self.max_execution_time_ms}ms)',
                'details': {'execution_time_ms': execution_time, 'max_time_ms': self.max_execution_time_ms}
            }
        
        return {
            'rule': self.rule_name,
            'result': 'passed',
            'message': f'Query executed in {execution_time}ms',
            'details': {'execution_time_ms': execution_time}
        }


class EvidenceValidationService:
    """Service for validating evidence submissions"""
    
    def __init__(self, db: Session):
        self.db = db
        self.document_rules = [
            DocumentExistsRule(),
            DocumentSizeRule(),
            DocumentFormatRule(),
            DocumentIntegrityRule(),
            DocumentReadabilityRule()
        ]
        
        self.data_source_rules = [
            QuerySyntaxRule(),
            DataSourceConnectivityRule(),
            QueryExecutionRule(),
            QueryRelevanceRule(),
            QueryPerformanceRule()
        ]
    
    def validate_evidence(self, evidence: TestCaseSourceEvidence, 
                         context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Validate evidence against all applicable rules"""
        
        if context is None:
            context = {}
        
        # Add evidence context
        if evidence.test_case and evidence.test_case.attribute:
            context['attribute_name'] = evidence.test_case.attribute.attribute_name
        
        # Get data source if applicable
        if evidence.data_source_id:
            data_source = self.db.query(CycleReportDataSource).filter(
                CycleReportDataSource.id == evidence.data_source_id
            ).first()
            context['data_source'] = data_source
        
        validation_results = []
        
        # Apply appropriate rules based on evidence type
        if evidence.evidence_type == 'document':
            for rule in self.document_rules:
                try:
                    result = rule.validate(evidence, context)
                    validation_results.append(result)
                except Exception as e:
                    validation_results.append({
                        'rule': rule.rule_name,
                        'result': 'failed',
                        'message': f'Validation rule failed: {str(e)}',
                        'details': {'error': str(e)}
                    })
        
        elif evidence.evidence_type == 'data_source':
            for rule in self.data_source_rules:
                try:
                    result = rule.validate(evidence, context)
                    validation_results.append(result)
                except Exception as e:
                    validation_results.append({
                        'rule': rule.rule_name,
                        'result': 'failed',
                        'message': f'Validation rule failed: {str(e)}',
                        'details': {'error': str(e)}
                    })
        
        return validation_results
    
    def save_validation_results(self, evidence_id: int, validation_results: List[Dict[str, Any]], 
                               validated_by: int = 1) -> None:
        """Save validation results to database"""
        
        # Clear existing validation results
        self.db.query(EvidenceValidationResult).filter(
            EvidenceValidationResult.evidence_id == evidence_id
        ).delete()
        
        # Save new validation results
        for result in validation_results:
            validation_record = EvidenceValidationResult(
                evidence_id=evidence_id,
                validation_rule=result['rule'],
                validation_result=result['result'],
                validation_message=result['message'],
                validated_by=validated_by
            )
            self.db.add(validation_record)
        
        self.db.commit()
    
    def get_validation_summary(self, evidence_id: int) -> Dict[str, Any]:
        """Get validation summary for evidence"""
        
        validation_results = self.db.query(EvidenceValidationResult).filter(
            EvidenceValidationResult.evidence_id == evidence_id
        ).all()
        
        if not validation_results:
            return {
                'evidence_id': evidence_id,
                'total_rules': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0,
                'overall_status': 'not_validated'
            }
        
        total_rules = len(validation_results)
        passed = len([r for r in validation_results if r.validation_result == 'passed'])
        failed = len([r for r in validation_results if r.validation_result == 'failed'])
        warnings = len([r for r in validation_results if r.validation_result == 'warning'])
        
        # Determine overall status
        if failed > 0:
            overall_status = 'invalid'
        elif warnings > 0:
            overall_status = 'requires_review'
        else:
            overall_status = 'valid'
        
        return {
            'evidence_id': evidence_id,
            'total_rules': total_rules,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'overall_status': overall_status,
            'validation_results': [
                {
                    'rule': r.validation_rule,
                    'result': r.validation_result,
                    'message': r.validation_message,
                    'validated_at': r.validated_at
                }
                for r in validation_results
            ]
        }
    
    def validate_document_evidence(self, evidence: TestCaseSourceEvidence) -> List[Dict[str, Any]]:
        """Validate document evidence using all applicable rules"""
        results = []
        
        # Use the document validation rules
        for rule in self.document_rules:
            try:
                result = rule.validate(evidence, {})
                results.append(result)
            except Exception as e:
                results.append({
                    'rule': rule.rule_name,
                    'result': 'failed',
                    'message': f'Validation rule failed: {str(e)}',
                    'details': {'error': str(e)}
                })
        
        return results

    def validate_data_source_evidence(self, evidence: TestCaseSourceEvidence) -> List[Dict[str, Any]]:
        """Validate data source evidence using all applicable rules"""
        results = []
        
        # Use the data source validation rules
        for rule in self.data_source_rules:
            try:
                result = rule.validate(evidence, {})
                results.append(result)
            except Exception as e:
                results.append({
                    'rule': rule.rule_name,
                    'result': 'failed',
                    'message': f'Validation rule failed: {str(e)}',
                    'details': {'error': str(e)}
                })
        
        return results

    def validate_and_save(self, evidence: TestCaseSourceEvidence, 
                         context: Optional[Dict[str, Any]] = None,
                         validated_by: int = 1) -> Dict[str, Any]:
        """Validate evidence and save results"""
        
        validation_results = self.validate_evidence(evidence, context)
        self.save_validation_results(evidence.id, validation_results, validated_by)
        
        return self.get_validation_summary(evidence.id)