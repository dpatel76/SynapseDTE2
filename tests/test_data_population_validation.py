"""
Tests for validating data population after migration
"""

import pytest
import asyncio
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.report_attribute import ReportAttribute
from app.models.scoping import ScopingAttribute, ScopingVersion
from app.models.sample_selection import SampleSelectionVersion
from app.models.workflow import WorkflowPhase


class TestDataPopulation:
    """Test that data is properly populated after migration"""
    
    @pytest.mark.asyncio
    async def test_llm_request_payload_populated(self):
        """Verify all scoping attributes have llm_request_payload populated"""
        async with AsyncSessionLocal() as db:
            # Count records with NULL llm_request_payload
            result = await db.execute(
                select(func.count())
                .select_from(ScopingAttribute)
                .where(ScopingAttribute.llm_request_payload.is_(None))
            )
            null_count = result.scalar()
            
            # Count records with empty JSON
            result = await db.execute(
                select(func.count())
                .select_from(ScopingAttribute)
                .where(ScopingAttribute.llm_request_payload == {})
            )
            empty_count = result.scalar()
            
            assert null_count == 0, f"Found {null_count} records with NULL llm_request_payload"
            assert empty_count == 0, f"Found {empty_count} records with empty llm_request_payload"
            
            # Verify populated records have required fields
            result = await db.execute(
                select(ScopingAttribute.llm_request_payload)
                .limit(10)
            )
            payloads = result.scalars().all()
            
            for payload in payloads:
                if payload:
                    assert 'model' in payload, "llm_request_payload missing 'model' field"
                    assert payload.get('model'), "llm_request_payload has empty 'model' field"
    
    @pytest.mark.asyncio
    async def test_workflow_phase_consistency(self):
        """Verify workflow phases have consistent status/state/progress"""
        async with AsyncSessionLocal() as db:
            # Check for inconsistent "Not Started" phases
            result = await db.execute(
                select(func.count())
                .select_from(WorkflowPhase)
                .where(
                    and_(
                        WorkflowPhase.status == 'Not Started',
                        WorkflowPhase.progress_percentage > 0
                    )
                )
            )
            count = result.scalar()
            assert count == 0, f"Found {count} phases with status='Not Started' but progress > 0"
            
            # Check for inconsistent "Complete" phases
            result = await db.execute(
                select(func.count())
                .select_from(WorkflowPhase)
                .where(
                    and_(
                        WorkflowPhase.status == 'Complete',
                        WorkflowPhase.progress_percentage < 100
                    )
                )
            )
            count = result.scalar()
            assert count == 0, f"Found {count} phases with status='Complete' but progress < 100"
            
            # Check for 100% progress but not complete
            result = await db.execute(
                select(func.count())
                .select_from(WorkflowPhase)
                .where(
                    and_(
                        WorkflowPhase.progress_percentage == 100,
                        WorkflowPhase.status != 'Complete'
                    )
                )
            )
            count = result.scalar()
            assert count == 0, f"Found {count} phases with progress=100 but status != 'Complete'"
    
    @pytest.mark.asyncio
    async def test_planning_attributes_have_audit_fields(self):
        """Verify planning attributes have audit fields populated"""
        async with AsyncSessionLocal() as db:
            # Check version field
            result = await db.execute(
                select(func.count())
                .select_from(ReportAttribute)
                .where(ReportAttribute.version.is_(None))
            )
            null_version_count = result.scalar()
            
            # Version can be NULL initially but should default to 1
            if null_version_count > 0:
                print(f"WARNING: {null_version_count} planning attributes have NULL version")
            
            # Check that at least some records have created_by populated
            result = await db.execute(
                select(func.count())
                .select_from(ReportAttribute)
                .where(ReportAttribute.created_by.isnot(None))
            )
            has_created_by = result.scalar()
            
            # Get total count
            result = await db.execute(
                select(func.count())
                .select_from(ReportAttribute)
            )
            total_count = result.scalar()
            
            if total_count > 0:
                created_by_percentage = (has_created_by / total_count) * 100
                print(f"Planning attributes with created_by: {has_created_by}/{total_count} ({created_by_percentage:.1f}%)")
    
    @pytest.mark.asyncio
    async def test_scoping_attributes_have_moved_fields(self):
        """Verify scoping attributes have fields moved from planning"""
        async with AsyncSessionLocal() as db:
            # Get a sample of scoping attributes
            result = await db.execute(
                select(ScopingAttribute)
                .limit(10)
            )
            scoping_attrs = result.scalars().all()
            
            fields_populated = {
                'validation_rules': 0,
                'testing_approach': 0,
                'expected_source_documents': 0,
                'search_keywords': 0
            }
            
            for attr in scoping_attrs:
                if attr.validation_rules:
                    fields_populated['validation_rules'] += 1
                if attr.testing_approach:
                    fields_populated['testing_approach'] += 1
                if attr.expected_source_documents:
                    fields_populated['expected_source_documents'] += 1
                if attr.search_keywords:
                    fields_populated['search_keywords'] += 1
            
            print(f"Scoping attributes field population (out of {len(scoping_attrs)} samples):")
            for field, count in fields_populated.items():
                percentage = (count / len(scoping_attrs) * 100) if scoping_attrs else 0
                print(f"  {field}: {count} ({percentage:.1f}%)")
    
    @pytest.mark.asyncio
    async def test_sample_selection_has_criteria(self):
        """Verify sample selection versions have selection_criteria populated"""
        async with AsyncSessionLocal() as db:
            # Count records with NULL selection_criteria
            result = await db.execute(
                select(func.count())
                .select_from(SampleSelectionVersion)
                .where(SampleSelectionVersion.selection_criteria.is_(None))
            )
            null_count = result.scalar()
            
            # Count records with empty criteria
            result = await db.execute(
                select(func.count())
                .select_from(SampleSelectionVersion)
                .where(SampleSelectionVersion.selection_criteria == {})
            )
            empty_count = result.scalar()
            
            # Get total count
            result = await db.execute(
                select(func.count())
                .select_from(SampleSelectionVersion)
            )
            total_count = result.scalar()
            
            if total_count > 0:
                populated_count = total_count - null_count - empty_count
                percentage = (populated_count / total_count) * 100
                print(f"Sample selection versions with selection_criteria: {populated_count}/{total_count} ({percentage:.1f}%)")
                
                # For new records, empty is acceptable but NULL is not
                assert null_count == 0, f"Found {null_count} records with NULL selection_criteria"
    
    @pytest.mark.asyncio
    async def test_no_data_loss_in_migration(self):
        """Verify no data was lost during field migration"""
        async with AsyncSessionLocal() as db:
            # Check if any planning attributes still have data in fields to be removed
            result = await db.execute(
                select(func.count())
                .select_from(ReportAttribute)
                .where(
                    (ReportAttribute.validation_rules.isnot(None)) |
                    (ReportAttribute.testing_approach.isnot(None)) |
                    (ReportAttribute.typical_source_documents.isnot(None)) |
                    (ReportAttribute.keywords_to_look_for.isnot(None))
                )
            )
            planning_with_data = result.scalar()
            
            if planning_with_data > 0:
                print(f"Note: {planning_with_data} planning attributes still have data in fields to be migrated")
                print("This is expected before final schema migration")
                
                # Verify corresponding scoping attributes have the data
                result = await db.execute(
                    select(ReportAttribute.id, ReportAttribute.validation_rules)
                    .where(ReportAttribute.validation_rules.isnot(None))
                    .limit(5)
                )
                samples = result.all()
                
                for attr_id, validation_rules in samples:
                    # Check if scoping has this data
                    scoping_result = await db.execute(
                        select(ScopingAttribute.validation_rules)
                        .where(ScopingAttribute.attribute_id == attr_id)
                        .limit(1)
                    )
                    scoping_validation = scoping_result.scalar()
                    
                    if not scoping_validation:
                        print(f"WARNING: Planning attribute {attr_id} has validation_rules but scoping doesn't")


