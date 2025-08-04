"""
DEPRECATED: Legacy Test Execution Models

This module contains the deprecated test execution models that have been replaced
by the unified test execution architecture in test_execution_unified.py.

These models are kept for reference and potential migration scripts only.
Do not use these models in new code.

Migration Path:
- Legacy TestExecution -> Unified TestExecutionResult
- Legacy TestResultReview -> Unified TestExecutionReview
- Legacy TestExecutionAuditLog -> Unified TestExecutionAudit
- Legacy DocumentAnalysis -> Integrated into TestExecutionResult
- Legacy DatabaseTest -> Integrated into TestExecutionResult
- Legacy TestComparison -> Removed (use analytics endpoints)
- Legacy BulkTestExecution -> Removed (use bulk execution endpoints)
"""

import warnings
from datetime import datetime

# Deprecation warning for this module
warnings.warn(
    "test_execution_legacy module is deprecated. Use test_execution_unified instead.",
    DeprecationWarning,
    stacklevel=2
)

# Legacy models have been moved to avoid conflicts
# Original models are preserved in migration scripts for reference
# All functionality has been replaced by the unified architecture

def get_migration_mapping():
    """
    Get the mapping between legacy and unified models for migration scripts
    """
    return {
        'legacy_to_unified': {
            'TestExecution': 'TestExecutionResult',
            'TestResultReview': 'TestExecutionReview', 
            'TestExecutionAuditLog': 'TestExecutionAudit',
            'DocumentAnalysis': 'TestExecutionResult.analysis_results',
            'DatabaseTest': 'TestExecutionResult.analysis_results',
            'TestComparison': 'Analytics API',
            'BulkTestExecution': 'Bulk Execution API'
        },
        'field_mappings': {
            'TestExecution': {
                'execution_id': 'id',
                'sample_record_id': 'test_case_id',
                'attribute_id': 'evidence_id',
                'test_type': 'test_type',
                'analysis_method': 'analysis_method',
                'status': 'execution_status',
                'result': 'test_result',
                'confidence_score': 'llm_confidence_score',
                'execution_summary': 'execution_summary',
                'error_message': 'error_message',
                'started_at': 'started_at',
                'completed_at': 'completed_at',
                'processing_time_ms': 'processing_time_ms',
                'executed_by': 'executed_by'
            },
            'TestResultReview': {
                'review_id': 'id',
                'execution_id': 'execution_id',
                'reviewer_id': 'reviewed_by',
                'review_result': 'review_status',
                'reviewer_comments': 'reviewer_comments',
                'recommended_action': 'recommended_action',
                'requires_retest': 'requires_retest',
                'accuracy_score': 'accuracy_score',
                'completeness_score': 'completeness_score',
                'consistency_score': 'consistency_score',
                'overall_score': 'overall_score',
                'review_criteria_used': 'review_criteria_used',
                'reviewed_at': 'reviewed_at'
            },
            'TestExecutionAuditLog': {
                'log_id': 'id',
                'cycle_id': 'execution_id',  # Context changes
                'report_id': 'execution_id',  # Context changes
                'phase_id': 'execution_id',   # Context changes
                'action': 'action',
                'entity_type': 'action_details',
                'entity_id': 'action_details',
                'performed_by': 'performed_by',
                'performed_at': 'performed_at',
                'old_values': 'previous_status',
                'new_values': 'new_status',
                'notes': 'change_reason'
            }
        }
    }


def get_deprecated_tables():
    """
    Get list of deprecated tables that have been removed
    """
    return [
        'cycle_report_test_executions',
        'cycle_report_test_execution_document_analyses',
        'cycle_report_test_execution_database_tests',
        'test_result_reviews',
        'test_comparisons',
        'bulk_test_executions',
        'test_execution_audit_logs'
    ]


def get_deprecated_enums():
    """
    Get list of deprecated PostgreSQL ENUMs that have been removed
    """
    return [
        'test_type_enum',
        'test_status_enum',
        'test_result_enum',
        'analysis_method_enum',
        'review_status_enum'
    ]


