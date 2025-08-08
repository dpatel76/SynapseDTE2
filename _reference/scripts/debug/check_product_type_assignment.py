#!/usr/bin/env python3
"""Check Product Type assignment status"""

import psycopg2
from psycopg2.extras import RealDictCursor

def check_product_type():
    """Check Product Type assignment status"""
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/synapse_dt")
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check if Product Type attribute exists
            cur.execute("""
                SELECT ra.*, r.report_name, tc.cycle_name
                FROM report_attributes ra
                JOIN reports r ON ra.report_id = r.report_id
                JOIN test_cycles tc ON ra.cycle_id = tc.cycle_id
                WHERE ra.attribute_name = 'Product Type'
                AND ra.cycle_id = 9
                AND ra.report_id = 156
            """)
            
            product_type = cur.fetchone()
            
            if product_type:
                print(f"✅ Product Type attribute found:")
                print(f"   - Attribute ID: {product_type['attribute_id']}")
                print(f"   - Is Primary Key: {product_type['is_primary_key']}")
                print(f"   - Report: {product_type['report_name']}")
                print(f"   - Cycle: {product_type['cycle_name']}")
                
                # Check DataProviderAssignment
                cur.execute("""
                    SELECT dpa.*, u.email as data_provider_email, u.first_name, u.last_name,
                           u2.email as cdo_email, u2.first_name as cdo_first_name, u2.last_name as cdo_last_name
                    FROM data_provider_assignments dpa
                    LEFT JOIN users u ON dpa.data_provider_id = u.user_id
                    LEFT JOIN users u2 ON dpa.cdo_id = u2.user_id
                    WHERE dpa.attribute_id = %s
                    AND dpa.cycle_id = 9
                    AND dpa.report_id = 156
                """, (product_type['attribute_id'],))
                
                assignment = cur.fetchone()
                
                if assignment:
                    print(f"\n✅ DataProviderAssignment found:")
                    print(f"   - Assignment ID: {assignment['assignment_id']}")
                    print(f"   - Status: {assignment['status']}")
                    print(f"   - CDO: {assignment['cdo_first_name']} {assignment['cdo_last_name']} ({assignment['cdo_email']})")
                    print(f"   - Data Provider: {assignment['data_provider_email'] or 'NOT ASSIGNED'}")
                    if assignment['data_provider_id']:
                        print(f"     Name: {assignment['first_name']} {assignment['last_name']}")
                else:
                    print("\n❌ No DataProviderAssignment found for Product Type")
                
                # Check AttributeLOBAssignment
                cur.execute("""
                    SELECT ala.*, l.lob_name, u.email, u.first_name, u.last_name
                    FROM attribute_lob_assignments ala
                    JOIN lobs l ON ala.lob_id = l.lob_id
                    JOIN users u ON ala.assigned_by = u.user_id
                    WHERE ala.attribute_id = %s
                    AND ala.cycle_id = 9
                    AND ala.report_id = 156
                """, (product_type['attribute_id'],))
                
                lob_assignment = cur.fetchone()
                
                if lob_assignment:
                    print(f"\n✅ AttributeLOBAssignment found:")
                    print(f"   - LOB: {lob_assignment['lob_name']}")
                    print(f"   - Assigned by: {lob_assignment['first_name']} {lob_assignment['last_name']} ({lob_assignment['email']})")
                    print(f"   - Assigned at: {lob_assignment['assigned_at']}")
                else:
                    print("\n❌ No AttributeLOBAssignment found for Product Type")
                
                # Check CDO for this LOB
                if lob_assignment:
                    cur.execute("""
                        SELECT u.* FROM users u
                        WHERE u.lob_id = %s
                        AND EXISTS (
                            SELECT 1 FROM user_roles ur
                            JOIN roles r ON ur.role_id = r.role_id
                            WHERE ur.user_id = u.user_id
                            AND r.role_name = 'Data Executive'
                        )
                    """, (lob_assignment['lob_id'],))
                    
                    cdo = cur.fetchone()
                    if cdo:
                        print(f"\n✅ Data Executive for LOB {lob_assignment['lob_name']}:")
                        print(f"   - {cdo['first_name']} {cdo['last_name']} ({cdo['email']})")
                    else:
                        print(f"\n❌ No Data Executive found for LOB {lob_assignment['lob_name']}")
                        
            else:
                print("❌ Product Type attribute not found for cycle 9, report 156")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Checking Product Type assignment status...")
    print("=" * 60)
    check_product_type()