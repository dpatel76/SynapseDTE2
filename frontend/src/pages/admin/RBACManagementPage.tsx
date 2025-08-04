import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Checkbox,
  Grid,
  Alert,
  Snackbar,
  FormControlLabel,
  Switch,
  Tooltip,
  Divider,
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  Security,
  Group,
  Person,
  Lock,
  LockOpen,
  History,
  Search,
  FilterList,
  Save,
  Cancel,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';

interface Permission {
  permission_id: number;
  resource: string;
  action: string;
  description: string;
}

interface Role {
  role_id: number;
  role_name: string;
  description: string;
  is_system: boolean;
  is_active: boolean;
  role_permissions?: RolePermission[];
  permissions?: Permission[];
  user_count?: number;
}

interface RolePermission {
  permission: Permission;
}

interface User {
  user_id: number;
  email: string;
  full_name: string;
  roles: Role[];
}

interface RoleRestrictions {
  role_name: string;
  role_description: string;
  total_permissions: number;
  allowed_count: number;
  forbidden_count: number;
  allowed_permissions: string[];
  forbidden_permissions: string[];
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`rbac-tabpanel-${index}`}
      aria-labelledby={`rbac-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const RBACManagementPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [selectedRole, setSelectedRole] = useState<Role | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [createRoleDialog, setCreateRoleDialog] = useState(false);
  const [editPermissionsDialog, setEditPermissionsDialog] = useState(false);
  const [userRolesDialog, setUserRolesDialog] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'warning' });
  const queryClient = useQueryClient();

  // Queries
  const { data: permissions = [] } = useQuery<Permission[]>({
    queryKey: ['permissions'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/rbac/permissions');
      return response.data;
    },
  });

  const { data: roles = [] } = useQuery<Role[]>({
    queryKey: ['roles'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/rbac/roles', {
        params: { include_permissions: true, include_user_count: true },
      });
      return response.data;
    },
  });

  const { data: usersResponse } = useQuery({
    queryKey: ['users-with-roles'],
    queryFn: async () => {
      const response = await apiClient.get('/users/', {
        params: { include_roles: true },
      });
      return response.data;
    },
  });

  const users = usersResponse?.users || [];

  // Add query for role restrictions when editing permissions
  const { data: roleRestrictions } = useQuery<RoleRestrictions>({
    queryKey: ['role-restrictions', selectedRole?.role_id],
    queryFn: async () => {
      if (!selectedRole) return null;
      const response = await apiClient.get(`/admin/rbac/roles/${selectedRole.role_id}/permissions/restrictions`);
      return response.data;
    },
    enabled: !!selectedRole && editPermissionsDialog,
  });

  const { data: auditLogs = [] } = useQuery({
    queryKey: ['permission-audit-logs'],
    queryFn: async () => {
      const response = await apiClient.get('/admin/rbac/audit-log/', {
        params: { limit: 50 },
      });
      return response.data;
    },
    enabled: activeTab === 3,
  });

  // Mutations
  const createRoleMutation = useMutation({
    mutationFn: async (data: { role_name: string; description: string }) => {
      const response = await apiClient.post('/admin/rbac/roles', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      setCreateRoleDialog(false);
      setSnackbar({ open: true, message: 'Role created successfully', severity: 'success' });
    },
    onError: () => {
      setSnackbar({ open: true, message: 'Failed to create role', severity: 'error' });
    },
  });

  const updateRolePermissionsMutation = useMutation({
    mutationFn: async ({ roleId, permissionIds }: { roleId: number; permissionIds: number[] }) => {
      const response = await apiClient.put(`/admin/rbac/roles/${roleId}/permissions`, {
        permission_ids: permissionIds,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      setEditPermissionsDialog(false);
      setSnackbar({ open: true, message: 'Permissions updated successfully', severity: 'success' });
    },
  });

  const assignRoleToUserMutation = useMutation({
    mutationFn: async ({ userId, roleId }: { userId: number; roleId: number }) => {
      const response = await apiClient.post(`/admin/rbac/users/${userId}/roles`, {
        role_id: roleId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users-with-roles'] });
      setSnackbar({ open: true, message: 'Role assigned successfully', severity: 'success' });
    },
  });

  const removeRoleFromUserMutation = useMutation({
    mutationFn: async ({ userId, roleId }: { userId: number; roleId: number }) => {
      const response = await apiClient.delete(`/admin/rbac/users/${userId}/roles/${roleId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users-with-roles'] });
      setSnackbar({ open: true, message: 'Role removed successfully', severity: 'success' });
    },
  });

  // Group permissions by resource
  const permissionsByResource = permissions.reduce((acc, perm) => {
    if (!acc[perm.resource]) {
      acc[perm.resource] = [];
    }
    acc[perm.resource].push(perm);
    return acc;
  }, {} as Record<string, Permission[]>);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <Security sx={{ mr: 1, verticalAlign: 'bottom' }} />
        RBAC Management
      </Typography>

      <Card>
        <Tabs value={activeTab} onChange={handleTabChange} sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tab label="Roles" icon={<Group />} iconPosition="start" />
          <Tab label="Permissions" icon={<Lock />} iconPosition="start" />
          <Tab label="Users" icon={<Person />} iconPosition="start" />
          <Tab label="Audit Log" icon={<History />} iconPosition="start" />
        </Tabs>

        <TabPanel value={activeTab} index={0}>
          {/* Roles Tab */}
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="h6">System Roles</Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateRoleDialog(true)}
            >
              Create Role
            </Button>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Role Name</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell align="center">Permissions</TableCell>
                  <TableCell align="center">Users</TableCell>
                  <TableCell align="center">System Role</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {roles.map((role) => (
                  <TableRow key={role.role_id}>
                    <TableCell>
                      <Typography variant="subtitle2">{role.role_name}</Typography>
                    </TableCell>
                    <TableCell>{role.description}</TableCell>
                    <TableCell align="center">
                      <Chip
                        label={(role.permissions?.length || role.role_permissions?.length) || 0}
                        size="small"
                        color="primary"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={role.user_count || 0}
                        size="small"
                        color="secondary"
                      />
                    </TableCell>
                    <TableCell align="center">
                      {role.is_system ? (
                        <Chip label="System" size="small" />
                      ) : (
                        <Chip label="Custom" size="small" variant="outlined" />
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedRole(role);
                          setEditPermissionsDialog(true);
                        }}
                      >
                        <Edit />
                      </IconButton>
                      {!role.is_system && (
                        <IconButton size="small" color="error">
                          <Delete />
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          {/* Permissions Tab */}
          <Typography variant="h6" gutterBottom>
            System Permissions
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Permissions are organized by resource and action
          </Typography>

          {Object.entries(permissionsByResource).map(([resource, perms]) => (
            <Card key={resource} sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {resource.charAt(0).toUpperCase() + resource.slice(1)}
                </Typography>
                <Box
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: {
                      xs: '1fr',
                      sm: 'repeat(2, 1fr)',
                      md: 'repeat(3, 1fr)'
                    },
                    gap: 2
                  }}
                >
                  {perms.map((perm) => (
                    <Paper key={perm.permission_id} variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="subtitle2">
                        {perm.resource}:{perm.action}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {perm.description}
                      </Typography>
                    </Paper>
                  ))}
                </Box>
              </CardContent>
            </Card>
          ))}
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          {/* Users Tab */}
          <Typography variant="h6" gutterBottom>
            User Role Assignments
          </Typography>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>User</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Assigned Roles</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user: any) => (
                  <TableRow key={user.user_id}>
                    <TableCell>{user.full_name}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>
                      {(user.roles || []).map((role: any) => (
                        <Chip
                          key={role.role_id}
                          label={role.role_name}
                          size="small"
                          sx={{ mr: 0.5 }}
                          onDelete={() => removeRoleFromUserMutation.mutate({
                            userId: user.user_id,
                            roleId: role.role_id,
                          })}
                        />
                      ))}
                    </TableCell>
                    <TableCell align="center">
                      <Button
                        size="small"
                        onClick={() => {
                          setSelectedUser(user);
                          setUserRolesDialog(true);
                        }}
                      >
                        Manage Roles
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          {/* Audit Log Tab */}
          <Typography variant="h6" gutterBottom>
            Permission Change History
          </Typography>

          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Action</TableCell>
                  <TableCell>Target</TableCell>
                  <TableCell>Details</TableCell>
                  <TableCell>Performed By</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {auditLogs.map((log: any) => (
                  <TableRow key={log.audit_id}>
                    <TableCell>
                      {new Date(log.performed_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={log.action_type}
                        size="small"
                        color={log.action_type === 'grant' ? 'success' : 'error'}
                      />
                    </TableCell>
                    <TableCell>
                      {log.target_type} #{log.target_id}
                    </TableCell>
                    <TableCell>
                      {log.permission?.permission_string || log.role?.role_name || '-'}
                    </TableCell>
                    <TableCell>
                      {log.performer?.email || 'System'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>
      </Card>

      {/* Dialogs */}
      {/* Create Role Dialog */}
      <Dialog open={createRoleDialog} onClose={() => setCreateRoleDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Role</DialogTitle>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.currentTarget);
            createRoleMutation.mutate({
              role_name: formData.get('role_name') as string,
              description: formData.get('description') as string,
            });
          }}
        >
          <DialogContent>
            <TextField
              name="role_name"
              label="Role Name"
              fullWidth
              required
              sx={{ mb: 2 }}
            />
            <TextField
              name="description"
              label="Description"
              fullWidth
              multiline
              rows={2}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateRoleDialog(false)}>Cancel</Button>
            <Button type="submit" variant="contained">
              Create Role
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Edit Permissions Dialog */}
      {selectedRole && (
        <Dialog
          open={editPermissionsDialog}
          onClose={() => setEditPermissionsDialog(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>Edit Permissions - {selectedRole.role_name}</DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Select permissions to grant to this role
            </Typography>
            
            {/* Role Restrictions Summary */}
            {roleRestrictions && (
              <Box sx={{ mb: 3, p: 2, border: '1px solid', borderColor: 'info.light', borderRadius: 1, backgroundColor: 'info.light' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Role Restrictions for {roleRestrictions.role_name}
                </Typography>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  {roleRestrictions.role_description}
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                  <Chip 
                    label={`${roleRestrictions.allowed_count} Allowed`} 
                    size="small" 
                    color="success" 
                    variant="outlined" 
                  />
                  <Chip 
                    label={`${roleRestrictions.forbidden_count} Forbidden`} 
                    size="small" 
                    color="error" 
                    variant="outlined" 
                  />
                  <Chip 
                    label={`${roleRestrictions.total_permissions} Total`} 
                    size="small" 
                    color="default" 
                    variant="outlined" 
                  />
                </Box>
              </Box>
            )}
            
            {/* Current Role Permissions */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Current Permissions ({(selectedRole.permissions?.length || selectedRole.role_permissions?.length) || 0})
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {(selectedRole.permissions || selectedRole.role_permissions?.map(rp => rp.permission) || []).map((perm) => (
                  <Chip
                    key={perm.permission_id}
                    label={`${perm.resource}:${perm.action}`}
                    size="small"
                    color="primary"
                    variant="outlined"
                  />
                )) || <Typography variant="body2" color="text.secondary">No permissions assigned</Typography>}
              </Box>
            </Box>
            
            {/* Available Permissions */}
            <Typography variant="subtitle2" gutterBottom>
              Available Permissions
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom sx={{ mb: 2 }}>
              Select permissions from the list below to assign to this role
            </Typography>
            
            {/* Legend */}
            <Box sx={{ mb: 3, p: 2, border: '1px solid', borderColor: 'grey.300', borderRadius: 1, backgroundColor: 'grey.50' }}>
              <Typography variant="subtitle2" gutterBottom>Legend:</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 16, height: 16, border: '2px solid', borderColor: 'success.main', backgroundColor: 'success.light', borderRadius: 1 }} />
                  <Typography variant="caption">Available to assign</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 16, height: 16, border: '2px solid', borderColor: 'primary.main', backgroundColor: 'primary.light', borderRadius: 1 }} />
                  <Typography variant="caption">Currently assigned</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Box sx={{ width: 16, height: 16, border: '2px solid', borderColor: 'error.main', backgroundColor: 'grey.200', borderRadius: 1 }} />
                  <Typography variant="caption">Not allowed for this role</Typography>
                </Box>
              </Box>
            </Box>
            
            {Object.entries(permissionsByResource).map(([resource, perms]) => (
              <Card key={resource} sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {resource.charAt(0).toUpperCase() + resource.slice(1)} Permissions
                    {roleRestrictions && (
                      <Typography variant="caption" sx={{ ml: 2, color: 'text.secondary' }}>
                        ({perms.filter(p => roleRestrictions.allowed_permissions.includes(`${p.resource}:${p.action}`)).length}/{perms.length} allowed)
                      </Typography>
                    )}
                  </Typography>
                  <Box
                    sx={{
                      display: 'grid',
                      gridTemplateColumns: {
                        xs: '1fr',
                        sm: 'repeat(2, 1fr)'
                      },
                      gap: 1
                    }}
                  >
                    {perms.map((perm) => {
                      const currentPermissions = selectedRole.permissions || selectedRole.role_permissions?.map(rp => rp.permission) || [];
                      const isCurrentlyAssigned = currentPermissions.some(
                        cp => cp.permission_id === perm.permission_id
                      );
                      
                      // Check if this permission is allowed for the role
                      const permissionString = `${perm.resource}:${perm.action}`;
                      const isAllowed = roleRestrictions ? 
                        roleRestrictions.allowed_permissions.includes(permissionString) : 
                        true; // Default to allowed if restrictions not loaded
                      const isForbidden = roleRestrictions ? 
                        roleRestrictions.forbidden_permissions.includes(permissionString) : 
                        false;
                      
                      // Define clear visual states
                      let borderColor, backgroundColor, textColor, cursor;
                      if (isCurrentlyAssigned) {
                        // Currently assigned - blue theme
                        borderColor = 'primary.main';
                        backgroundColor = 'primary.light';
                        textColor = 'primary.dark';
                        cursor = 'pointer';
                      } else if (isForbidden) {
                        // Forbidden - muted with red border
                        borderColor = 'error.main';
                        backgroundColor = 'grey.100';
                        textColor = 'text.disabled';
                        cursor = 'not-allowed';
                      } else if (isAllowed) {
                        // Available - green theme
                        borderColor = 'success.main';
                        backgroundColor = 'success.light';
                        textColor = 'success.dark';
                        cursor = 'pointer';
                      } else {
                        // Default state
                        borderColor = 'grey.300';
                        backgroundColor = 'transparent';
                        textColor = 'text.primary';
                        cursor = 'pointer';
                      }
                      
                      return (
                        <Box
                          key={perm.permission_id}
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            p: 1.5,
                            border: '2px solid',
                            borderColor: borderColor,
                            borderRadius: 1,
                            backgroundColor: backgroundColor,
                            cursor: cursor,
                            transition: 'all 0.2s ease-in-out',
                            '&:hover': {
                              transform: (isAllowed && !isForbidden) ? 'translateY(-1px)' : 'none',
                              boxShadow: (isAllowed && !isForbidden) ? 1 : 'none'
                            }
                          }}
                          onClick={() => {
                            if (!isAllowed || isForbidden) {
                              setSnackbar({
                                open: true,
                                message: `Permission '${permissionString}' is not allowed for role '${selectedRole.role_name}'`,
                                severity: 'warning'
                              });
                              return;
                            }
                            
                            if (isCurrentlyAssigned) {
                              // TODO: Remove permission logic
                              console.log('Remove permission:', perm.permission_id);
                            } else {
                              // TODO: Add permission logic  
                              console.log('Add permission:', perm.permission_id);
                            }
                          }}
                        >
                          <Box sx={{ flexGrow: 1 }}>
                            <Typography 
                              variant="subtitle2" 
                              sx={{ 
                                fontWeight: isCurrentlyAssigned ? 'bold' : 'medium',
                                textDecoration: isForbidden ? 'line-through' : 'none',
                                color: textColor,
                                mb: 0.5
                              }}
                            >
                              {perm.resource}:{perm.action}
                            </Typography>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                fontSize: '0.75rem',
                                fontStyle: isForbidden ? 'italic' : 'normal',
                                color: isForbidden ? 'text.disabled' : 'text.secondary'
                              }}
                            >
                              {perm.description}
                              {isForbidden && " (Not allowed for this role)"}
                            </Typography>
                          </Box>
                          <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
                            {isCurrentlyAssigned && (
                              <Chip
                                label="ASSIGNED"
                                size="small"
                                color="primary"
                                sx={{ 
                                  fontWeight: 'bold',
                                  fontSize: '0.7rem'
                                }}
                              />
                            )}
                            {isForbidden && (
                              <Chip
                                label="FORBIDDEN"
                                size="small"
                                color="error"
                                variant="outlined"
                                sx={{ 
                                  fontWeight: 'bold',
                                  fontSize: '0.7rem'
                                }}
                              />
                            )}
                            {!isForbidden && !isCurrentlyAssigned && isAllowed && (
                              <Chip
                                label="AVAILABLE"
                                size="small"
                                color="success"
                                variant="outlined"
                                sx={{ 
                                  fontWeight: 'bold',
                                  fontSize: '0.7rem'
                                }}
                              />
                            )}
                          </Box>
                        </Box>
                      );
                    })}
                  </Box>
                </CardContent>
              </Card>
            ))}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditPermissionsDialog(false)}>Cancel</Button>
            <Button 
              variant="contained"
              onClick={() => {
                // For now, just close the dialog
                // TODO: Implement save logic with selected permissions
                setEditPermissionsDialog(false);
                setSnackbar({ 
                  open: true, 
                  message: 'Permission editing interface loaded successfully!', 
                  severity: 'success' 
                });
              }}
            >
              Save Permissions
            </Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default RBACManagementPage;