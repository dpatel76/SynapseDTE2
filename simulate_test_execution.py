#!/usr/bin/env python3
"""
Simulate test execution to show complete flow
"""

import asyncio
import json
from sqlalchemy import create_engine, text
from datetime import datetime

DATABASE_URL = "postgresql://synapse_user:synapse_password@localhost/synapse_dt"


def simulate_test_execution():
    """Simulate a test execution using the evidence"""
    print("\n🎯 SIMULATING TEST EXECUTION WITH EVIDENCE")
    print("=" * 60)
    
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Get the evidence we created
        evidence = conn.execute(text("""
            SELECT 
                id,
                test_case_id,
                sample_id,
                query_text,
                data_source_id,
                attribute_id
            FROM cycle_report_request_info_testcase_source_evidence
            WHERE id = 5
        """)).fetchone()
        
        if not evidence:
            print("❌ Evidence not found")
            return
        
        print(f"📄 Using Evidence ID: {evidence[0]}")
        print(f"   Test Case ID: {evidence[1]}")
        print(f"   Query: {evidence[3][:100]}...")
        
        # Get sample data
        sample_data = conn.execute(text("""
            SELECT 
                s.sample_identifier,
                s.sample_data
            FROM cycle_report_sample_selection_samples s
            WHERE s.sample_id = CAST(:sample_id AS UUID)
        """), {"sample_id": evidence[2]}).fetchone()
        
        if sample_data:
            sample_value = sample_data[1].get("Current Credit limit", "0") if sample_data[1] else "0"
            print(f"\n📊 Sample Data:")
            print(f"   Sample ID: {sample_data[0]}")
            print(f"   Expected Value: {sample_value}")
        
        # Execute the query from evidence
        print(f"\n🔄 Executing Query from Evidence...")
        try:
            result = conn.execute(text(evidence[3]))
            query_result = result.fetchone()
            
            if query_result:
                extracted_value = query_result[1]  # current_credit_limit
                print(f"✅ Query Executed Successfully")
                print(f"   Customer ID: {query_result[0]}")
                print(f"   Retrieved Value: {extracted_value}")
                
                # Compare values
                print(f"\n🔍 COMPARISON:")
                print(f"   Sample Value: {sample_value}")
                print(f"   Extracted Value: {extracted_value}")
                
                # Check if they match
                match = float(sample_value) == float(extracted_value)
                print(f"   Match Status: {'✅ VALUES MATCH' if match else '❌ VALUES DO NOT MATCH'}")
                
                # Simulate creating test execution record
                print(f"\n💾 Creating Test Execution Record...")
                
                # Get phase_id
                phase_result = conn.execute(text("""
                    SELECT phase_id FROM workflow_phases 
                    WHERE cycle_id = 55 AND report_id = 156 
                    AND phase_name = 'Testing'
                """)).fetchone()
                
                if phase_result:
                    phase_id = phase_result[0]
                    
                    # Create execution record
                    exec_result = conn.execute(text("""
                        INSERT INTO cycle_report_test_execution_results
                        (phase_id, test_case_id, evidence_id, execution_number, is_latest_execution,
                         execution_reason, test_type, analysis_method, sample_value, extracted_value,
                         expected_value, test_result, comparison_result, database_query_executed,
                         database_result_count, execution_status, started_at, completed_at,
                         executed_by, created_by, updated_by, execution_method, analysis_results,
                         evidence_validation_status, evidence_version_number, execution_summary)
                        VALUES (:phase_id, :test_case_id, :evidence_id, 1, true,
                                'Testing evidence submission flow', 'database_test', 'database_query',
                                :sample_value, :extracted_value, :sample_value,
                                :test_result, :comparison_result, :query,
                                1, 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
                                1, 1, 1, 'automatic', :analysis_results,
                                'valid', 1, :summary)
                        RETURNING id
                    """), {
                        "phase_id": phase_id,
                        "test_case_id": str(evidence[1]),
                        "evidence_id": evidence[0],
                        "sample_value": str(sample_value),
                        "extracted_value": str(extracted_value),
                        "test_result": "pass" if match else "fail",
                        "comparison_result": match,
                        "query": evidence[3],
                        "analysis_results": json.dumps({
                            "database_analysis": {
                                "query_executed": evidence[3],
                                "result_count": 1,
                                "execution_time_ms": 15,
                                "result_sample": [{"customer_id": query_result[0], "current_credit_limit": float(extracted_value)}]
                            }
                        }),
                        "summary": f"Test {'passed' if match else 'failed'}: Sample value {sample_value} {'matches' if match else 'does not match'} extracted value {extracted_value}"
                    })
                    
                    execution_id = exec_result.fetchone()[0]
                    conn.commit()
                    
                    print(f"✅ Test Execution Created (ID: {execution_id})")
                    print(f"   Status: completed")
                    print(f"   Result: {'pass' if match else 'fail'}")
                    print(f"   Comparison: {'✅ MATCH' if match else '❌ MISMATCH'}")
                    
                    # Show what tester would see
                    print(f"\n👨‍💼 TESTER VIEW:")
                    print("=" * 60)
                    print(f"Test Case: TC-001")
                    print(f"Attribute: Current Credit limit")
                    print(f"Evidence Type: Data Source Query")
                    print(f"Sample Value: {sample_value}")
                    print(f"Retrieved Value: {extracted_value}")
                    print(f"Test Result: {'✅ PASS' if match else '❌ FAIL'}")
                    print(f"Confidence: High (direct database query)")
                    
            else:
                print("❌ Query returned no results")
                
        except Exception as e:
            print(f"❌ Query execution failed: {e}")


if __name__ == "__main__":
    simulate_test_execution()