import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.core.database import get_db
from app.models.workflow import WorkflowPhase

async def fix_workflow_phase_inconsistency():
    """Fix workflow phase data inconsistency"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("FIXING WORKFLOW PHASE DATA INCONSISTENCY")
            print("=" * 80)
            
            cycle_id = 9
            report_id = 156
            
            print(f"\n🔧 STEP 1: Fixing inconsistent phases for cycle_id={cycle_id}, report_id={report_id}")
            
            # Get all phases with inconsistent status/state
            inconsistent_phases = await db.execute(
                select(WorkflowPhase).where(and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id,
                    WorkflowPhase.status == "Complete",
                    WorkflowPhase.state == "Not Started"
                ))
            )
            inconsistent_phases = inconsistent_phases.scalars().all()
            
            print(f"Found {len(inconsistent_phases)} phases to fix:")
            
            for phase in inconsistent_phases:
                print(f"   - {phase.phase_name}: Updating state from 'Not Started' to 'Complete'")
                
                # Update the state to match the status
                phase.state = "Complete"
                
                # Also ensure completed_by is set if it's missing
                if not phase.completed_by and phase.started_by:
                    phase.completed_by = phase.started_by
                    print(f"     Also setting completed_by = {phase.started_by}")
            
            # Commit the changes
            await db.commit()
            print(f"\n✅ Successfully updated {len(inconsistent_phases)} phases")
            
            print(f"\n🔍 STEP 2: Verifying the fixes")
            
            # Verify all phases are now consistent
            all_phases = await db.execute(
                select(WorkflowPhase).where(and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id
                )).order_by(WorkflowPhase.phase_name)
            )
            all_phases = all_phases.scalars().all()
            
            print(f"\nUpdated workflow phases:")
            print("-" * 80)
            print(f"{'Phase Name':<20} {'Status':<12} {'State':<12} {'Consistent?':<12}")
            print("-" * 80)
            
            all_consistent = True
            for phase in all_phases:
                is_consistent = (
                    (phase.status == "Complete" and phase.state == "Complete") or
                    (phase.status == "In Progress" and phase.state == "In Progress") or
                    (phase.status == "Not Started" and phase.state == "Not Started")
                )
                
                consistency_status = "✅ Yes" if is_consistent else "❌ No"
                if not is_consistent:
                    all_consistent = False
                
                print(f"{phase.phase_name:<20} {phase.status:<12} {phase.state:<12} {consistency_status:<12}")
            
            if all_consistent:
                print(f"\n🎉 All phases are now consistent!")
            else:
                print(f"\n⚠️  Some phases still have inconsistencies")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(fix_workflow_phase_inconsistency()) 