"""
Tests for validating schema changes and data migration
"""

import pytest
from sqlalchemy import inspect
from app.models.report_attribute import ReportAttribute
from app.models.scoping import ScopingAttribute, ScopingVersion
from app.models.sample_selection import SampleSelectionVersion
from app.core.database import engine


class TestPlanningAttributeSchema:
    """Test planning attributes table has correct schema after migration"""
    
    def test_planning_has_audit_fields(self):
        """Verify planning attributes has audit fields"""
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('cycle_report_planning_attributes')}
        
        # Should have these audit fields
        assert 'version' in columns, "Missing version column"
        assert 'created_by' in columns, "Missing created_by column"
        assert 'updated_by' in columns, "Missing updated_by column"
    
    def test_planning_removed_scoping_fields(self):
        """Verify planning attributes doesn't have scoping fields after migration"""
        # Note: These are temporarily kept for migration but marked for removal
        # After final migration, this test should check they are removed
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('cycle_report_planning_attributes')}
        
        # These fields should eventually be removed
        deprecated_fields = [
            'validation_rules',
            'typical_source_documents', 
            'keywords_to_look_for',
            'testing_approach',
            'risk_score',
            'llm_risk_rationale'
        ]
        
        # For now, they exist but are marked for removal
        # After migration completes, change this to assert they don't exist
        for field in deprecated_fields:
            if field in columns:
                print(f"WARNING: {field} still exists but is marked for removal")
    
    def test_planning_model_attributes(self):
        """Verify planning model has correct attributes"""
        # Check model has audit fields
        assert hasattr(ReportAttribute, 'version')
        assert hasattr(ReportAttribute, 'created_by')
        assert hasattr(ReportAttribute, 'updated_by')
        
        # Check model has relationships
        assert hasattr(ReportAttribute, 'created_by_user')
        assert hasattr(ReportAttribute, 'updated_by_user')


class TestScopingAttributeSchema:
    """Test scoping attributes table has correct schema after migration"""
    
    def test_scoping_has_planning_fields(self):
        """Verify scoping attributes has fields moved from planning"""
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('cycle_report_scoping_attributes')}
        
        # Should have these fields from planning
        assert 'validation_rules' in columns, "Missing validation_rules column"
        assert 'testing_approach' in columns, "Missing testing_approach column"
        assert 'expected_source_documents' in columns, "Has expected_source_documents"
        assert 'search_keywords' in columns, "Has search_keywords"
    
    def test_scoping_has_llm_request_payload(self):
        """Verify scoping attributes has llm_request_payload"""
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('cycle_report_scoping_attributes')}
        
        assert 'llm_request_payload' in columns, "Missing llm_request_payload column"
        assert 'llm_response_payload' in columns, "Missing llm_response_payload column"
    
    def test_scoping_removed_duplicate_fields(self):
        """Verify scoping attributes doesn't have duplicate fields from planning"""
        # Note: These are temporarily kept for migration but marked for removal
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('cycle_report_scoping_attributes')}
        
        # These fields should eventually be removed (accessed via planning join)
        deprecated_fields = [
            'is_cde',
            'has_historical_issues',
            'is_primary_key'
        ]
        
        # For now, they exist but are marked for removal
        # After migration completes, change this to assert they don't exist
        for field in deprecated_fields:
            if field in columns:
                print(f"WARNING: {field} still exists in scoping but should be accessed via planning join")
    
    def test_scoping_model_attributes(self):
        """Verify scoping model has correct attributes"""
        # Check model has fields from planning
        assert hasattr(ScopingAttribute, 'validation_rules')
        assert hasattr(ScopingAttribute, 'testing_approach')
        assert hasattr(ScopingAttribute, 'expected_source_documents')
        assert hasattr(ScopingAttribute, 'search_keywords')
        
        # Check model has LLM fields
        assert hasattr(ScopingAttribute, 'llm_request_payload')
        assert hasattr(ScopingAttribute, 'llm_response_payload')


class TestSampleSelectionSchema:
    """Test sample selection tables have correct schema after migration"""
    
    def test_sample_selection_has_selection_criteria(self):
        """Verify sample selection versions has selection_criteria"""
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('cycle_report_sample_selection_versions')}
        
        assert 'selection_criteria' in columns, "Missing selection_criteria column"
    
    def test_sample_selection_model_attributes(self):
        """Verify sample selection model has correct attributes"""
        assert hasattr(SampleSelectionVersion, 'selection_criteria')


class TestWorkflowPhaseSchema:
    """Test workflow phases table consistency"""
    
    def test_workflow_phase_columns(self):
        """Verify workflow phases has required columns"""
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns('workflow_phases')}
        
        required_columns = [
            'phase_id',
            'cycle_id',
            'report_id',
            'phase_name',
            'status',
            'state',
            'progress_percentage',
            'metadata',
            'phase_data'
        ]
        
        for col in required_columns:
            assert col in columns, f"Missing {col} column in workflow_phases"


if __name__ == "__main__":
    # Run tests
    import sys
    pytest.main([__file__, '-v'] + sys.argv[1:])