import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import {
  Snackbar,
  Alert,
  AlertColor,
  Badge,
  IconButton,
  Menu,
  MenuItem,
  Typography,
  Box,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Chip,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Close as CloseIcon,
  Check as CheckIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';

// Types for notification system
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  category: 'system' | 'workflow' | 'user' | 'data' | 'security';
  priority: 'low' | 'medium' | 'high' | 'critical';
  actionable?: boolean;
  actionText?: string;
  actionUrl?: string;
  relatedEntityType?: 'cycle' | 'report' | 'phase' | 'user' | 'observation';
  relatedEntityId?: string;
  autoHide?: boolean;
  duration?: number; // milliseconds
}

interface ToastNotification {
  id: string;
  type: AlertColor;
  message: string;
  autoHide: boolean;
  duration: number;
}

interface NotificationContextValue {
  // Toast notifications
  showToast: (type: AlertColor, message: string, autoHide?: boolean, duration?: number) => void;
  hideToast: (id: string) => void;
  
  // System notifications
  notifications: Notification[];
  unreadCount: number;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  
  // Notification menu
  notificationMenuAnchor: HTMLElement | null;
  openNotificationMenu: (event: React.MouseEvent<HTMLElement>) => void;
  closeNotificationMenu: () => void;
}

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

export const useNotifications = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [toasts, setToasts] = useState<ToastNotification[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([
    // Mock notifications for demonstration
    {
      id: 'notif_001',
      type: 'warning',
      title: 'Testing Phase Overdue',
      message: 'Total Assets Calculation Logic test case is 2 days overdue. Please review and complete.',
      timestamp: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000),
      read: false,
      category: 'workflow',
      priority: 'high',
      actionable: true,
      actionText: 'View Test Case',
      actionUrl: '/phases/test-execution',
      relatedEntityType: 'phase',
      relatedEntityId: 'test_execution_001',
    },
    {
      id: 'notif_002',
      type: 'info',
      title: 'New Data Submission',
      message: 'Community Credit Union has submitted sample data for Q4 2024 reporting cycle.',
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
      read: false,
      category: 'data',
      priority: 'medium',
      actionable: true,
      actionText: 'Review Submission',
      actionUrl: '/phases/data-owner',
      relatedEntityType: 'cycle',
      relatedEntityId: 'cycle_001',
    },
    {
      id: 'notif_003',
      type: 'success',
      title: 'Observation Resolved',
      message: 'Institution Name whitespace issue has been successfully resolved and verified.',
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
      read: true,
      category: 'workflow',
      priority: 'low',
      actionable: false,
      relatedEntityType: 'observation',
      relatedEntityId: 'obs_002',
    },
    {
      id: 'notif_004',
      type: 'error',
      title: 'Critical Observation',
      message: 'New critical calculation error identified in Total Assets validation. Immediate attention required.',
      timestamp: new Date(Date.now() - 30 * 60 * 1000),
      read: false,
      category: 'workflow',
      priority: 'critical',
      actionable: true,
      actionText: 'View Observation',
      actionUrl: '/phases/observation-management',
      relatedEntityType: 'observation',
      relatedEntityId: 'obs_001',
    },
  ]);
  
  const [notificationMenuAnchor, setNotificationMenuAnchor] = useState<HTMLElement | null>(null);

  // Toast notification functions
  const showToast = useCallback((
    type: AlertColor, 
    message: string, 
    autoHide: boolean = true, 
    duration: number = 6000
  ) => {
    const id = `toast_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newToast: ToastNotification = {
      id,
      type,
      message,
      autoHide,
      duration,
    };
    
    setToasts(prev => [...prev, newToast]);
    
    if (autoHide) {
      setTimeout(() => {
        hideToast(id);
      }, duration);
    }
  }, []);

  const hideToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  // System notification functions
  const addNotification = useCallback((notificationData: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const id = `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: Notification = {
      ...notificationData,
      id,
      timestamp: new Date(),
      read: false,
    };
    
    setNotifications(prev => [newNotification, ...prev]);
    
    // Also show as toast for immediate visibility
    if (notificationData.priority === 'critical' || notificationData.priority === 'high') {
      showToast(notificationData.type, notificationData.title, true, 8000);
    }
  }, [showToast]);

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev => 
      prev.map(notif => 
        notif.id === id ? { ...notif, read: true } : notif
      )
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => 
      prev.map(notif => ({ ...notif, read: true }))
    );
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  }, []);

  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
  }, []);

  // Notification menu functions
  const openNotificationMenu = useCallback((event: React.MouseEvent<HTMLElement>) => {
    setNotificationMenuAnchor(event.currentTarget);
  }, []);

  const closeNotificationMenu = useCallback(() => {
    setNotificationMenuAnchor(null);
  }, []);

  // Calculate unread count
  const unreadCount = notifications.filter(notif => !notif.read).length;

  // Get priority color for notifications
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'primary';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  // Get category icon
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'workflow': return '🔄';
      case 'data': return '📊';
      case 'user': return '👤';
      case 'security': return '🔒';
      case 'system': return '⚙️';
      default: return '📋';
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - timestamp.getTime();
    const diffMins = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return timestamp.toLocaleDateString();
  };

  const contextValue: NotificationContextValue = {
    showToast,
    hideToast,
    notifications,
    unreadCount,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAllNotifications,
    notificationMenuAnchor,
    openNotificationMenu,
    closeNotificationMenu,
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      
      {/* Toast Notifications */}
      {toasts.map((toast, index) => (
        <Snackbar
          key={toast.id}
          open={true}
          autoHideDuration={toast.autoHide ? toast.duration : null}
          onClose={() => hideToast(toast.id)}
          anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
          sx={{ 
            mt: `${index * 70}px`,
            '& .MuiSnackbar-root': {
              position: 'relative'
            }
          }}
        >
          <Alert
            severity={toast.type}
            onClose={() => hideToast(toast.id)}
            sx={{ minWidth: '300px' }}
          >
            {toast.message}
          </Alert>
        </Snackbar>
      ))}

      {/* Notification Menu */}
      <Menu
        anchorEl={notificationMenuAnchor}
        open={Boolean(notificationMenuAnchor)}
        onClose={closeNotificationMenu}
        PaperProps={{
          sx: {
            width: 400,
            maxHeight: 500,
          }
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">
              Notifications
            </Typography>
            <Box display="flex" gap={1}>
              {unreadCount > 0 && (
                <IconButton size="small" onClick={markAllAsRead} title="Mark all as read">
                  <CheckIcon />
                </IconButton>
              )}
              <IconButton size="small" onClick={clearAllNotifications} title="Clear all">
                <ClearIcon />
              </IconButton>
            </Box>
          </Box>
          {unreadCount > 0 && (
            <Typography variant="caption" color="text.secondary">
              {unreadCount} unread notification{unreadCount > 1 ? 's' : ''}
            </Typography>
          )}
        </Box>

        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
          {notifications.length > 0 ? (
            <List disablePadding>
              {notifications.slice(0, 10).map((notification) => (
                <ListItem
                  key={notification.id}
                  sx={{
                    backgroundColor: notification.read ? 'transparent' : 'action.hover',
                    borderLeft: 4,
                    borderLeftColor: `${notification.type}.main`,
                    cursor: notification.actionable ? 'pointer' : 'default',
                  }}
                  onClick={() => {
                    if (!notification.read) markAsRead(notification.id);
                    if (notification.actionable && notification.actionUrl) {
                      window.location.href = notification.actionUrl;
                      closeNotificationMenu();
                    }
                  }}
                >
                  <Box sx={{ flex: 1 }}>
                    <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                      <span>{getCategoryIcon(notification.category)}</span>
                      <Typography variant="subtitle2" sx={{ fontWeight: notification.read ? 'normal' : 'bold' }}>
                        {notification.title}
                      </Typography>
                      <Chip
                        label={notification.priority}
                        size="small"
                        color={getPriorityColor(notification.priority) as any}
                        variant="outlined"
                        sx={{ ml: 'auto' }}
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {notification.message}
                    </Typography>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="caption" color="text.secondary">
                        {formatTimestamp(notification.timestamp)}
                      </Typography>
                      {notification.actionable && (
                        <Typography variant="caption" color="primary" sx={{ fontWeight: 'bold' }}>
                          {notification.actionText}
                        </Typography>
                      )}
                    </Box>
                  </Box>
                  <ListItemSecondaryAction>
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeNotification(notification.id);
                      }}
                    >
                      <CloseIcon fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          ) : (
            <Box sx={{ p: 3, textAlign: 'center' }}>
              <NotificationsIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
              <Typography variant="body2" color="text.secondary">
                No notifications
              </Typography>
            </Box>
          )}
        </Box>

        {notifications.length > 10 && (
          <Box sx={{ p: 1, borderTop: 1, borderColor: 'divider', textAlign: 'center' }}>
            <Typography variant="caption" color="primary" sx={{ cursor: 'pointer' }}>
              View all notifications
            </Typography>
          </Box>
        )}
      </Menu>
    </NotificationContext.Provider>
  );
};

// Export notification bell component for use in header
// Export simplified hook for showing toast notifications
export const useNotification = () => {
  const { showToast } = useNotifications();
  
  return {
    showSuccess: (message: string) => showToast('success', message),
    showError: (message: string) => showToast('error', message),
    showWarning: (message: string) => showToast('warning', message),
    showInfo: (message: string) => showToast('info', message),
  };
};

// Export notification bell component for use in header
export const NotificationBell: React.FC = () => {
  const { unreadCount, openNotificationMenu } = useNotifications();

  return (
    <IconButton
      color="inherit"
      onClick={openNotificationMenu}
      sx={{ mx: 1 }}
    >
      <Badge badgeContent={unreadCount} color="error" max={99}>
        <NotificationsIcon />
      </Badge>
    </IconButton>
  );
}; 