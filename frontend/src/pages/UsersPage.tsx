import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Tooltip,
  Menu,
  Avatar,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
  Person as PersonIcon,
  AdminPanelSettings as AdminIcon,
  Engineering as TechIcon,
  Business as BusinessIcon,
  LockReset as ResetPasswordIcon,
  PersonOff as StopImpersonateIcon,
  AccountCircle as ImpersonateIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersApi, CreateUserRequest, UpdateUserRequest } from '../api/users';
import { User, UserRole } from '../types/api';
import { useAuth } from '../contexts/AuthContext';
import apiClient from '../api/client';
import { usePermissions } from '../contexts/PermissionContext';
import { PermissionGate } from '../components/auth/PermissionGate';

const UsersPage: React.FC = () => {
  const { user: currentUser, impersonateUser, isImpersonating } = useAuth();
  const { hasPermission } = usePermissions();
  const queryClient = useQueryClient();
  
  // State for pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // State for dialogs
  const [openCreateDialog, setOpenCreateDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  
  // State for forms
  const [formData, setFormData] = useState<CreateUserRequest>({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    role: UserRole.TESTER,
    lob_id: undefined,
  });
  
  // State for menu
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuUser, setMenuUser] = useState<User | null>(null);

  // Query for users
  const {
    data: usersData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['users', page + 1, rowsPerPage],
    queryFn: () => usersApi.getAll(page + 1, rowsPerPage),
  });

  // Query for LOBs
  const { data: lobsData } = useQuery({
    queryKey: ['lobs'],
    queryFn: async () => {
      const response = await apiClient.get('/lobs/');
      return response.data;
    },
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setOpenCreateDialog(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateUserRequest }) => 
      usersApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setOpenEditDialog(false);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: usersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      handleCloseMenu();
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) => 
      usersApi.toggleStatus(id, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
  });

  const resetPasswordMutation = useMutation({
    mutationFn: usersApi.resetPassword,
    onSuccess: () => {
      alert('Password reset email sent successfully');
      handleCloseMenu();
    },
  });

  const resetForm = () => {
    setFormData({
      username: '',
      email: '',
      first_name: '',
      last_name: '',
      password: '',
      role: UserRole.TESTER,
      lob_id: undefined,
    });
    setSelectedUser(null);
  };

  const handleCreate = () => {
    setOpenCreateDialog(true);
    resetForm();
  };

  const handleEdit = (user: User) => {
    setSelectedUser(user);
    setFormData({
      username: user.username,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      password: '', // Don't pre-fill password for editing
      role: user.role,
      lob_id: user.lob_id,
    });
    setOpenEditDialog(true);
    handleCloseMenu();
  };

  const handleDelete = (user: User) => {
    if (window.confirm(`Are you sure you want to delete user "${user.username}"?`)) {
      deleteMutation.mutate(user.user_id);
    }
  };

  const handleToggleStatus = (user: User) => {
    toggleStatusMutation.mutate({
      id: user.user_id,
      isActive: !user.is_active
    });
    handleCloseMenu();
  };

  const handleResetPassword = (user: User) => {
    if (window.confirm(`Reset password for "${user.username}"?`)) {
      resetPasswordMutation.mutate(user.user_id);
    }
  };

  const handleImpersonate = async (user: User) => {
    try {
      await impersonateUser(user.user_id);
      handleCloseMenu();
    } catch (error) {
      console.error('Failed to impersonate user:', error);
      alert('Failed to impersonate user. Please try again.');
    }
  };

  const handleSubmitCreate = () => {
    createMutation.mutate(formData);
  };

  const handleSubmitEdit = () => {
    if (selectedUser) {
      const updateData: UpdateUserRequest = {
        username: formData.username,
        email: formData.email,
        first_name: formData.first_name,
        last_name: formData.last_name,
        role: formData.role,
        lob_id: formData.lob_id,
      };
      
      // Only include password if it's provided
      if (formData.password) {
        // Note: This would require a different endpoint for password changes
        // For now, we'll exclude password from user updates
      }

      updateMutation.mutate({
        id: selectedUser.user_id,
        data: updateData
      });
    }
  };

  const handleMenu = (event: React.MouseEvent<HTMLElement>, user: User) => {
    setAnchorEl(event.currentTarget);
    setMenuUser(user);
  };

  const handleCloseMenu = () => {
    setAnchorEl(null);
    setMenuUser(null);
  };

  const getRoleIcon = (role: UserRole) => {
    switch (role) {
      case UserRole.ADMIN:
        return <AdminIcon fontSize="small" color="secondary" />;
      case UserRole.TEST_EXECUTIVE:
        return <AdminIcon fontSize="small" color="error" />;
      case UserRole.REPORT_OWNER:
        return <TechIcon fontSize="small" color="primary" />;
      case UserRole.TESTER:
        return <BusinessIcon fontSize="small" color="success" />;
      case UserRole.DATA_EXECUTIVE:
        return <AdminIcon fontSize="small" color="warning" />;
      case UserRole.DATA_OWNER:
        return <TechIcon fontSize="small" color="info" />;
      case UserRole.REPORT_EXECUTIVE:
        return <AdminIcon fontSize="small" color="secondary" />;
      default:
        return <PersonIcon fontSize="small" />;
    }
  };

  const getRoleColor = (role: UserRole) => {
    switch (role) {
      case UserRole.ADMIN:
        return 'secondary';
      case UserRole.TEST_EXECUTIVE:
        return 'error';
      case UserRole.REPORT_OWNER:
        return 'primary';
      case UserRole.TESTER:
        return 'success';
      case UserRole.DATA_EXECUTIVE:
        return 'warning';
      case UserRole.DATA_OWNER:
        return 'info';
      case UserRole.REPORT_EXECUTIVE:
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getInitials = (firstName: string, lastName: string) => {
    return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
  };

  const isCurrentUser = (user: User) => {
    return currentUser?.user_id === user.user_id;
  };

  const canManageUser = (user: User) => {
    return (currentUser?.role === UserRole.ADMIN || 
           (currentUser?.role === UserRole.TEST_EXECUTIVE && !isCurrentUser(user)));
  };

  const canCreateUser = () => {
    return currentUser?.role === UserRole.ADMIN || currentUser?.role === UserRole.TEST_EXECUTIVE;
  };

  const getLOBName = (lobId: number | undefined) => {
    if (!lobId || !lobsData?.lobs) return 'Not assigned';
    const lob = lobsData.lobs.find((l: any) => l.lob_id === lobId);
    return lob?.lob_name || 'Unknown LOB';
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        Failed to load users. Please try again.
      </Alert>
    );
  }

  const users = usersData?.items || [];
  const totalCount = usersData?.total || 0;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Users</Typography>
        <PermissionGate resource="users" action="create">
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreate}
          >
            Create User
          </Button>
        </PermissionGate>
      </Box>

      {/* Data Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>User</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>LOB</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Login</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.user_id} hover>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                        {getInitials(user.first_name, user.last_name)}
                      </Avatar>
                      <Box>
                        <Typography variant="subtitle2">
                          {user.first_name} {user.last_name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          @{user.username}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {user.email}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      {getRoleIcon(user.role)}
                      <Chip
                        label={user.role.replace('_', ' ').toUpperCase()}
                        color={getRoleColor(user.role)}
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {getLOBName(user.lob_id)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={user.is_active}
                          onChange={() => handleToggleStatus(user)}
                          disabled={!canManageUser(user)}
                          size="small"
                        />
                      }
                      label={user.is_active ? 'Active' : 'Inactive'}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      Never
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {(hasPermission('users', 'update') || hasPermission('users', 'delete')) && (
                      <Tooltip title="More actions">
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenu(e, user)}
                        >
                          <MoreVertIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                  </TableCell>
                </TableRow>
              ))}
              {users.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography variant="body2" color="text.secondary">
                      No users found.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
        
        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Paper>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        {menuUser && (
          [
            hasPermission('users', 'update') && (
              <MenuItem key="edit" onClick={() => menuUser && handleEdit(menuUser)}>
                <EditIcon fontSize="small" sx={{ mr: 1 }} />
                Edit
              </MenuItem>
            ),
            hasPermission('users', 'update') && (
              <MenuItem key="reset" onClick={() => menuUser && handleResetPassword(menuUser)}>
                <ResetPasswordIcon fontSize="small" sx={{ mr: 1 }} />
                Reset Password
              </MenuItem>
            ),
            hasPermission('users', 'delete') && (
              <MenuItem key="delete" onClick={() => menuUser && handleDelete(menuUser)}>
                <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
                Delete
              </MenuItem>
            ),
            hasPermission('system', 'admin') && (
              <MenuItem key="impersonate" onClick={() => menuUser && handleImpersonate(menuUser)}>
                <ImpersonateIcon fontSize="small" sx={{ mr: 1 }} />
                Impersonate User
              </MenuItem>
            )
          ].filter(Boolean)
        )}
        {menuUser && !canManageUser(menuUser) && (
          <MenuItem disabled>
            <Typography variant="body2" color="text.secondary">
              No actions available
            </Typography>
          </MenuItem>
        )}
      </Menu>

      {/* Create Dialog */}
      <Dialog open={openCreateDialog} onClose={() => setOpenCreateDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create User</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <TextField
              label="Username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              fullWidth
              required
            />
            <Box display="flex" gap={2}>
              <TextField
                label="First Name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                fullWidth
                required
              />
              <TextField
                label="Last Name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                fullWidth
                required
              />
            </Box>
            <TextField
              label="Password"
              type="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              fullWidth
              required
            />
            <FormControl fullWidth required>
              <InputLabel>Role</InputLabel>
              <Select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
                label="Role"
              >
                {currentUser?.role === UserRole.ADMIN && (
                  <MenuItem value={UserRole.ADMIN}>Admin</MenuItem>
                )}
                <MenuItem value={UserRole.TESTER}>Tester</MenuItem>
                <MenuItem value={UserRole.REPORT_OWNER}>Report Owner</MenuItem>
                <MenuItem value={UserRole.TEST_EXECUTIVE}>Test Executive</MenuItem>
                <MenuItem value={UserRole.DATA_EXECUTIVE}>Data Executive</MenuItem>
                <MenuItem value={UserRole.DATA_OWNER}>Data Owner</MenuItem>
                <MenuItem value={UserRole.REPORT_EXECUTIVE}>Report Executive</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Line of Business</InputLabel>
              <Select
                value={formData.lob_id || ''}
                onChange={(e) => setFormData({ ...formData, lob_id: e.target.value ? Number(e.target.value) : undefined })}
                label="Line of Business"
              >
                <MenuItem value="">
                  <em>Not assigned</em>
                </MenuItem>
                {lobsData?.lobs?.map((lob: any) => (
                  <MenuItem key={lob.lob_id} value={lob.lob_id}>
                    {lob.lob_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitCreate}
            variant="contained"
            disabled={!formData.username || !formData.email || !formData.password || createMutation.isPending}
          >
            {createMutation.isPending ? <CircularProgress size={20} /> : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit User</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} pt={1}>
            <TextField
              label="Username"
              value={formData.username}
              onChange={(e) => setFormData({ ...formData, username: e.target.value })}
              fullWidth
              required
            />
            <TextField
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              fullWidth
              required
            />
            <Box display="flex" gap={2}>
              <TextField
                label="First Name"
                value={formData.first_name}
                onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                fullWidth
                required
              />
              <TextField
                label="Last Name"
                value={formData.last_name}
                onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                fullWidth
                required
              />
            </Box>
            <FormControl fullWidth required>
              <InputLabel>Role</InputLabel>
              <Select
                value={formData.role}
                onChange={(e) => setFormData({ ...formData, role: e.target.value as UserRole })}
                label="Role"
              >
                {currentUser?.role === UserRole.ADMIN && (
                  <MenuItem value={UserRole.ADMIN}>Admin</MenuItem>
                )}
                <MenuItem value={UserRole.TESTER}>Tester</MenuItem>
                <MenuItem value={UserRole.REPORT_OWNER}>Report Owner</MenuItem>
                <MenuItem value={UserRole.TEST_EXECUTIVE}>Test Executive</MenuItem>
                <MenuItem value={UserRole.DATA_EXECUTIVE}>Data Executive</MenuItem>
                <MenuItem value={UserRole.DATA_OWNER}>Data Owner</MenuItem>
                <MenuItem value={UserRole.REPORT_EXECUTIVE}>Report Executive</MenuItem>
              </Select>
            </FormControl>
            <FormControl fullWidth>
              <InputLabel>Line of Business</InputLabel>
              <Select
                value={formData.lob_id || ''}
                onChange={(e) => setFormData({ ...formData, lob_id: e.target.value ? Number(e.target.value) : undefined })}
                label="Line of Business"
              >
                <MenuItem value="">
                  <em>Not assigned</em>
                </MenuItem>
                {lobsData?.lobs?.map((lob: any) => (
                  <MenuItem key={lob.lob_id} value={lob.lob_id}>
                    {lob.lob_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditDialog(false)}>Cancel</Button>
          <Button
            onClick={handleSubmitEdit}
            variant="contained"
            disabled={!formData.username || !formData.email || updateMutation.isPending}
          >
            {updateMutation.isPending ? <CircularProgress size={20} /> : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UsersPage; 