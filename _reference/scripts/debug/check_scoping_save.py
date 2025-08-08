import asyncio
import asyncpg

async def check_scoping_save():
    conn = await asyncpg.connect('postgresql://synapse_user:synapse_password@localhost:5432/synapse_dt')
    
    # Get the latest cycle
    latest_cycle = await conn.fetchrow("""
        SELECT cycle_id FROM test_cycles ORDER BY cycle_id DESC LIMIT 1
    """)
    cycle_id = latest_cycle['cycle_id']
    
    print(f"=== CHECKING SCOPING DECISIONS FOR CYCLE {cycle_id} ===")
    
    # Get all scoping decisions with attribute details
    decisions = await conn.fetch("""
        SELECT 
            tsd.decision_id, 
            tsd.attribute_id, 
            tsd.final_scoping, 
            tsd.decision,
            tsd.tester_rationale,
            ra.attribute_name, 
            ra.is_primary_key,
            tsd.updated_at
        FROM cycle_report_scoping_tester_decisions tsd
        JOIN report_attributes ra ON tsd.attribute_id = ra.attribute_id
        WHERE tsd.cycle_id = $1
        ORDER BY tsd.updated_at DESC, tsd.decision_id DESC
        LIMIT 20
    """, cycle_id)
    
    print(f"Total decisions found: {len(decisions)}")
    print()
    
    # Separate PK and non-PK attributes
    pk_included = []
    non_pk_included = []
    non_pk_excluded = []
    
    for decision in decisions:
        is_pk = decision['is_primary_key']
        is_included = decision['final_scoping']
        
        if is_pk and is_included:
            pk_included.append(decision)
        elif not is_pk and is_included:
            non_pk_included.append(decision)
        elif not is_pk and not is_included:
            non_pk_excluded.append(decision)
    
    print(f"📊 SUMMARY:")
    print(f"  - PK attributes included: {len(pk_included)}")
    print(f"  - Non-PK attributes included: {len(non_pk_included)}")
    print(f"  - Non-PK attributes excluded: {len(non_pk_excluded)}")
    print()
    
    if pk_included:
        print("✅ PRIMARY KEY ATTRIBUTES (Included):")
        for decision in pk_included[:5]:  # Show first 5
            print(f"  - {decision['attribute_name']} (ID: {decision['attribute_id']})")
            print(f"    final_scoping: {decision['final_scoping']}, decision: {decision['decision']}")
            print(f"    rationale: {decision['tester_rationale']}")
        print()
    
    if non_pk_included:
        print("✅ NON-PK ATTRIBUTES (Included):")
        for decision in non_pk_included:
            print(f"  - {decision['attribute_name']} (ID: {decision['attribute_id']})")
            print(f"    final_scoping: {decision['final_scoping']}, decision: {decision['decision']}")
            print(f"    rationale: {decision['tester_rationale']}")
            print(f"    updated_at: {decision['updated_at']}")
        print()
    else:
        print("❌ NO NON-PK ATTRIBUTES INCLUDED")
        print()
    
    if non_pk_excluded:
        print("❌ NON-PK ATTRIBUTES (Excluded - showing first 5):")
        for decision in non_pk_excluded[:5]:
            print(f"  - {decision['attribute_name']} (ID: {decision['attribute_id']})")
            print(f"    final_scoping: {decision['final_scoping']}, decision: {decision['decision']}")
        print()
    
    # Check latest submission
    print("=== LATEST SUBMISSION ===")
    submission = await conn.fetchrow("""
        SELECT submission_id, total_attributes, scoped_attributes, skipped_attributes, 
               submission_notes, created_at
        FROM cycle_report_scoping_submissions 
        WHERE cycle_id = $1
        ORDER BY created_at DESC
        LIMIT 1
    """, cycle_id)
    
    if submission:
        print(f"Submission ID: {submission['submission_id']}")
        print(f"Total: {submission['total_attributes']}, Scoped: {submission['scoped_attributes']}, Skipped: {submission['skipped_attributes']}")
        print(f"Notes: {submission['submission_notes']}")
        print(f"Created: {submission['created_at']}")
    else:
        print("No submission found yet")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check_scoping_save()) 