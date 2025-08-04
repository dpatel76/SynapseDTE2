#!/usr/bin/env python3
"""
Find test cases that have evidence but no current evidence
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = "postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt"

def main():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Find test cases with evidence but no current evidence
        cur.execute("""
            SELECT DISTINCT e1.test_case_id
            FROM cycle_report_request_info_testcase_source_evidence e1
            WHERE NOT EXISTS (
                SELECT 1 
                FROM cycle_report_request_info_testcase_source_evidence e2
                WHERE e2.test_case_id = e1.test_case_id
                AND e2.is_current = true
            )
            ORDER BY e1.test_case_id
        """)
        
        problem_test_cases = cur.fetchall()
        
        if problem_test_cases:
            print(f"Found {len(problem_test_cases)} test cases with evidence but no current evidence:")
            for tc in problem_test_cases:
                test_case_id = tc['test_case_id']
                
                # Get details about this test case's evidence
                cur.execute("""
                    SELECT id, version_number, is_current, evidence_type, submitted_at
                    FROM cycle_report_request_info_testcase_source_evidence
                    WHERE test_case_id = %s
                    ORDER BY version_number DESC
                """, (test_case_id,))
                
                evidence = cur.fetchall()
                print(f"\nTest case {test_case_id}:")
                for e in evidence:
                    print(f"  - v{e['version_number']}: {e['evidence_type']} (is_current={e['is_current']}) submitted at {e['submitted_at']}")
                
                # Fix by marking the latest version as current
                if evidence:
                    latest = evidence[0]
                    print(f"  ✅ Fixing: Setting version {latest['version_number']} as current")
                    cur.execute("""
                        UPDATE cycle_report_request_info_testcase_source_evidence
                        SET is_current = true
                        WHERE id = %s
                    """, (latest['id'],))
            
            conn.commit()
            print(f"\n✅ Fixed {len(problem_test_cases)} test cases")
        else:
            print("✅ All test cases with evidence have current evidence marked correctly")
        
        # Verify the fix
        cur.execute("""
            SELECT COUNT(DISTINCT test_case_id) as with_evidence,
                   COUNT(DISTINCT CASE WHEN is_current = true THEN test_case_id END) as with_current
            FROM cycle_report_request_info_testcase_source_evidence
        """)
        result = cur.fetchone()
        print(f"\nVerification:")
        print(f"Test cases with evidence: {result['with_evidence']}")
        print(f"Test cases with current evidence: {result['with_current']}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        conn.rollback()
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()