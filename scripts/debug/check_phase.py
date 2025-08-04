import sys
sys.path.append('.')
from app.core.database import get_db
from app.models.request_info import RequestInfoPhase
from sqlalchemy.orm import Session

# Get database session
db_gen = get_db()
db: Session = next(db_gen)

try:
    # Check if phase exists
    phase = db.query(RequestInfoPhase).filter(
        RequestInfoPhase.cycle_id == 9,
        RequestInfoPhase.report_id == 156
    ).first()
    
    if phase:
        print(f'Phase found: {phase.phase_id}')
        print(f'Status: {phase.phase_status}')
        print(f'Cycle: {phase.cycle_id}, Report: {phase.report_id}')
    else:
        print('No phase found for cycle 9, report 156')
        
    # Check all phases
    all_phases = db.query(RequestInfoPhase).all()
    print(f'Total phases in database: {len(all_phases)}')
    for p in all_phases:
        print(f'  Phase {p.phase_id}: Cycle {p.cycle_id}, Report {p.report_id}, Status: {p.phase_status}')
        
finally:
    db.close() 