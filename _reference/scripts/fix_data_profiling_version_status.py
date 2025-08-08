#!/usr/bin/env python3
"""
Fix data profiling versions that are stuck in DRAFT status but have been sent to report owner.
This script identifies versions that have rules with report owner decisions but are still in draft status.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.data_profiling import DataProfilingRuleVersion, ProfilingRule, VersionStatus, Decision


async def fix_stuck_versions():
    """Find and fix versions that are stuck in draft but have report owner activity"""
    async with AsyncSessionLocal() as db:
        try:
            # Find versions that are in DRAFT status but have rules with report owner decisions
            query = select(DataProfilingRuleVersion).join(
                ProfilingRule, ProfilingRule.version_id == DataProfilingRuleVersion.version_id
            ).where(
                and_(
                    DataProfilingRuleVersion.version_status == VersionStatus.DRAFT,
                    ProfilingRule.report_owner_decision.isnot(None)
                )
            ).distinct()
            
            result = await db.execute(query)
            stuck_versions = result.scalars().all()
            
            if not stuck_versions:
                print("✅ No stuck versions found. All versions are in correct status.")
                return
            
            print(f"🔍 Found {len(stuck_versions)} version(s) stuck in DRAFT status with report owner activity:")
            
            for version in stuck_versions:
                # Get counts of rules with report owner decisions
                ro_decision_count_query = await db.execute(
                    select(func.count(ProfilingRule.rule_id))
                    .where(
                        and_(
                            ProfilingRule.version_id == version.version_id,
                            ProfilingRule.report_owner_decision.isnot(None)
                        )
                    )
                )
                ro_decision_count = ro_decision_count_query.scalar() or 0
                
                # Get counts of rules with tester decisions
                tester_decision_count_query = await db.execute(
                    select(func.count(ProfilingRule.rule_id))
                    .where(
                        and_(
                            ProfilingRule.version_id == version.version_id,
                            ProfilingRule.tester_decision.isnot(None)
                        )
                    )
                )
                tester_decision_count = tester_decision_count_query.scalar() or 0
                
                print(f"\n📋 Version ID: {version.version_id}")
                print(f"   Version Number: {version.version_number}")
                print(f"   Phase ID: {version.phase_id}")
                print(f"   Current Status: {version.version_status}")
                print(f"   Rules with Tester Decisions: {tester_decision_count}")
                print(f"   Rules with Report Owner Decisions: {ro_decision_count}")
                
                # Update the version status to PENDING_APPROVAL
                version.version_status = VersionStatus.PENDING_APPROVAL
                version.updated_at = datetime.utcnow()
                
                # If the version wasn't submitted, set submitted timestamp
                if not version.submitted_at:
                    version.submitted_at = datetime.utcnow()
                
                print(f"   ✏️  Updating status to: PENDING_APPROVAL")
            
            # Commit all changes
            await db.commit()
            print(f"\n✅ Successfully updated {len(stuck_versions)} version(s) to PENDING_APPROVAL status.")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            await db.rollback()
            raise


async def check_specific_version(version_id: str):
    """Check a specific version's status and details"""
    async with AsyncSessionLocal() as db:
        try:
            # Get the version
            query = select(DataProfilingRuleVersion).where(
                DataProfilingRuleVersion.version_id == version_id
            )
            result = await db.execute(query)
            version = result.scalar_one_or_none()
            
            if not version:
                print(f"❌ Version {version_id} not found.")
                return
            
            print(f"\n📋 Version Details:")
            print(f"   Version ID: {version.version_id}")
            print(f"   Version Number: {version.version_number}")
            print(f"   Phase ID: {version.phase_id}")
            print(f"   Current Status: {version.version_status}")
            print(f"   Created At: {version.created_at}")
            print(f"   Submitted At: {version.submitted_at}")
            print(f"   Approved At: {version.approved_at}")
            
            # Get rule statistics
            rules_query = await db.execute(
                select(
                    func.count(ProfilingRule.rule_id).label('total'),
                    func.count(ProfilingRule.tester_decision).label('with_tester_decision'),
                    func.count(ProfilingRule.report_owner_decision).label('with_ro_decision')
                )
                .where(ProfilingRule.version_id == version.version_id)
            )
            stats = rules_query.one()
            
            print(f"\n📊 Rule Statistics:")
            print(f"   Total Rules: {stats.total}")
            print(f"   Rules with Tester Decision: {stats.with_tester_decision}")
            print(f"   Rules with Report Owner Decision: {stats.with_ro_decision}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix data profiling version statuses")
    parser.add_argument("--check", help="Check a specific version ID", type=str)
    parser.add_argument("--fix", action="store_true", help="Fix all stuck versions")
    
    args = parser.parse_args()
    
    if args.check:
        asyncio.run(check_specific_version(args.check))
    elif args.fix:
        asyncio.run(fix_stuck_versions())
    else:
        print("Usage:")
        print("  python fix_data_profiling_version_status.py --check <version_id>  # Check specific version")
        print("  python fix_data_profiling_version_status.py --fix                 # Fix all stuck versions")