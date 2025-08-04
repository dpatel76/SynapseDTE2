#!/usr/bin/env python3
"""Final test to demonstrate complete sample selection workflow with version tables"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
import sys
sys.path.append('/Users/dineshpatel/code/projects/SynapseDTE')

from app.services.sample_selection_v2_service import SampleSelectionServiceV2
from app.models.workflow import WorkflowPhase
from app.models.sample_selection import SampleSelectionVersion, SampleSelectionSample, VersionStatus
from app.models.lob import LOB
from app.models.user import User

async def demonstrate_workflow():
    engine = create_async_engine(
        "postgresql+asyncpg://synapse_user:synapse_password@localhost:5432/synapse_dt",
        echo=False
    )
    
    async with AsyncSession(engine) as db:
        print("=== Sample Selection Version Table Implementation ===")
        
        # Get phase
        phase_query = await db.execute(
            select(WorkflowPhase).where(
                WorkflowPhase.cycle_id == 55,
                WorkflowPhase.report_id == 156,
                WorkflowPhase.phase_name == "Sample Selection"
            )
        )
        phase = phase_query.scalar_one()
        
        # Get users
        tester_query = await db.execute(select(User).where(User.email == "tester@example.com"))
        tester = tester_query.scalar_one()
        
        ro_query = await db.execute(select(User).where(User.email == "report.owner@example.com"))
        report_owner = ro_query.scalar_one()
        
        # Get LOBs
        lob_query = await db.execute(select(LOB).limit(3))
        lobs = list(lob_query.scalars().all())
        
        print(f"\nWorking with:")
        print(f"  Phase: {phase.phase_id}")
        print(f"  Tester: {tester.first_name} {tester.last_name}")
        print(f"  Report Owner: {report_owner.first_name} {report_owner.last_name}")
        print(f"  LOBs: {[lob.lob_name for lob in lobs]}")
        
        # Step 1: Create initial version with samples
        print("\n1. Creating initial version with samples...")
        v1 = await SampleSelectionServiceV2.get_or_create_version(
            db, phase.phase_id, tester.user_id
        )
        
        # Add samples
        samples_data = []
        for i, lob in enumerate(lobs[:2]):
            samples_data.append({
                "lob_id": lob.lob_id,
                "sample_identifier": f"SAMPLE-{i+1:03d}",
                "sample_category": "clean" if i % 2 == 0 else "anomaly",
                "sample_data": {
                    "customer_id": f"CUST{i+1:04d}",
                    "account_number": f"ACC{i+1:06d}",
                    "balance": 1000 * (i + 1)
                },
                "risk_score": 0.1 + (i * 0.3)
            })
        
        samples = await SampleSelectionServiceV2.add_samples_to_version(
            db, v1.version_id, samples_data, tester.user_id
        )
        print(f"  Created version 1 with {len(samples)} samples")
        
        # Step 2: Tester approves samples
        print("\n2. Tester approving samples...")
        for sample in samples:
            await SampleSelectionServiceV2.update_sample_decision(
                db, sample.sample_id, "approved", "Looks good", tester.user_id
            )
        
        # Submit for approval
        await SampleSelectionServiceV2.submit_version_for_approval(
            db, v1.version_id, tester.user_id, "Initial submission"
        )
        print("  Version 1 submitted for approval")
        
        # Step 3: Report Owner reviews and requests changes
        print("\n3. Report Owner reviewing...")
        # Update metadata to indicate RO reviewed
        v1.metadata['reviewed_by_report_owner'] = True
        v1.metadata['report_owner_id'] = report_owner.user_id
        v1.metadata['report_owner_decision'] = 'revision_required'
        
        # RO provides feedback on samples
        await SampleSelectionServiceV2.update_sample_decision(
            db, samples[0].sample_id, "rejected", "Need different sample", 
            report_owner.user_id, is_report_owner=True
        )
        await SampleSelectionServiceV2.update_sample_decision(
            db, samples[1].sample_id, "approved", "Good sample", 
            report_owner.user_id, is_report_owner=True
        )
        print("  Report Owner provided feedback")
        
        # Step 4: Make Changes - Create new version from RO feedback
        print("\n4. Making changes based on RO feedback...")
        v2 = await SampleSelectionServiceV2.create_new_version(
            db, phase.phase_id, tester.user_id,
            parent_version_id=v1.version_id,
            copy_samples=True,
            change_reason="Incorporating Report Owner feedback"
        )
        
        # Add new sample to replace rejected one
        new_sample_data = [{
            "lob_id": lobs[2].lob_id,
            "sample_identifier": "SAMPLE-003",
            "sample_category": "clean",
            "sample_data": {
                "customer_id": "CUST0003",
                "account_number": "ACC000003",
                "balance": 5000
            },
            "risk_score": 0.2
        }]
        
        await SampleSelectionServiceV2.add_samples_to_version(
            db, v2.version_id, new_sample_data, tester.user_id
        )
        print(f"  Created version 2 with {v2.actual_sample_size + 1} samples")
        
        # Step 5: Submit v2 and get final approval
        print("\n5. Submitting v2 for final approval...")
        await SampleSelectionServiceV2.submit_version_for_approval(
            db, v2.version_id, tester.user_id, "Updated based on feedback"
        )
        
        # Simulate approval
        v2.version_status = VersionStatus.APPROVED
        v2.approved_by_id = report_owner.user_id
        v2.metadata['reviewed_by_report_owner'] = True
        v2.metadata['report_owner_decision'] = 'approved'
        print("  Version 2 approved!")
        
        # Step 6: Show version history
        print("\n6. Version History:")
        all_versions = await SampleSelectionServiceV2.get_all_versions_for_phase(
            db, phase.phase_id
        )
        
        for v in sorted(all_versions, key=lambda x: x.version_number):
            samples = await SampleSelectionServiceV2.get_samples_for_version(db, v.version_id)
            ro_reviewed = v.metadata.get('reviewed_by_report_owner', False)
            print(f"  v{v.version_number}: {v.version_status.value}")
            print(f"    - Samples: {len(samples)}")
            print(f"    - RO Reviewed: {'Yes' if ro_reviewed else 'No'}")
            if ro_reviewed:
                print(f"    - RO Decision: {v.metadata.get('report_owner_decision', 'N/A')}")
        
        # Step 7: Verify latest version with RO feedback
        print("\n7. Finding latest version with RO feedback:")
        latest_ro_version = await SampleSelectionServiceV2.get_latest_version_with_report_owner_feedback(
            db, phase.phase_id
        )
        
        if latest_ro_version:
            print(f"  Latest RO reviewed version: v{latest_ro_version.version_number}")
            print(f"  Decision: {latest_ro_version.metadata.get('report_owner_decision')}")
        
        await db.commit()
        print("\n✅ Sample Selection with Version Tables - Complete!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(demonstrate_workflow())