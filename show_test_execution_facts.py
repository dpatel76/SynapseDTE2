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
                e.id AS evidence_id,
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
        """)).mappings().fetchall()
        
        for row in evidence_data:
            print(f"\n📄 Evidence ID: {row['evidence_id']}")
            print(f"   Type: {row['evidence_type']}")
            if row['evidence_type'] == 'document':
                print(f"   Document: {row['document_name']}")
            else:
                print(f"   Query: {row['query_text'][:100]}..." if row['query_text'] else "")
            print(f"   Validation Status: {row['validation_status']}")
            print(f"   Version: {row['version_number']}")
            print(f"   Attribute: {row['attribute_name']}")
            print(f"   Sample ID: {row['sample_id']}")
            print(f"   Notes: {row['submission_notes']}")
            print(f"   Submitted: {row['created_at']}")
        
        # 2. Test Executions
        print("\n\n2️⃣ TEST EXECUTIONS:")
        print("-" * 60)
        
        execution_data = conn.execute(text("""
            SELECT 
                ter.id AS execution_id,
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
        """)).mappings().fetchall()
        
        for row in execution_data:
            print(f"\n🧪 Execution ID: {row['execution_id']} (Execution #{row['execution_number']})")
            print(f"   Test Type: {row['test_type']}")
            print(f"   Analysis Method: {row['analysis_method']}")
            print(f"   Attribute: {row['attribute_name']}")
            print(f"   Evidence Type: {row['evidence_type']}")
            if row['evidence_type'] == 'document':
                print(f"   Document: {row['document_name']}")
            print(f"   Sample Value: ${row['sample_value']}")
            print(f"   Extracted Value: ${row['extracted_value']}")
            print(f"   Match Result: {row['test_result'].upper()} {'✅' if row['comparison_result'] else '❌'}")
            print(f"   LLM Confidence: {row['llm_confidence_score']}")
            print(f"   Summary: {row['execution_summary']}")
            print(f"   Completed: {row['completed_at']}")
            
            # Parse analysis results
            if row['analysis_results']:
                analysis = row['analysis_results'] if isinstance(row['analysis_results'], dict) else json.loads(row['analysis_results'])
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
        """)).mappings().fetchall()
        
        print("\n📊 Evidence Submissions:")
        for stat in evidence_stats:
            print(f"   {stat['evidence_type']}: {stat['count']} total, {stat['valid_count']} validated")
        
        # Execution stats
        exec_stats = conn.execute(text("""
            SELECT 
                test_result,
                COUNT(*) as count,
                AVG(llm_confidence_score) as avg_confidence
            FROM cycle_report_test_execution_results
            WHERE created_at >= CURRENT_DATE
            GROUP BY test_result
        """)).mappings().fetchall()
        
        print("\n📊 Test Execution Results:")
        for stat in exec_stats:
            print(f"   {stat['test_result'].upper()}: {stat['count']} tests (avg confidence: {stat['avg_confidence']:.2f})")
        
        # Document processing stats
        doc_stats = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT e.document_name) as unique_docs,
                COUNT(DISTINCT ter.id) as doc_executions
            FROM cycle_report_request_info_testcase_source_evidence e
            JOIN cycle_report_test_execution_results ter ON ter.evidence_id = e.id
            WHERE e.evidence_type = 'document'
            AND e.created_at >= CURRENT_DATE
        """)).mappings().fetchone()
        
        print(f"\n📊 Document Processing:")
        print(f"   Unique documents: {doc_stats['unique_docs']}")
        print(f"   Document-based executions: {doc_stats['doc_executions']}")
        
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
        """)).mappings().fetchall()
        
        for row in cc_evidence:
            print(f"\n💳 {row['document_name']}")
            print(f"   Submission Notes: {row['submission_notes']}")
            print(f"   Extracted Credit Limit: ${row['extracted_value']}")
            print(f"   Sample Credit Limit: ${row['sample_value']}")
            print(f"   Test Result: {row['test_result'].upper()} {'✅' if row['test_result'] == 'pass' else '❌'}")
            
            if row['analysis_results']:
                analysis = row['analysis_results'] if isinstance(row['analysis_results'], dict) else json.loads(row['analysis_results'])
                if 'document_analysis' in analysis:
                    da = analysis['document_analysis']
                    print(f"   Identified as: {da.get('document_type', 'N/A')}")
                    print(f"   FR Y-14M Schedule: {da.get('regulatory_schedule', 'N/A')}")
                    print(f"   Confidence: {da.get('extraction_confidence', 'N/A')}")

if __name__ == "__main__":
    show_test_execution_facts()
