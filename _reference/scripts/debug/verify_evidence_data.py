#!/usr/bin/env python3
"""
Script to verify evidence submission data in the PostgreSQL database.
This script connects to the database and checks the cycle_report_rfi_evidence table
to verify evidence exists and shows statistics about the evidence data.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json


def connect_to_db():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="synapse_dt",
            user="synapse_user",
            password="synapse_password",
            cursor_factory=RealDictCursor
        )
        print("✅ Successfully connected to the database")
        return conn
    except psycopg2.Error as e:
        print(f"❌ Error connecting to database: {e}")
        return None


def check_evidence_count(cursor):
    """Check total count of evidence records."""
    print("\n📊 EVIDENCE COUNT STATISTICS")
    print("=" * 60)
    
    # Total evidence count
    cursor.execute("SELECT COUNT(*) as total FROM cycle_report_rfi_evidence")
    result = cursor.fetchone()
    print(f"Total evidence records: {result['total']}")
    
    # Count by test_case_id
    cursor.execute("""
        SELECT test_case_id, COUNT(*) as count
        FROM cycle_report_rfi_evidence
        GROUP BY test_case_id
        ORDER BY test_case_id
    """)
    results = cursor.fetchall()
    
    print("\nEvidence count by test_case_id:")
    for row in results:
        print(f"  Test Case ID {row['test_case_id']}: {row['count']} evidence records")


def show_sample_evidence(cursor):
    """Show sample evidence records with details."""
    print("\n📋 SAMPLE EVIDENCE RECORDS")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            id,
            test_case_id,
            evidence_type,
            original_filename,
            file_size_bytes,
            mime_type,
            submission_notes,
            submitted_at,
            submitted_by,
            validation_status,
            sample_id,
            version_number
        FROM cycle_report_rfi_evidence
        ORDER BY submitted_at DESC
        LIMIT 5
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("No evidence records found.")
        return
    
    for i, row in enumerate(results, 1):
        print(f"\nEvidence Record #{i}:")
        print(f"  ID: {row['id']}")
        print(f"  Test Case ID: {row['test_case_id']}")
        print(f"  Evidence Type: {row['evidence_type']}")
        print(f"  Sample ID: {row['sample_id']}")
        print(f"  Version: {row['version_number']}")
        if row['original_filename']:
            print(f"  File Name: {row['original_filename']}")
            print(f"  File Size: {row['file_size_bytes']:,} bytes" if row['file_size_bytes'] else "  File Size: N/A")
            print(f"  MIME Type: {row['mime_type'] or 'N/A'}")
        print(f"  Validation Status: {row['validation_status']}")
        print(f"  Submission Notes: {row['submission_notes'] or 'N/A'}")
        print(f"  Submitted At: {row['submitted_at']}")
        print(f"  Submitted By: User ID {row['submitted_by']}")


def check_test_cases_with_evidence(cursor):
    """Show which test cases have evidence attached."""
    print("\n🔗 TEST CASES WITH EVIDENCE")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            tc.id as test_case_id,
            tc.test_case_name,
            tc.status,
            COUNT(e.id) as evidence_count,
            STRING_AGG(e.original_filename, ', ') as file_names
        FROM cycle_report_test_cases tc
        LEFT JOIN cycle_report_rfi_evidence e ON tc.id = e.test_case_id
        GROUP BY tc.id, tc.test_case_name, tc.status
        ORDER BY tc.id
    """)
    
    results = cursor.fetchall()
    
    # Separate test cases with and without evidence
    with_evidence = [r for r in results if r['evidence_count'] > 0]
    without_evidence = [r for r in results if r['evidence_count'] == 0]
    
    print(f"\nTest cases WITH evidence: {len(with_evidence)}")
    print(f"Test cases WITHOUT evidence: {len(without_evidence)}")
    
    if with_evidence:
        print("\nTest cases with evidence:")
        for row in with_evidence:
            print(f"\n  Test Case ID: {row['test_case_id']}")
            print(f"  Name: {row['test_case_name']}")
            print(f"  Status: {row['status']}")
            print(f"  Evidence Count: {row['evidence_count']}")
            print(f"  Files: {row['file_names']}")


