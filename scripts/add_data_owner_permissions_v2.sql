-- Add data source management permissions for Data Owner role
-- This script adds the necessary permissions for Data Owners to manage data sources

-- Insert new permissions with available IDs
INSERT INTO rbac_permissions (permission_id, resource, action, description, created_at)
VALUES 
    (85, 'data_source', 'manage', 'Create, update and test data sources', NOW()),
    (86, 'request_info', 'write', 'Write access to request info resources', NOW())
ON CONFLICT (permission_id) DO NOTHING;

-- Grant these permissions to Data Owner role (role_id = 6)
INSERT INTO rbac_role_permissions (role_id, permission_id, created_at)
VALUES 
    (6, 85, NOW()),  -- data_source:manage
    (6, 86, NOW())   -- request_info:write
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Also grant to Admin role (look up admin role_id)
INSERT INTO rbac_role_permissions (role_id, permission_id, created_at)
SELECT r.role_id, p.permission_id, NOW()
FROM rbac_roles r
CROSS JOIN (VALUES (85), (86)) AS p(permission_id)
WHERE r.role_name = 'Admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Verify the permissions were added
SELECT 
    r.role_name,
    p.resource || ':' || p.action as permission,
    p.description
FROM rbac_roles r
JOIN rbac_role_permissions rp ON r.role_id = rp.role_id
JOIN rbac_permissions p ON rp.permission_id = p.permission_id
WHERE r.role_name IN ('Data Owner', 'Admin')
  AND p.permission_id IN (85, 86)
ORDER BY r.role_name, p.permission_id;