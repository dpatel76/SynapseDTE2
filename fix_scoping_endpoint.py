"""
Fix the scoping endpoint to avoid enum issues
"""

# New cleaned up version of the endpoint
clean_endpoint = '''@router.get("/cycles/{cycle_id}/reports/{report_id}/attributes")
async def get_scoping_attributes_legacy(
    cycle_id: int,
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Legacy endpoint for scoping attributes"""
    try:
        # First, rollback any existing transaction errors
        await db.rollback()
        
        # Get the phase for this cycle/report using text query to avoid enum issues
        from sqlalchemy import text
        
        phase_query = await db.execute(
            text("""
                SELECT phase_id, cycle_id, report_id, phase_name, status
                FROM workflow_phases 
                WHERE cycle_id = :cycle_id 
                AND report_id = :report_id 
                AND phase_name::text = 'Scoping'
                ORDER BY phase_id DESC
                LIMIT 1
            """),
            {"cycle_id": cycle_id, "report_id": report_id}
        )
        phase_result = phase_query.first()
        
        if not phase_result:
            raise HTTPException(status_code=404, detail="Scoping phase not found")
        
        # Get the latest version by version number using text query
        version_query = await db.execute(
            text("""
                SELECT version_id, version_number, phase_id, version_status
                FROM cycle_report_scoping_versions
                WHERE phase_id = :phase_id
                ORDER BY version_number DESC
                LIMIT 1
            """),
            {"phase_id": phase_result.phase_id}
        )
        current_version = version_query.first()
        
        if not current_version:
            return []  # Return empty array directly
            
        # Query scoping attributes using text query
        scoping_attrs_query = await db.execute(
            text("""
                SELECT 
                    sa.attribute_id,
                    sa.version_id,
                    sa.planning_attribute_id,
                    sa.tester_decision,
                    sa.report_owner_decision,
                    sa.tester_rationale,
                    sa.report_owner_feedback,
                    pa.attribute_name,
                    pa.attribute_description,
                    pa.sample_attribute_values,
                    pa.is_primary_key,
                    pa.is_nullable,
                    pa.table_name
                FROM cycle_report_scoping_attributes sa
                JOIN cycle_report_planning_attributes pa ON sa.planning_attribute_id = pa.id
                WHERE sa.version_id = :version_id
                ORDER BY pa.attribute_name
            """),
            {"version_id": current_version.version_id}
        )
        
        scoping_attrs = scoping_attrs_query.fetchall()
        
        # If no scoping attributes, return empty array
        if not scoping_attrs:
            return []
        
        # Build simplified response using data from text query
        attributes = []
        for row in scoping_attrs:
            attributes.append({
                "attribute_id": str(row.attribute_id),
                "planning_attribute_id": row.planning_attribute_id,
                "attribute_name": row.attribute_name,
                "description": row.attribute_description,
                "is_primary_key": row.is_primary_key,
                "is_nullable": row.is_nullable,
                "table_name": row.table_name,
                "sample_attribute_values": row.sample_attribute_values,
                "tester_decision": row.tester_decision,
                "report_owner_decision": row.report_owner_decision,
                "tester_rationale": row.tester_rationale,
                "report_owner_feedback": row.report_owner_feedback,
                "selected_for_testing": row.tester_decision == "accept" if row.tester_decision else False
            })
        
        return attributes
    except Exception as e:
        import traceback
        logger.error(f"Error retrieving scoping attributes: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")
'''

print("Clean endpoint code saved to fix_scoping_endpoint.py")
print("\nTo apply the fix:")
print("1. Find the get_scoping_attributes_legacy function in app/api/v1/endpoints/scoping.py")
print("2. Replace it with the clean version above")