def check_recent_uploads(cursor):
    """Check recent evidence uploads."""
    print("\n⏰ RECENT EVIDENCE UPLOADS (Last 24 hours)")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            e.id,
            e.test_case_id,
            e.original_filename,
            e.evidence_type,
            e.submitted_at,
            u.email as submitted_by
        FROM cycle_report_rfi_evidence e
        LEFT JOIN users u ON e.submitted_by = u.user_id
        WHERE e.submitted_at >= NOW() - INTERVAL '24 hours'
        ORDER BY e.submitted_at DESC
    """)
    
    results = cursor.fetchall()
    
    if not results:
        print("No evidence uploaded in the last 24 hours.")
        return
    
    print(f"Found {len(results)} evidence uploads in the last 24 hours:")
    for row in results:
        print(f"\n  Type: {row['evidence_type']}")
        if row['original_filename']:
            print(f"  File: {row['original_filename']}")
        print(f"  Test Case ID: {row['test_case_id']}")
        print(f"  Submitted: {row['submitted_at']}")
        print(f"  By: {row['submitted_by'] or 'Unknown'}")


def check_evidence_by_cycle_report(cursor):
    """Check evidence grouped by cycle and report."""
    print("\n📂 EVIDENCE BY CYCLE AND REPORT")
    print("=" * 60)
    
    cursor.execute("""
        SELECT 
            wp.cycle_id,
            wp.report_id,
            COUNT(DISTINCT tc.id) as total_test_cases,
            COUNT(DISTINCT CASE WHEN e.id IS NOT NULL THEN tc.id END) as test_cases_with_evidence,
            COUNT(e.id) as total_evidence_files
        FROM workflow_phases wp
        JOIN cycle_report_test_cases tc ON wp.phase_id = tc.phase_id
        LEFT JOIN cycle_report_rfi_evidence e ON tc.id = e.test_case_id
        WHERE wp.phase_name = 'Request Info'
        GROUP BY wp.cycle_id, wp.report_id
        ORDER BY wp.cycle_id, wp.report_id
    """)
    
    results = cursor.fetchall()
    
    for row in results:
        print(f"\nCycle {row['cycle_id']}, Report {row['report_id']}:")
        print(f"  Total Test Cases: {row['total_test_cases']}")
        print(f"  Test Cases with Evidence: {row['test_cases_with_evidence']}")
        print(f"  Total Evidence Files: {row['total_evidence_files']}")
        if row['total_test_cases'] > 0:
            coverage = (row['test_cases_with_evidence'] / row['total_test_cases']) * 100
            print(f"  Evidence Coverage: {coverage:.1f}%")


def check_evidence_details(cursor):
    """Check detailed evidence information including data source type evidence."""
    print("\n🔍 DETAILED EVIDENCE ANALYSIS")
    print("=" * 60)
    
    # Check data source type evidence details
    cursor.execute("""
        SELECT 
            e.id,
            e.test_case_id,
            e.sample_id,
            e.version_number,
            e.query_text,
            e.query_parameters,
            tc.test_case_name,
            tc.attribute_name,
            ds.source_name,
            ds.connection_type
        FROM cycle_report_rfi_evidence e
        JOIN cycle_report_test_cases tc ON e.test_case_id = tc.id
        LEFT JOIN cycle_report_rfi_data_sources ds ON e.rfi_data_source_id = ds.data_source_id
        WHERE e.evidence_type = 'data_source'
        ORDER BY e.test_case_id, e.version_number
    """)
    
    results = cursor.fetchall()
    
    if results:
        print("\nData Source Evidence Details:")
        for row in results:
            print(f"\n  Test Case: {row['test_case_name']}")
            print(f"  Attribute: {row['attribute_name']}")
            print(f"  Sample ID: {row['sample_id']}")
            print(f"  Version: {row['version_number']}")
            if row['source_name']:
                print(f"  Data Source: {row['source_name']} ({row['connection_type']})")
            if row['query_text']:
                print(f"  Query: {row['query_text'][:100]}{'...' if len(row['query_text']) > 100 else ''}")
            if row['query_parameters']:
                print(f"  Parameters: {row['query_parameters']}")
    
    # Check document type evidence details
    cursor.execute("""
        SELECT 
            e.id,
            e.test_case_id,
            e.original_filename,
            e.file_size_bytes,
            e.mime_type,
            tc.test_case_name
        FROM cycle_report_rfi_evidence e
        JOIN cycle_report_test_cases tc ON e.test_case_id = tc.id
        WHERE e.evidence_type = 'document'
        ORDER BY e.test_case_id
    """)
    
    doc_results = cursor.fetchall()
    
    if doc_results:
        print("\n\nDocument Evidence Details:")
        for row in doc_results:
            print(f"\n  Test Case: {row['test_case_name']}")
            print(f"  File: {row['original_filename']}")
            print(f"  Size: {row['file_size_bytes']:,} bytes")
            print(f"  Type: {row['mime_type']}")


def main():
    """Main function to run all verification checks."""
    print("🔍 EVIDENCE DATA VERIFICATION SCRIPT")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Connect to database
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Run all checks
        check_evidence_count(cursor)
        show_sample_evidence(cursor)
        check_test_cases_with_evidence(cursor)
        check_recent_uploads(cursor)
        check_evidence_by_cycle_report(cursor)
        check_evidence_details(cursor)
        
        print("\n" + "=" * 60)
        print("✅ Verification complete!")
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
    finally:
        cursor.close()
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()