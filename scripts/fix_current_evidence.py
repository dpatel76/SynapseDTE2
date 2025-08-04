#!/usr/bin/env python3
"""
Script to verify and fix current evidence flags in the database.
Ensures that the latest version of each test case's evidence has is_current=True.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, select, and_, func
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.models.request_info import TestCaseSourceEvidence, CycleReportTestCase


def check_and_fix_current_evidence():
    """Check and fix is_current flags for test case evidence"""
    
    # Create sync database connection
    # Convert async URL to sync URL if needed
    db_url = settings.database_url
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    
    with SessionLocal() as db:
        try:
            print("Checking test case evidence for is_current flags...")
            
            # Get all unique test_case_ids that have evidence
            result = db.execute(
                select(TestCaseSourceEvidence.test_case_id).distinct()
            )
            test_case_ids = [row[0] for row in result]
            
            print(f"Found {len(test_case_ids)} test cases with evidence")
            
            fixed_count = 0
            
            for test_case_id in test_case_ids:
                # Get all evidence for this test case ordered by version_number
                evidence_result = db.execute(
                    select(TestCaseSourceEvidence).where(
                        TestCaseSourceEvidence.test_case_id == test_case_id
                    ).order_by(TestCaseSourceEvidence.version_number.desc())
                )
                evidence_list = evidence_result.scalars().all()
                
                if not evidence_list:
                    continue
                
                # The first one (highest version) should be current
                latest_evidence = evidence_list[0]
                
                # Check if any evidence is marked as current
                has_current = any(e.is_current for e in evidence_list)
                
                if not has_current:
                    print(f"\n❌ Test case {test_case_id}: No evidence marked as current")
                    print(f"   Latest version: {latest_evidence.version_number}")
                    print(f"   Evidence type: {latest_evidence.evidence_type}")
                    print(f"   Submitted at: {latest_evidence.submitted_at}")
                    
                    # Fix: Mark the latest version as current
                    latest_evidence.is_current = True
                    latest_evidence.updated_at = datetime.utcnow()
                    fixed_count += 1
                    
                elif not latest_evidence.is_current:
                    # Latest version is not marked as current, but some other version is
                    print(f"\n⚠️  Test case {test_case_id}: Latest version not marked as current")
                    
                    # Unmark all as current first
                    for e in evidence_list:
                        if e.is_current:
                            print(f"   Unmarking version {e.version_number} as current")
                            e.is_current = False
                    
                    # Mark latest as current
                    latest_evidence.is_current = True
                    latest_evidence.updated_at = datetime.utcnow()
                    fixed_count += 1
                else:
                    # Everything looks good
                    # Make sure only the latest is marked as current
                    for i, e in enumerate(evidence_list):
                        if i == 0 and not e.is_current:
                            e.is_current = True
                            fixed_count += 1
                        elif i > 0 and e.is_current:
                            e.is_current = False
                            fixed_count += 1
            
            if fixed_count > 0:
                print(f"\n✅ Fixed {fixed_count} evidence records")
                db.commit()
                print("Changes committed to database")
            else:
                print("\n✅ All evidence records have correct is_current flags")
            
            # Verify the fixes
            print("\nVerifying current evidence counts...")
            current_evidence_result = db.execute(
                select(func.count(TestCaseSourceEvidence.id)).where(
                    TestCaseSourceEvidence.is_current == True
                )
            )
            current_count = current_evidence_result.scalar()
            
            print(f"Total evidence records with is_current=True: {current_count}")
            print(f"Total test cases with evidence: {len(test_case_ids)}")
            
            if current_count != len(test_case_ids):
                print("\n⚠️  Warning: Mismatch between test cases and current evidence count")
                print("This might indicate test cases with no evidence or data inconsistency")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            db.rollback()
            raise
        finally:
            engine.dispose()


if __name__ == "__main__":
    check_and_fix_current_evidence()