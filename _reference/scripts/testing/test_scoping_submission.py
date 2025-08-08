#!/usr/bin/env python3
"""Create a test scoping submission for report owner to review"""

import asyncio
from app.core.database import get_db
from sqlalchemy import text
from datetime import datetime


async def create_test_submission():
    """Create a test scoping submission"""
    async for db in get_db():
        try:
            # Check if submission already exists
            result = await db.execute(text("""
                SELECT submission_id FROM cycle_report_scoping_submissions
                WHERE cycle_id = 13 AND report_id = 156
            """))
            existing = result.first()
            
            if existing:
                print(f"Submission already exists with ID: {existing[0]}")
                
                # Check if it has a review
                review_result = await db.execute(text("""
                    SELECT review_id FROM cycle_report_scoping_report_owner_reviews
                    WHERE submission_id = :submission_id
                """), {"submission_id": existing[0]})
                
                if review_result.first():
                    print("This submission has already been reviewed")
                    
                    # Delete the review to make it pending again
                    await db.execute(text("""
                        DELETE FROM cycle_report_scoping_report_owner_reviews
                        WHERE submission_id = :submission_id
                    """), {"submission_id": existing[0]})
                    print("✅ Deleted existing review to make submission pending again")
                else:
                    print("✅ Submission is already pending review")
            else:
                # Create new submission
                result = await db.execute(text("""
                    INSERT INTO cycle_report_scoping_submissions (
                        cycle_id, report_id, version, submitted_by, 
                        submitted_at, scoped_attributes, total_attributes, 
                        submission_notes, is_latest
                    ) VALUES (
                        13, 156, 1, 253,  -- 253 is tester@synapse.com
                        :submitted_at, 42, 118, 
                        'Test submission for Report Owner review', true
                    ) RETURNING submission_id
                """), {"submitted_at": datetime.utcnow()})
                
                submission_id = result.scalar()
                print(f"✅ Created new submission with ID: {submission_id}")
            
            await db.commit()
            
            # Verify the submission is visible
            result = await db.execute(text("""
                SELECT 
                    ss.submission_id,
                    ss.cycle_id,
                    ss.report_id,
                    r.report_name,
                    r.report_owner_id,
                    u.email as owner_email
                FROM cycle_report_scoping_submissions ss
                JOIN reports r ON r.report_id = ss.report_id
                LEFT JOIN users u ON u.user_id = r.report_owner_id
                WHERE ss.cycle_id = 13 AND ss.report_id = 156
                  AND ss.is_latest = true
            """))
            
            row = result.first()
            if row:
                print(f"\nSubmission details:")
                print(f"  Submission ID: {row[0]}")
                print(f"  Report: {row[3]} (ID: {row[2]})")
                print(f"  Owner ID: {row[4]} ({row[5]})")
                print(f"  Status: Pending Review")
            
        except Exception as e:
            print(f"Error: {e}")
            await db.rollback()
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(create_test_submission())