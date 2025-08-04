import {
  Group,
  Business as BusinessIcon,
  Assignment as AssignmentIcon,
  DataObject as DataObjectIcon,
  Schedule as ScheduleIcon,
  Settings,
} from '@mui/icons-material';

const adminMenuItems = [
  { text: 'User Management', icon: <Group />, path: '/admin/users' },
  { text: 'LOB Management', icon: <BusinessIcon />, path: '/admin/lobs' },
  { text: 'Report Management', icon: <AssignmentIcon />, path: '/admin/reports' },
  { text: 'Data Sources', icon: <DataObjectIcon />, path: '/admin/data-sources' },
  { text: 'SLA Configuration', icon: <ScheduleIcon />, path: '/admin/sla-configuration' },
  { text: 'System Settings', icon: <Settings />, path: '/admin/settings' },
]; 