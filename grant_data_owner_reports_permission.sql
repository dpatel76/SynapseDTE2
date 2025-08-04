-- Grant reports:read permission to Data Owner role
-- This allows Data Owners to view the Reports page

-- Check if the permission already exists
DO $$
BEGIN
    -- Check if Data Owner role has reports:read permission
    IF NOT EXISTS (
        SELECT 1 
        FROM rbac_role_permissions rp
        JOIN rbac_roles r ON r.role_id = rp.role_id
        JOIN rbac_permissions p ON p.permission_id = rp.permission_id
        WHERE r.role_name = 'Data Owner'
        AND p.resource = 'reports'
        AND p.action = 'read'
    ) THEN
        -- Insert the permission
        INSERT INTO rbac_role_permissions (role_id, permission_id, granted_at, created_at, updated_at)
        SELECT 
            r.role_id,
            p.permission_id,
            NOW(),
            NOW(),
            NOW()
        FROM rbac_roles r
        CROSS JOIN rbac_permissions p
        WHERE r.role_name = 'Data Owner'
        AND p.resource = 'reports'
        AND p.action = 'read';
        
        RAISE NOTICE 'Added reports:read permission to Data Owner role';
    ELSE
        RAISE NOTICE 'Data Owner already has reports:read permission';
    END IF;
END $$;

-- Verify the permission was added
SELECT 
    r.role_name,
    p.resource,
    p.action,
    p.description,
    rp.granted_at
FROM rbac_role_permissions rp
JOIN rbac_roles r ON r.role_id = rp.role_id
JOIN rbac_permissions p ON p.permission_id = rp.permission_id
WHERE r.role_name = 'Data Owner'
AND p.resource = 'reports'
AND p.action = 'read';