class LegacyTestExecutionMigrationHelper:
    """
    Helper class for migrating data from legacy test execution models
    to the unified architecture
    """
    
    @staticmethod
    def migrate_test_execution_data(legacy_data: dict) -> dict:
        """
        Migrate legacy TestExecution data to unified TestExecutionResult format
        """
        mapping = get_migration_mapping()['field_mappings']['TestExecution']
        
        unified_data = {}
        for legacy_field, unified_field in mapping.items():
            if legacy_field in legacy_data:
                unified_data[unified_field] = legacy_data[legacy_field]
        
        # Handle special conversions
        if 'sample_record_id' in legacy_data:
            unified_data['test_case_id'] = f"tc_{legacy_data['sample_record_id']}"
        
        if 'attribute_id' in legacy_data:
            # Evidence ID needs to be looked up from the Request for Information phase
            unified_data['evidence_id'] = legacy_data['attribute_id']  # Placeholder
        
        # Set default values for new fields
        unified_data.update({
            'execution_number': 1,
            'is_latest_execution': True,
            'execution_reason': 'migrated_from_legacy',
            'analysis_results': {},
            'evidence_validation_status': 'valid',
            'evidence_version_number': 1,
            'execution_method': 'automatic',
            'retry_count': 0
        })
        
        return unified_data
    
    @staticmethod
    def migrate_review_data(legacy_data: dict) -> dict:
        """
        Migrate legacy TestResultReview data to unified TestExecutionReview format
        """
        mapping = get_migration_mapping()['field_mappings']['TestResultReview']
        
        unified_data = {}
        for legacy_field, unified_field in mapping.items():
            if legacy_field in legacy_data:
                unified_data[unified_field] = legacy_data[legacy_field]
        
        # Set default values for new fields
        unified_data.update({
            'phase_id': 1,  # This needs to be looked up
            'review_notes': legacy_data.get('reviewer_comments', ''),
            'escalation_required': False,
            'escalation_reason': ''
        })
        
        return unified_data
    
    @staticmethod
    def migrate_audit_data(legacy_data: dict) -> dict:
        """
        Migrate legacy TestExecutionAuditLog data to unified TestExecutionAudit format
        """
        mapping = get_migration_mapping()['field_mappings']['TestExecutionAuditLog']
        
        unified_data = {}
        for legacy_field, unified_field in mapping.items():
            if legacy_field in legacy_data:
                if unified_field == 'action_details':
                    # Combine multiple legacy fields into action_details
                    if 'action_details' not in unified_data:
                        unified_data['action_details'] = {}
                    unified_data['action_details'][legacy_field] = legacy_data[legacy_field]
                else:
                    unified_data[unified_field] = legacy_data[legacy_field]
        
        # Set default values for new fields
        unified_data.update({
            'execution_id': legacy_data.get('entity_id', 1),  # This needs proper mapping
            'system_info': {
                'migrated_from': 'legacy_audit_log',
                'original_cycle_id': legacy_data.get('cycle_id'),
                'original_report_id': legacy_data.get('report_id'),
                'original_phase_id': legacy_data.get('phase_id')
            }
        })
        
        return unified_data


# Usage example for migration scripts:
"""
# Example migration script usage:

from app.models.test_execution_legacy import LegacyTestExecutionMigrationHelper

# Migrate legacy test execution data
legacy_execution = {
    'execution_id': 123,
    'sample_record_id': 'sample_001',
    'attribute_id': 456,
    'test_type': 'Document Based',
    'analysis_method': 'LLM Analysis',
    'status': 'Completed',
    'result': 'Pass',
    'confidence_score': 0.95,
    'execution_summary': 'Test completed successfully',
    'started_at': datetime.now(),
    'completed_at': datetime.now(),
    'processing_time_ms': 1500,
    'executed_by': 789
}

unified_data = LegacyTestExecutionMigrationHelper.migrate_test_execution_data(legacy_execution)
# Use unified_data to create new TestExecutionResult record
"""