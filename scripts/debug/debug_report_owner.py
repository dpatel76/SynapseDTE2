#!/usr/bin/env python3
"""Debug report owner visibility issue"""

import asyncio
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from app.core.database import get_db
from sqlalchemy import select, and_, exists, func, text
from sqlalchemy.ext.asyncio import AsyncSession


async def debug_report_owner():
    """Debug why report owner cannot see pending reviews"""
    async for db in get_db():
        try:
            print("=== DEBUG REPORT OWNER VISIBILITY ===\n")
            
            # 1. Check report 156 ownership using raw SQL
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
                else:
                    print("  No owner assigned!")
            else:
                print("Report 156 not found!")
            
            print("\n" + "="*50 + "\n")
            
            # 2. Check scoping submissions for cycle 13, report 156
            submission_query = select(ScopingSubmission).where(
                and_(
                    ScopingSubmission.cycle_id == 13,
                    ScopingSubmission.report_id == 156
                )
            ).order_by(ScopingSubmission.version.desc())
            
            submissions = (await db.execute(submission_query)).scalars().all()
            
            print(f"Scoping submissions for cycle 13, report 156: {len(submissions)} found")
            for sub in submissions:
                submitter_query = select(User).where(User.user_id == sub.submitted_by)
                submitter = (await db.execute(submitter_query)).scalar_one_or_none()
                
                print(f"\nSubmission {sub.submission_id}:")
                print(f"  Version: {sub.version}")
                print(f"  Is Latest: {sub.is_latest}")
                print(f"  Submitted by: {submitter.username if submitter else 'Unknown'}")
                print(f"  Submitted at: {sub.submitted_at}")
                print(f"  Attributes: {sub.scoped_attributes}/{sub.total_attributes}")
                
                # Check if reviewed
                review_query = select(ReportOwnerScopingReview).where(
                    ReportOwnerScopingReview.submission_id == sub.submission_id
                )
                review = (await db.execute(review_query)).scalar_one_or_none()
                if review:
                    print(f"  Reviewed: Yes - {review.review_decision}")
                else:
                    print(f"  Reviewed: No - PENDING")
            
            print("\n" + "="*50 + "\n")
            
            # 3. Check all Report Owners in the system
            ro_query = select(User).where(
                User.role.in_(["Report Owner", "Report Owner Executive"])
            )
            report_owners = (await db.execute(ro_query)).scalars().all()
            
            print(f"Report Owners in system: {len(report_owners)}")
            for ro in report_owners:
                # Count assigned reports
                count_query = select(func.count(Report.report_id)).where(
                    Report.report_owner_id == ro.user_id
                )
                report_count = (await db.execute(count_query)).scalar()
                
                print(f"\n{ro.username} ({ro.email}):")
                print(f"  Role: {ro.role}")
                print(f"  Assigned Reports: {report_count}")
                
                # Check pending reviews for this RO
                if report_count > 0:
                    # Get report IDs owned by this user
                    owned_reports_query = select(Report.report_id).where(
                        Report.report_owner_id == ro.user_id
                    )
                    owned_report_ids = (await db.execute(owned_reports_query)).scalars().all()
                    
                    # Count pending submissions
                    pending_query = select(func.count(ScopingSubmission.submission_id)).where(
                        and_(
                            ScopingSubmission.report_id.in_(owned_report_ids),
                            ScopingSubmission.is_latest == True,
                            ~exists(
                                select(ReportOwnerScopingReview)
                                .where(ReportOwnerScopingReview.submission_id == ScopingSubmission.submission_id)
                            )
                        )
                    )
                    pending_count = (await db.execute(pending_query)).scalar()
                    print(f"  Pending Reviews: {pending_count}")
            
            print("\n" + "="*50 + "\n")
            
            # 4. Test the pending-reviews query logic
            if report and report.report_owner_id:
                print("Testing pending-reviews endpoint logic for report owner...")
                
                # Get reports owned by the report owner
                reports_query = select(Report).where(
                    Report.report_owner_id == report.report_owner_id
                )
                owned_reports = (await db.execute(reports_query)).scalars().all()
                report_ids = [r.report_id for r in owned_reports]
                
                print(f"Reports owned by user {report.report_owner_id}: {report_ids}")
                
                # Get pending submissions
                pending_query = select(ScopingSubmission).where(
                    and_(
                        ScopingSubmission.report_id.in_(report_ids),
                        ScopingSubmission.is_latest == True,
                        ~exists(
                            select(ReportOwnerScopingReview)
                            .where(ReportOwnerScopingReview.submission_id == ScopingSubmission.submission_id)
                        )
                    )
                )
                
                pending_submissions = (await db.execute(pending_query)).scalars().all()
                print(f"Pending submissions found: {len(pending_submissions)}")
                
                for ps in pending_submissions:
                    print(f"  - Cycle {ps.cycle_id}, Report {ps.report_id}, Version {ps.version}")
            
        finally:
            await db.close()
            break


if __name__ == "__main__":
    asyncio.run(debug_report_owner())