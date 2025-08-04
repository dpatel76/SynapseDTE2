#!/usr/bin/env python3
"""
Show concrete facts from test executions
"""

import json
from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = "postgresql://synapse_user:synapse_password@localhost/synapse_dt"

def show_test_execution_facts():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("🔍 TEST EXECUTION FACTS FROM DATABASE")
        print("=" * 80)
        
        # 1. Evidence Submissions
        print("\n1️⃣ EVIDENCE SUBMISSIONS:")
        print("-" * 60)
        
        evidence_data = conn.execute(text("""
            SELECT 
                e.id,
                e.evidence_type,
                e.document_name,
                e.query_text,
                e.validation_status,
                e.version_number,
                e.submission_notes,
                e.created_at,
                tc.attribute_name,
                tc.sample_id
            FROM cycle_report_request_info_testcase_source_evidence e
            JOIN cycle_report_test_cases tc ON e.test_case_id = tc.id
            WHERE e.created_at >= CURRENT_DATE
            ORDER BY e.created_at DESC
        """)).fetchall()
        
        for row in evidence_data:
            print(f"\n📄 Evidence ID: {row[0]}")
            print(f"   Type: {row[1]}")
            if row[1] == 'document':
                print(f"   Document: {row[2]}")
            else:
                print(f"   Query: {row[3][:100]}..." if row[3] else "")
            print(f"   Validation Status: {row[4]}")
            print(f"   Version: {row[5]}")
            print(f"   Attribute: {row[8]}")
            print(f"   Sample ID: {row[9]}")
            print(f"   Notes: {row[6]}")
            print(f"   Submitted: {row[7]}")
        
        # 2. Test Executions
        print("\n\n2️⃣ TEST EXECUTIONS:")
        print("-" * 60)
        
        execution_data = conn.execute(text("""
            SELECT 
                ter.id,
                ter.execution_number,
                ter.test_type,
                ter.analysis_method,
                ter.sample_value,
                ter.extracted_value,
                ter.test_result,
                ter.comparison_result,
                ter.llm_confidence_score,
                ter.execution_summary,
                ter.completed_at,
                ter.analysis_results,
                tc.attribute_name,
                e.evidence_type,
                e.document_name
            FROM cycle_report_test_execution_results ter
            JOIN cycle_report_test_cases tc ON ter.test_case_id = tc.id::text
            LEFT JOIN cycle_report_request_info_testcase_source_evidence e ON ter.evidence_id = e.id
            WHERE ter.created_at >= CURRENT_DATE
            ORDER BY ter.completed_at DESC
        """)).fetchall()
        
        for row in execution_data:
            print(f"\n🧪 Execution ID: {row[0]} (Execution #{row[1]})")
            print(f"   Test Type: {row[2]}")
            print(f"   Analysis Method: {row[3]}")
            print(f"   Attribute: {row[12]}")
            print(f"   Evidence Type: {row[13]}")
            if row[13] == 'document':
                print(f"   Document: {row[14]}")
            print(f"   Sample Value: ${row[4]}")
            print(f"   Extracted Value: ${row[5]}")
            print(f"   Match Result: {row[6].upper()} {'✅' if row[7] else '❌'}")
            print(f"   LLM Confidence: {row[8]}")
            print(f"   Summary: {row[9]}")
            print(f"   Completed: {row[10]}")
            
            # Parse analysis results
            if row[11]:
                analysis = row[11] if isinstance(row[11], dict) else json.loads(row[11])
                if 'document_analysis' in analysis:
                    doc_analysis = analysis['document_analysis']
                    print(f"   Document Type: {doc_analysis.get('document_type', 'N/A')}")
                    print(f"   Regulatory Schedule: {doc_analysis.get('regulatory_schedule', 'N/A')}")
                    print(f"   FR Y-14M Field: {doc_analysis.get('fr_y_14m_field', 'N/A')}")
                    print(f"   Extraction Method: {doc_analysis.get('extraction_method', 'N/A')}")
        
        # 3. Summary Statistics
        print("\n\n3️⃣ SUMMARY STATISTICS:")
        print("-" * 60)
        
        # Evidence stats
        evidence_stats = conn.execute(text("""
            SELECT 
                evidence_type,
                COUNT(*) as count,
                COUNT(CASE WHEN validation_status = 'valid' THEN 1 END) as valid_count
            FROM cycle_report_request_info_testcase_source_evidence
            WHERE created_at >= CURRENT_DATE
            GROUP BY evidence_type
        """)).fetchall()
        
        print("\n📊 Evidence Submissions:")
        for stat in evidence_stats:
            print(f"   {stat[0]}: {stat[1]} total, {stat[2]} validated")
        
        # Execution stats
        exec_stats = conn.execute(text("""
            SELECT 
                test_result,
                COUNT(*) as count,
                AVG(llm_confidence_score) as avg_confidence
            FROM cycle_report_test_execution_results
            WHERE created_at >= CURRENT_DATE
            GROUP BY test_result
        """)).fetchall()
        
        print("\n📊 Test Execution Results:")
        for stat in exec_stats:
            print(f"   {stat[0].upper()}: {stat[1]} tests (avg confidence: {stat[2]:.2f})")
        
        # Document processing stats
        doc_stats = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT e.document_name) as unique_docs,
                COUNT(DISTINCT ter.id) as doc_executions
            FROM cycle_report_request_info_testcase_source_evidence e
            JOIN cycle_report_test_execution_results ter ON ter.evidence_id = e.id
            WHERE e.evidence_type = 'document'
            AND e.created_at >= CURRENT_DATE
        """)).fetchone()
        
        print(f"\n📊 Document Processing:")
        print(f"   Unique documents: {doc_stats[0]}")
        print(f"   Document-based executions: {doc_stats[1]}")
        
        # 4. Generated Credit Card Statements
        print("\n\n4️⃣ CREDIT CARD STATEMENT FACTS:")
        print("-" * 60)
        
        cc_evidence = conn.execute(text("""
            SELECT 
                e.document_name,
                e.submission_notes,
                ter.extracted_value,
                ter.sample_value,
                ter.test_result,
                ter.analysis_results
            FROM cycle_report_request_info_testcase_source_evidence e
            JOIN cycle_report_test_execution_results ter ON ter.evidence_id = e.id
            WHERE e.evidence_type = 'document'
            AND e.document_name LIKE 'credit_card%'
            AND e.created_at >= CURRENT_DATE
            ORDER BY e.created_at
        """)).fetchall()
        
        for row in cc_evidence:
            print(f"\n💳 {row[0]}")
            print(f"   Submission Notes: {row[1]}")
            print(f"   Extracted Credit Limit: ${row[2]}")
            print(f"   Sample Credit Limit: ${row[3]}")
            print(f"   Test Result: {row[4].upper()} {'✅' if row[4] == 'pass' else '❌'}")
            
            if row[5]:
                analysis = row[5] if isinstance(row[5], dict) else json.loads(row[5])
                if 'document_analysis' in analysis:
                    da = analysis['document_analysis']
                    print(f"   Identified as: {da.get('document_type', 'N/A')}")
                    print(f"   FR Y-14M Schedule: {da.get('regulatory_schedule', 'N/A')}")
                    print(f"   Confidence: {da.get('extraction_confidence', 'N/A')}")

if __name__ == "__main__":
    show_test_execution_facts()