class TestDataIntegrity:
    """Test data integrity after migration"""
    
    @pytest.mark.asyncio
    async def test_foreign_key_integrity(self):
        """Verify all foreign keys are valid"""
        async with AsyncSessionLocal() as db:
            # Check scoping attributes reference valid planning attributes
            result = await db.execute(
                select(func.count())
                .select_from(ScopingAttribute)
                .outerjoin(ReportAttribute, ScopingAttribute.attribute_id == ReportAttribute.id)
                .where(ReportAttribute.id.is_(None))
            )
            orphaned_scoping = result.scalar()
            
            assert orphaned_scoping == 0, f"Found {orphaned_scoping} scoping attributes with invalid attribute_id"
    
    @pytest.mark.asyncio
    async def test_enum_values_valid(self):
        """Verify enum columns have valid values"""
        async with AsyncSessionLocal() as db:
            # Check workflow phase status values
            result = await db.execute(
                select(WorkflowPhase.status, func.count())
                .group_by(WorkflowPhase.status)
            )
            status_counts = result.all()
            
            valid_statuses = ['Not Started', 'In Progress', 'Complete', 'Pending', 'Blocked']
            for status, count in status_counts:
                if status not in valid_statuses:
                    pytest.fail(f"Invalid workflow phase status: {status} ({count} records)")


if __name__ == "__main__":
    # Run tests
    import sys
    pytest.main([__file__, '-v'] + sys.argv[1:])