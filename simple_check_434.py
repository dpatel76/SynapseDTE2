#!/usr/bin/env python3

import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
import json

# Database connection
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres:admin123@localhost:5432/synapse_dt')
if DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)

async def check_test_case():
    """Check test case and evidence"""
    
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get test case
        tc_query = text("""
            SELECT * FROM cycle_report_test_cases WHERE id = 434
        """)
        tc_result = await session.execute(tc_query)
        test_case = tc_result.first()
        
        print(f"\n=== Test Case 434 ===")
        if test_case:
            print(f"Test Case Name: {test_case.test_case_name}")
            print(f"Attribute ID: {test_case.attribute_id}")
            print(f"Attribute Name: {test_case.attribute_name}")
            print(f"Sample ID: {test_case.sample_id}")
            print(f"Status: {test_case.status}")
            
            # Check for primary key attributes
            if hasattr(test_case, 'primary_key_attributes'):
                print(f"Primary Key Attributes: {test_case.primary_key_attributes}")
        
        # Get sample data from sample selection table
        sample_query = text("""
            SELECT * FROM cycle_report_sample_selection_samples 
            WHERE sample_identifier = :sample_id
            LIMIT 1
        """)
        sample_result = await session.execute(sample_query, {"sample_id": test_case.sample_id if test_case else ""})
        sample = sample_result.first()
        
        print(f"\n=== Sample Data ===")
        if sample:
            print(f"Sample Identifier: {sample.sample_identifier}")
            print(f"Primary Key Values: {sample.primary_key_values}")
            print(f"Attribute Values: {sample.attribute_values}")
        else:
            print("No sample data found")
        
        # Get evidence
        ev_query = text("""
            SELECT 
                id,
                evidence_type,
                document_name,
                query_text,
                data_source_id
            FROM test_case_evidence 
            WHERE test_case_id = 434 
            AND is_current = true
            ORDER BY created_at DESC
            LIMIT 1
        """)
        ev_result = await session.execute(ev_query)
        evidence = ev_result.first()
        
        print(f"\n=== Evidence ===")
        if evidence:
            print(f"Evidence ID: {evidence.id}")
            print(f"Type: {evidence.evidence_type}")
            if evidence.evidence_type == 'data_source':
                print(f"Data Source ID: {evidence.data_source_id}")
                print(f"Query: {evidence.query_text[:200]}..." if evidence.query_text and len(evidence.query_text) > 200 else f"Query: {evidence.query_text}")
        else:
            print("No evidence found")

if __name__ == "__main__":
    asyncio.run(check_test_case())