#!/usr/bin/env python3
"""Debug report owner visibility issue using raw SQL"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db
from sqlalchemy import text


async def debug_report_owner():
    """Debug why report owner cannot see pending reviews"""
    async for db in get_db():
        try:
            print("=== DEBUG REPORT OWNER VISIBILITY ===\n")
            
            # 1. Check report 156 ownership
            result = await db.execute(text("""
                SELECT 
                    r.report_id,
                    r.report_name,
                    r.report_owner_id,
                    u.username,
                    u.email,
                    u.role
                FROM reports r
                LEFT JOIN users u ON r.report_owner_id = u.user_id
                WHERE r.report_id = 156
            """))
            
            row = result.first()
            if row:
                print(f"Report 156: {row[1]}")
                print(f"  Owner ID: {row[2]}")
                if row[2]:
                    print(f"  Owner: {row[3]} ({row[4]})")
                    print(f"  Role: {row[5]}")
                    report_owner_id = row[2]
                else:
                    print("  No owner assigned!")
                    report_owner_id = None
            else:
                print("Report 156 not found!")
                report_owner_id = None
            
            print("\n" + "="*50 + "\n")
            
            # 2. Check scoping submissions for cycle 13, report 156
            result = await db.execute(text("""
                SELECT 
                    ss.submission_id,
                    ss.cycle_id,
                    ss.report_id,
                    ss.version,
                    ss.submitted_by,
                    ss.submitted_at,
                    ss.is_latest,
                    ss.scoped_attributes,
                    ss.total_attributes,
                    u.username as submitter
                FROM cycle_report_scoping_submissions ss
                LEFT JOIN users u ON ss.submitted_by = u.user_id
                WHERE ss.cycle_id = 13 AND ss.report_id = 156
                ORDER BY ss.version DESC
            """))
            
            submissions = result.fetchall()
            print(f"Scoping submissions for cycle 13, report 156: {len(submissions)} found")
            
            for sub in submissions:
                print(f"\nSubmission {sub[0]}:")
                print(f"  Version: {sub[3]}")
                print(f"  Is Latest: {sub[6]}")
                print(f"  Submitted by: {sub[9]}")
                print(f"  Submitted at: {sub[5]}")
                print(f"  Attributes: {sub[7]}/{sub[8]}")
                
                # Check if reviewed
                review_result = await db.execute(text("""
                    SELECT review_id, review_decision, reviewed_at
                    FROM cycle_report_scoping_report_owner_reviews
                    WHERE submission_id = :submission_id
                """), {"submission_id": sub[0]})
                
                review = review_result.first()
                if review:
                    print(f"  Reviewed: Yes - {review[1]}")
                else:
                    print(f"  Reviewed: No - PENDING")
            
            print("\n" + "="*50 + "\n")
            
            # 3. Check all Report Owners in the system
            result = await db.execute(text("""
                SELECT 
                    u.user_id,
                    u.username,
                    u.email,
                    u.role,
                    COUNT(r.report_id) as report_count
                FROM users u
                LEFT JOIN reports r ON r.report_owner_id = u.user_id
                WHERE u.role IN ('Report Owner', 'Report Owner Executive')
                GROUP BY u.user_id, u.username, u.email, u.role
            """))
            
            report_owners = result.fetchall()
            print(f"Report Owners in system: {len(report_owners)}")
            
            for ro in report_owners:
                print(f"\n{ro[1]} ({ro[2]}):")
                print(f"  Role: {ro[3]}")
                print(f"  Assigned Reports: {ro[4]}")
                
                if ro[4] > 0:
                    # Count pending reviews for this RO
                    pending_result = await db.execute(text("""
                        SELECT COUNT(DISTINCT ss.submission_id)
                        FROM cycle_report_scoping_submissions ss
                        INNER JOIN reports r ON r.report_id = ss.report_id
                        WHERE r.report_owner_id = :user_id
                          AND ss.is_latest = true
                          AND NOT EXISTS (
                              SELECT 1 
                              FROM cycle_report_scoping_report_owner_reviews rosr
                              WHERE rosr.submission_id = ss.submission_id
                          )
                    """), {"user_id": ro[0]})
                    
                    pending_count = pending_result.scalar()
                    print(f"  Pending Reviews: {pending_count}")
            
            print("\n" + "="*50 + "\n")
            
            # 4. Test the pending-reviews query logic
            if report_owner_id:
                print(f"Testing pending-reviews endpoint logic for report owner ID {report_owner_id}...")
                
                # Get reports owned by the report owner
                result = await db.execute(text("""
                    SELECT report_id, report_name
                    FROM reports
                    WHERE report_owner_id = :owner_id
                """), {"owner_id": report_owner_id})
                
                owned_reports = result.fetchall()
                report_ids = [r[0] for r in owned_reports]
                
                print(f"Reports owned by user {report_owner_id}: {report_ids}")
                
                # Get pending submissions
                result = await db.execute(text("""
                    SELECT 
                        ss.submission_id,
                        ss.cycle_id,
                        ss.report_id,
                        ss.version,
                        r.report_name
                    FROM cycle_report_scoping_submissions ss
                    INNER JOIN reports r ON r.report_id = ss.report_id
                    WHERE ss.report_id = ANY(:report_ids)
                      AND ss.is_latest = true
                      AND NOT EXISTS (
                          SELECT 1 
                          FROM cycle_report_scoping_report_owner_reviews rosr
                          WHERE rosr.submission_id = ss.submission_id
                      )
                """), {"report_ids": report_ids})
                
                pending_submissions = result.fetchall()
                print(f"Pending submissions found: {len(pending_submissions)}")
                
                for ps in pending_submissions:
                    print(f"  - Cycle {ps[1]}, Report {ps[2]} ({ps[4]}), Version {ps[3]}")
            
            print("\n" + "="*50 + "\n")
            
            # 5. Direct check what the API would return
            print("Simulating /scoping/pending-reviews API call for report owner...")
            
            if report_owner_id:
                result = await db.execute(text("""
                    SELECT 
                        ss.cycle_id,
                        ss.report_id,
                        r.report_name,
                        r.lob,
                        u.username as submitted_by,
                        ss.submitted_at,
                        ss.scoped_attributes as attributes_selected,
                        ss.total_attributes,
                        ss.submission_id,
                        ss.version
                    FROM cycle_report_scoping_submissions ss
                    INNER JOIN reports r ON r.report_id = ss.report_id
                    LEFT JOIN users u ON ss.submitted_by = u.user_id
                    WHERE r.report_owner_id = :owner_id
                      AND ss.is_latest = true
                      AND NOT EXISTS (
                          SELECT 1 
                          FROM cycle_report_scoping_report_owner_reviews rosr
                          WHERE rosr.submission_id = ss.submission_id
                      )
                    ORDER BY ss.submitted_at DESC
                """), {"owner_id": report_owner_id})
                
                api_results = result.fetchall()
                print(f"API would return {len(api_results)} pending reviews")
                
                for ar in api_results:
                    print(f"\n  Cycle {ar[0]}, Report {ar[1]}: {ar[2]}")
                    print(f"    LOB: {ar[3]}")
                    print(f"    Submitted by: {ar[4]} at {ar[5]}")
                    print(f"    Attributes: {ar[6]}/{ar[7]}")
                    print(f"    Submission ID: {ar[8]}, Version: {ar[9]}")
            
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(debug_report_owner())