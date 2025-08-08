import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.workflow import WorkflowPhase

async def investigate_workflow_phase_inconsistency():
    """Investigate workflow phase data inconsistency"""
    
    async for db in get_db():
        try:
            print("=" * 80)
            print("INVESTIGATING WORKFLOW PHASE DATA INCONSISTENCY")
            print("=" * 80)
            
            cycle_id = 9
            report_id = 156
            
            print(f"\n🔍 STEP 1: Detailed analysis of all workflow phases for cycle_id={cycle_id}, report_id={report_id}")
            
            all_phases = await db.execute(
                select(WorkflowPhase).where(and_(
                    WorkflowPhase.cycle_id == cycle_id,
                    WorkflowPhase.report_id == report_id
                )).order_by(WorkflowPhase.phase_name)
            )
            all_phases = all_phases.scalars().all()
            
            print(f"\nFound {len(all_phases)} workflow phases:")
            print("-" * 120)
            print(f"{'Phase Name':<20} {'Status':<12} {'State':<12} {'Start Date':<20} {'End Date':<20} {'Started By':<12} {'Completed By':<12}")
            print("-" * 120)
            
            inconsistent_phases = []
            
            for phase in all_phases:
                start_date_str = str(phase.actual_start_date) if phase.actual_start_date else "None"
                end_date_str = str(phase.actual_end_date) if phase.actual_end_date else "None"
                started_by_str = str(phase.started_by) if phase.started_by else "None"
                completed_by_str = str(phase.completed_by) if phase.completed_by else "None"
                
                print(f"{phase.phase_name:<20} {phase.status:<12} {phase.state:<12} {start_date_str:<20} {end_date_str:<20} {started_by_str:<12} {completed_by_str:<12}")
                
                # Check for inconsistencies
                if phase.status == "Complete" and phase.state == "Not Started":
                    inconsistent_phases.append({
                        'phase': phase.phase_name,
                        'issue': 'Status=Complete but State=Not Started'
                    })
                elif phase.status == "Complete" and not phase.actual_end_date:
                    inconsistent_phases.append({
                        'phase': phase.phase_name,
                        'issue': 'Status=Complete but no actual_end_date'
                    })
                elif phase.status == "Complete" and not phase.completed_by:
                    inconsistent_phases.append({
                        'phase': phase.phase_name,
                        'issue': 'Status=Complete but no completed_by'
                    })
                elif phase.status == "In Progress" and not phase.actual_start_date:
                    inconsistent_phases.append({
                        'phase': phase.phase_name,
                        'issue': 'Status=In Progress but no actual_start_date'
                    })
                elif phase.status == "Not Started" and phase.actual_start_date:
                    inconsistent_phases.append({
                        'phase': phase.phase_name,
                        'issue': 'Status=Not Started but has actual_start_date'
                    })
            
            print("\n🔍 STEP 2: Inconsistency Analysis")
            if inconsistent_phases:
                print(f"\n❌ Found {len(inconsistent_phases)} inconsistent phases:")
                for issue in inconsistent_phases:
                    print(f"   - {issue['phase']}: {issue['issue']}")
                
                print(f"\n💡 RECOMMENDED FIXES:")
                for phase in all_phases:
                    if phase.status == "Complete" and phase.state == "Not Started":
                        print(f"   - {phase.phase_name}: Update state to 'Complete' to match status")
                    elif phase.status == "Complete" and not phase.actual_end_date:
                        print(f"   - {phase.phase_name}: Set actual_end_date since status is Complete")
                    elif phase.status == "Complete" and not phase.completed_by:
                        print(f"   - {phase.phase_name}: Set completed_by since status is Complete")
            else:
                print("✅ No inconsistencies found")
            
            print(f"\n🔍 STEP 3: Understanding the root cause")
            print("The inconsistency suggests that:")
            print("1. Phases were marked as 'Complete' in status")
            print("2. But their state was never updated from 'Not Started'")
            print("3. This creates confusion in the UI logic")
            print("4. The 'state' field might be redundant or not properly maintained")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
            break

if __name__ == "__main__":
    asyncio.run(investigate_workflow_phase_inconsistency()) 