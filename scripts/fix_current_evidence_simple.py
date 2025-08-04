#!/usr/bin/env python3
"""
Simple script to check and fix is_current flags in test case evidence
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt")

# Convert async URL to sync if needed
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        print("Checking test case evidence for is_current flags...")
        
        # Get all unique test_case_ids that have evidence
        cur.execute("""
            SELECT DISTINCT test_case_id 
            FROM cycle_report_request_info_testcase_source_evidence
            ORDER BY test_case_id
        """)
        test_case_ids = [row['test_case_id'] for row in cur.fetchall()]
        
        print(f"Found {len(test_case_ids)} test cases with evidence")
        
        fixed_count = 0
        
        for test_case_id in test_case_ids:
            # Get all evidence for this test case ordered by version_number
            cur.execute("""
                SELECT id, version_number, is_current, evidence_type, submitted_at
                FROM cycle_report_request_info_testcase_source_evidence
                WHERE test_case_id = %s
                ORDER BY version_number DESC
            """, (test_case_id,))
            
            evidence_list = cur.fetchall()
            
            if not evidence_list:
                continue
            
            # The first one (highest version) should be current
            latest_evidence = evidence_list[0]
            
            # Check if any evidence is marked as current
            has_current = any(e['is_current'] for e in evidence_list)
            
            if not has_current:
                print(f"\n❌ Test case {test_case_id}: No evidence marked as current")
                print(f"   Latest version: {latest_evidence['version_number']}")
                print(f"   Evidence type: {latest_evidence['evidence_type']}")
                print(f"   Submitted at: {latest_evidence['submitted_at']}")
                
                # Fix: Mark the latest version as current
                cur.execute("""
                    UPDATE cycle_report_request_info_testcase_source_evidence
                    SET is_current = true, updated_at = %s
                    WHERE id = %s
                """, (datetime.utcnow(), latest_evidence['id']))
                fixed_count += 1
                
            elif not latest_evidence['is_current']:
                # Latest version is not marked as current, but some other version is
                print(f"\n⚠️  Test case {test_case_id}: Latest version not marked as current")
                
                # Unmark all as current first
                cur.execute("""
                    UPDATE cycle_report_request_info_testcase_source_evidence
                    SET is_current = false
                    WHERE test_case_id = %s
                """, (test_case_id,))
                
                # Mark latest as current
                cur.execute("""
                    UPDATE cycle_report_request_info_testcase_source_evidence
                    SET is_current = true, updated_at = %s
                    WHERE id = %s
                """, (datetime.utcnow(), latest_evidence['id']))
                fixed_count += 1
            else:
                # Everything looks good - but make sure only the latest is marked as current
                for i, e in enumerate(evidence_list):
                    if i == 0 and not e['is_current']:
                        cur.execute("""
                            UPDATE cycle_report_request_info_testcase_source_evidence
                            SET is_current = true, updated_at = %s
                            WHERE id = %s
                        """, (datetime.utcnow(), e['id']))
                        fixed_count += 1
                    elif i > 0 and e['is_current']:
                        cur.execute("""
                            UPDATE cycle_report_request_info_testcase_source_evidence
                            SET is_current = false
                            WHERE id = %s
                        """, (e['id'],))
                        fixed_count += 1
        
        if fixed_count > 0:
            print(f"\n✅ Fixed {fixed_count} evidence records")
            conn.commit()
            print("Changes committed to database")
        else:
            print("\n✅ All evidence records have correct is_current flags")
        
        # Verify the fixes
        print("\nVerifying current evidence counts...")
        cur.execute("""
            SELECT COUNT(*) as count
            FROM cycle_report_request_info_testcase_source_evidence
            WHERE is_current = true
        """)
        current_count = cur.fetchone()['count']
        
        print(f"Total evidence records with is_current=True: {current_count}")
        print(f"Total test cases with evidence: {len(test_case_ids)}")
        
        if current_count != len(test_case_ids):
            print("\n⚠️  Warning: Mismatch between test cases and current evidence count")
            print("This might indicate test cases with no evidence or data inconsistency")
            
            # Find test cases without current evidence
            cur.execute("""
                SELECT DISTINCT test_case_id 
                FROM cycle_report_request_info_testcase_source_evidence
                WHERE test_case_id NOT IN (
                    SELECT test_case_id 
                    FROM cycle_report_request_info_testcase_source_evidence
                    WHERE is_current = true
                )
            """)
            missing = cur.fetchall()
            if missing:
                print(f"\nTest cases without current evidence: {[r['test_case_id'] for r in missing]}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()