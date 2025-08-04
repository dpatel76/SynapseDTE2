#!/usr/bin/env python3
"""Trace where is_match is being set"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, text
import json
import sys
import os
from datetime import datetime, timedelta

# Add the app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import get_settings
from app.models.test_execution import TestExecution

settings = get_settings()

# Create async engine
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False
)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def find_is_match_pattern():
    """Find the pattern of is_match creation"""
    async with AsyncSessionLocal() as db:
        # Check for any patterns in timing
        query = text("""
            SELECT 
                id,
                test_case_id,
                created_at,
                completed_at,
                started_at,
                execution_status,
                test_result,
                analysis_results,
                EXTRACT(EPOCH FROM (completed_at - created_at)) as duration_seconds
            FROM cycle_report_test_execution_results
            WHERE analysis_results ? 'is_match'
            ORDER BY id DESC
        """)
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        print(f"Found {len(rows)} executions with 'is_match'")
        print("=" * 100)
        
        for row in rows:
            print(f"\nID: {row[0]}, Test Case: {row[1]}")
            print(f"Created: {row[2]}")
            print(f"Started: {row[4]}")
            print(f"Completed: {row[3]}")
            print(f"Duration: {row[8]:.2f} seconds ({row[8]/3600:.2f} hours)")
            print(f"Status: {row[5]}, Result: {row[6]}")
            
            # Check if duration is exactly 4 hours
            if row[8] and abs(row[8] - 14400) < 10:  # Within 10 seconds of 4 hours
                print("⚠️  EXACTLY 4 HOURS! This suggests a timeout or scheduled process")
            
            analysis = row[7]
            if analysis:
                print(f"Analysis timestamp: {analysis.get('analysis_timestamp')}")
                
                # Check if the analysis timestamp matches completed_at
                if 'analysis_timestamp' in analysis:
                    analysis_dt = datetime.fromisoformat(analysis['analysis_timestamp'].replace('Z', '+00:00'))
                    completed_dt = row[3]
                    if completed_dt:
                        diff = abs((analysis_dt - completed_dt.replace(tzinfo=None)).total_seconds())
                        if diff < 1:
                            print("✓ Analysis timestamp matches completed_at")
                        else:
                            print(f"⚠️  Analysis timestamp differs from completed_at by {diff} seconds")
        
        # Check for any other processes that might be running
        print("\n" + "=" * 100)
        print("Checking for background job patterns...")
        
        # Look for jobs that might be processing these
        job_query = text("""
            SELECT COUNT(*), execution_status, test_result,
                   analysis_results ? 'is_match' as has_is_match,
                   analysis_results ? 'execution_source' as has_source
            FROM cycle_report_test_execution_results
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY execution_status, test_result, has_is_match, has_source
            ORDER BY execution_status, test_result
        """)
        
        result = await db.execute(job_query)
        
        print("\nExecution patterns in last 24 hours:")
        print("Status      | Result | Has is_match | Has source | Count")
        print("-" * 60)
        for row in result:
            print(f"{row[1]:11} | {row[2] or 'None':6} | {str(row[3]):12} | {str(row[4]):10} | {row[0]}")
        
        # Check audit logs for clues
        audit_query = text("""
            SELECT DISTINCT action, COUNT(*)
            FROM cycle_report_test_execution_audit
            WHERE created_at > NOW() - INTERVAL '24 hours'
            GROUP BY action
            ORDER BY COUNT(*) DESC
        """)
        
        result = await db.execute(audit_query)
        
        print("\nAudit log actions in last 24 hours:")
        for row in result:
            print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    asyncio.run(find_is_match_pattern())