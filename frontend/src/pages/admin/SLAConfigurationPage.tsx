import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Alert,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  Snackbar,
  Tooltip
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Warning as WarningIcon,
  Schedule as ScheduleIcon,
  Notifications as NotificationsIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  History as HistoryIcon,
  Timeline as TimelineIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../api/client';

interface SLAConfiguration {
  sla_id: number;
  transition_name: string;
  from_role: string;
  to_role: string;
  sla_hours: number;
  is_active: boolean;
  escalation_enabled: boolean;
  escalation_hours: number;
  description: string;
  created_at: string;
  updated_at: string;
}

interface EscalationRule {
  rule_id: number;
  sla_id: number;
  escalation_level: number;
  escalation_hours: number;
  escalation_to_role: string;
  notification_template: string;
  is_active: boolean;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function CustomTabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`sla-tabpanel-${index}`}
      aria-labelledby={`sla-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SLAConfigurationPage: React.FC = () => {
  const { user } = useAuth();
  const [tabValue, setTabValue] = useState(0);
  const [slaConfigs, setSlaConfigs] = useState<SLAConfiguration[]>([]);
  const [escalationRules, setEscalationRules] = useState<EscalationRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Dialog states
  const [openSLADialog, setOpenSLADialog] = useState(false);
  const [openEscalationDialog, setOpenEscalationDialog] = useState(false);
  const [editingSLA, setEditingSLA] = useState<SLAConfiguration | null>(null);
  const [editingEscalation, setEditingEscalation] = useState<EscalationRule | null>(null);

  // Form states
  const [slaForm, setSlaForm] = useState({
    transition_name: '',
    from_role: '',
    to_role: '',
    sla_hours: 24,
    escalation_enabled: true,
    escalation_hours: 48,
    description: '',
    is_active: true
  });

  const [escalationForm, setEscalationForm] = useState({
    sla_id: 0,
    escalation_level: 1,
    escalation_hours: 24,
    escalation_to_role: '',
    notification_template: '',
    is_active: true
  });

  const roles = [
    'Tester',
    'Test Executive',
    'Report Owner',
    'Report Owner Executive',
    'Data Owner',
    'Data Executive'
  ];

  const transitionTypes = [
    'Planning Phase Completion',
    'Scoping Submission',
    'Scoping Approval',
    'Data Owner Assignment',
    'Sample Selection Submission',
    'Sample Selection Approval',
    'Information Request Response',
    'Testing Completion',
    'Observation Submission',
    'Observation Approval'
  ];

  useEffect(() => {
    loadSLAConfigurations();
    loadEscalationRules();
  }, []);

  const loadSLAConfigurations = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/admin-sla/configurations');
      setSlaConfigs(response.data);
    } catch (err: any) {
      setError('Failed to load SLA configurations');
      console.error('Error loading SLA configs:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadEscalationRules = async () => {
    try {
      const response = await apiClient.get('/admin-sla/escalation-rules');
      setEscalationRules(response.data);
    } catch (err: any) {
      setError('Failed to load escalation rules');
      console.error('Error loading escalation rules:', err);
    }
  };

  const handleSaveSLA = async () => {
    try {
      if (editingSLA) {
        await apiClient.put(`/admin-sla/configurations/${editingSLA.sla_id}`, slaForm);
        setSuccess('SLA configuration updated successfully');
      } else {
        await apiClient.post('/admin-sla/configurations', slaForm);
        setSuccess('SLA configuration created successfully');
      }
      
      setOpenSLADialog(false);
      setEditingSLA(null);
      resetSLAForm();
      loadSLAConfigurations();
    } catch (err: any) {
      setError('Failed to save SLA configuration');
      console.error('Error saving SLA:', err);
    }
  };

  const handleDeleteSLA = async (slaId: number) => {
    if (!window.confirm('Are you sure you want to delete this SLA configuration?')) {
      return;
    }

    try {
      await apiClient.delete(`/admin-sla/configurations/${slaId}`);
      setSuccess('SLA configuration deleted successfully');
      loadSLAConfigurations();
    } catch (err: any) {
      setError('Failed to delete SLA configuration');
      console.error('Error deleting SLA:', err);
    }
  };

  const handleEditSLA = (sla: SLAConfiguration) => {
    setEditingSLA(sla);
    setSlaForm({
      transition_name: sla.transition_name,
      from_role: sla.from_role,
      to_role: sla.to_role,
      sla_hours: sla.sla_hours,
      escalation_enabled: sla.escalation_enabled,
      escalation_hours: sla.escalation_hours,
      description: sla.description,
      is_active: sla.is_active
    });
    setOpenSLADialog(true);
  };

  const handleSaveEscalation = async () => {
    try {
      if (editingEscalation) {
        await apiClient.put(`/admin-sla/escalation-rules/${editingEscalation.rule_id}`, escalationForm);
        setSuccess('Escalation rule updated successfully');
      } else {
        await apiClient.post('/admin-sla/escalation-rules', escalationForm);
        setSuccess('Escalation rule created successfully');
      }
      
      setOpenEscalationDialog(false);
      setEditingEscalation(null);
      resetEscalationForm();
      loadEscalationRules();
    } catch (err: any) {
      setError('Failed to save escalation rule');
      console.error('Error saving escalation rule:', err);
    }
  };

  const resetSLAForm = () => {
    setSlaForm({
      transition_name: '',
      from_role: '',
      to_role: '',
      sla_hours: 24,
      escalation_enabled: true,
      escalation_hours: 48,
      description: '',
      is_active: true
    });
  };

  const resetEscalationForm = () => {
    setEscalationForm({
      sla_id: 0,
      escalation_level: 1,
      escalation_hours: 24,
      escalation_to_role: '',
      notification_template: '',
      is_active: true
    });
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const formatDuration = (hours: number) => {
    if (hours < 24) {
      return `${hours} hours`;
    } else {
      const days = Math.floor(hours / 24);
      const remainingHours = hours % 24;
      return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days} days`;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Typography>Loading SLA configurations...</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <SettingsIcon sx={{ mr: 2, verticalAlign: 'middle' }} />
        SLA Configuration Management
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="SLA Configurations" icon={<TimelineIcon />} />
          <Tab label="Escalation Rules" icon={<NotificationsIcon />} />
          <Tab label="System Settings" icon={<SettingsIcon />} />
        </Tabs>
      </Box>

      {/* SLA Configurations Tab */}
      <CustomTabPanel value={tabValue} index={0}>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">SLA Configurations</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              resetSLAForm();
              setEditingSLA(null);
              setOpenSLADialog(true);
            }}
          >
            Add SLA Configuration
          </Button>
        </Box>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Transition</TableCell>
                <TableCell>From Role</TableCell>
                <TableCell>To Role</TableCell>
                <TableCell>SLA Duration</TableCell>
                <TableCell>Escalation</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {slaConfigs.map((sla) => (
                <TableRow key={sla.sla_id}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {sla.transition_name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {sla.description}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={sla.from_role} size="small" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <Chip label={sla.to_role} size="small" color="primary" />
                  </TableCell>
                  <TableCell>{formatDuration(sla.sla_hours)}</TableCell>
                  <TableCell>
                    {sla.escalation_enabled ? (
                      <Chip 
                        label={`After ${formatDuration(sla.escalation_hours)}`} 
                        size="small" 
                        color="warning" 
                      />
                    ) : (
                      <Chip label="Disabled" size="small" variant="outlined" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={sla.is_active ? 'Active' : 'Inactive'} 
                      size="small" 
                      color={sla.is_active ? 'success' : 'default'} 
                    />
                  </TableCell>
                  <TableCell>
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => handleEditSLA(sla)}>
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton size="small" onClick={() => handleDeleteSLA(sla.sla_id)}>
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CustomTabPanel>

      {/* Escalation Rules Tab */}
      <CustomTabPanel value={tabValue} index={1}>
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Escalation Rules</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              resetEscalationForm();
              setEditingEscalation(null);
              setOpenEscalationDialog(true);
            }}
          >
            Add Escalation Rule
          </Button>
        </Box>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>SLA Configuration</TableCell>
                <TableCell>Level</TableCell>
                <TableCell>Escalation Time</TableCell>
                <TableCell>Escalate To</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {escalationRules.map((rule) => {
                const slaConfig = slaConfigs.find(sla => sla.sla_id === rule.sla_id);
                return (
                  <TableRow key={rule.rule_id}>
                    <TableCell>
                      <Typography variant="body2">
                        {slaConfig?.transition_name || 'Unknown'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={`Level ${rule.escalation_level}`} size="small" />
                    </TableCell>
                    <TableCell>{formatDuration(rule.escalation_hours)}</TableCell>
                    <TableCell>
                      <Chip label={rule.escalation_to_role} size="small" color="secondary" />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={rule.is_active ? 'Active' : 'Inactive'} 
                        size="small" 
                        color={rule.is_active ? 'success' : 'default'} 
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Edit">
                        <IconButton size="small">
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton size="small">
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </CustomTabPanel>

      {/* System Settings Tab */}
      <CustomTabPanel value={tabValue} index={2}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Global SLA Settings
              </Typography>
              <Box sx={{ mt: 2 }}>
                <TextField
                  fullWidth
                  label="Default SLA Hours"
                  type="number"
                  defaultValue={24}
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  label="Default Escalation Hours"
                  type="number"
                  defaultValue={48}
                  sx={{ mb: 2 }}
                />
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Enable automatic escalations"
                />
              </Box>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Notification Settings
              </Typography>
              <Box sx={{ mt: 2 }}>
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Email notifications"
                  sx={{ display: 'block', mb: 1 }}
                />
                <FormControlLabel
                  control={<Switch defaultChecked />}
                  label="Daily digest emails"
                  sx={{ display: 'block', mb: 1 }}
                />
                <FormControlLabel
                  control={<Switch />}
                  label="SMS notifications (critical only)"
                  sx={{ display: 'block', mb: 1 }}
                />
                <TextField
                  fullWidth
                  label="Notification frequency (hours)"
                  type="number"
                  defaultValue={24}
                  sx={{ mt: 2 }}
                />
              </Box>
            </CardContent>
          </Card>
        </Box>
      </CustomTabPanel>

      {/* SLA Configuration Dialog */}
      <Dialog open={openSLADialog} onClose={() => setOpenSLADialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingSLA ? 'Edit SLA Configuration' : 'Add SLA Configuration'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' }, gap: 2, mt: 1 }}>
            <Box sx={{ gridColumn: { xs: '1', sm: '1 / -1' } }}>
              <FormControl fullWidth>
                <InputLabel>Transition Type</InputLabel>
                <Select
                  value={slaForm.transition_name}
                  onChange={(e) => setSlaForm({ ...slaForm, transition_name: e.target.value })}
                >
                  {transitionTypes.map((type) => (
                    <MenuItem key={type} value={type}>{type}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <Box>
              <FormControl fullWidth>
                <InputLabel>From Role</InputLabel>
                <Select
                  value={slaForm.from_role}
                  onChange={(e) => setSlaForm({ ...slaForm, from_role: e.target.value })}
                >
                  {roles.map((role) => (
                    <MenuItem key={role} value={role}>{role}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <Box>
              <FormControl fullWidth>
                <InputLabel>To Role</InputLabel>
                <Select
                  value={slaForm.to_role}
                  onChange={(e) => setSlaForm({ ...slaForm, to_role: e.target.value })}
                >
                  {roles.map((role) => (
                    <MenuItem key={role} value={role}>{role}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
            
            <Box>
              <TextField
                fullWidth
                label="SLA Hours"
                type="number"
                value={slaForm.sla_hours}
                onChange={(e) => setSlaForm({ ...slaForm, sla_hours: parseInt(e.target.value) })}
              />
            </Box>
            
            <Box>
              <TextField
                fullWidth
                label="Escalation Hours"
                type="number"
                value={slaForm.escalation_hours}
                onChange={(e) => setSlaForm({ ...slaForm, escalation_hours: parseInt(e.target.value) })}
                disabled={!slaForm.escalation_enabled}
              />
            </Box>
            
            <Box sx={{ gridColumn: { xs: '1', sm: '1 / -1' } }}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={3}
                value={slaForm.description}
                onChange={(e) => setSlaForm({ ...slaForm, description: e.target.value })}
              />
            </Box>
            
            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={slaForm.escalation_enabled}
                    onChange={(e) => setSlaForm({ ...slaForm, escalation_enabled: e.target.checked })}
                  />
                }
                label="Enable Escalation"
              />
            </Box>
            
            <Box>
              <FormControlLabel
                control={
                  <Switch
                    checked={slaForm.is_active}
                    onChange={(e) => setSlaForm({ ...slaForm, is_active: e.target.checked })}
                  />
                }
                label="Active"
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenSLADialog(false)} startIcon={<CancelIcon />}>
            Cancel
          </Button>
          <Button onClick={handleSaveSLA} variant="contained" startIcon={<SaveIcon />}>
            Save
          </Button>
        </DialogActions>
      </Dialog>

      {/* Success/Error Snackbars */}
      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
      >
        <Alert onClose={() => setSuccess(null)} severity="success">
          {success}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert onClose={() => setError(null)} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default SLAConfigurationPage; 