-- Add data source management permissions for Data Owner role
-- This script adds the necessary permissions for Data Owners to manage data sources

-- Insert new permissions
INSERT INTO rbac_permissions (permission_id, resource, action, description, created_at)
VALUES 
    (70, 'data_source', 'manage', 'Create, update and test data sources', NOW()),
    (71, 'request_info', 'write', 'Write access to request info resources', NOW()),
    (72, 'request_info', 'read', 'Read access to request info resources', NOW())
ON CONFLICT (permission_id) DO NOTHING;

-- Grant these permissions to Data Owner role (role_id = 6)
INSERT INTO rbac_role_permissions (role_id, permission_id, created_at)
VALUES 
    (6, 70, NOW()),  -- data_source:manage
    (6, 71, NOW()),  -- request_info:write
    (6, 72, NOW())   -- request_info:read
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Also grant to Admin role (role_id = 7)
INSERT INTO rbac_role_permissions (role_id, permission_id, created_at)
VALUES 
    (7, 70, NOW()),
    (7, 71, NOW()),
    (7, 72, NOW())
ON CONFLICT (role_id, permission_id) DO NOTHING;

-- Verify the permissions were added
SELECT 
    r.role_name,
    p.resource || ':' || p.action as permission,
    p.description
FROM rbac_roles r
JOIN rbac_role_permissions rp ON r.role_id = rp.role_id
JOIN rbac_permissions p ON rp.permission_id = p.permission_id
WHERE r.role_id IN (6, 7) 
  AND p.permission_id IN (70, 71, 72)
ORDER BY r.role_name, p.permission_id;