import React, { useState, useEffect } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Box,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  TextField,
  MenuItem,
  Button,
  CircularProgress,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Cancel as CancelIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  HourglassEmpty as PendingIcon,
  PlayCircle as RunningIcon,
  Info as InfoIcon,
  Pause as PauseIcon,
  PlayArrow as ResumeIcon,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import apiClient from '../api/client';
import { formatDistanceToNow } from 'date-fns';

interface BackgroundJob {
  job_id: string;
  job_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'paused' | 'pausing';
  progress_percentage: number;
  current_step: string;
  message: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  metadata?: Record<string, any>;
  error?: string;
  result?: any;
}

const BackgroundJobsPage: React.FC = () => {
  const { user } = useAuth();
  const { showError, showSuccess } = useNotification();
  const [jobs, setJobs] = useState<BackgroundJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'active' | 'completed'>('all');
  const [jobTypeFilter, setJobTypeFilter] = useState<string>('all');
  const [refreshInterval, setRefreshInterval] = useState<NodeJS.Timeout | null>(null);

  // Fetch jobs
  const fetchJobs = async () => {
    try {
      const response = await apiClient.get('/jobs/active');
      const activeJobs = response.data.active_jobs || [];
      
      // Debug: Check for timestamp issues
      activeJobs.forEach((job: BackgroundJob) => {
        if (job.started_at) {
          const startTime = new Date(job.started_at);
          const now = new Date();
          const diffMs = now.getTime() - startTime.getTime();
          
          console.log('Job timestamp debug:', {
            job_id: job.job_id,
            job_type: job.job_type,
            started_at_raw: job.started_at,
            started_at_parsed: startTime.toISOString(),
            now: now.toISOString(),
            diff_ms: diffMs,
            diff_minutes: diffMs / (1000 * 60),
            is_future: startTime > now
          });
        }
      });
      
      // Sort by created_at descending
      const sortedJobs = activeJobs.sort((a: BackgroundJob, b: BackgroundJob) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      
      setJobs(sortedJobs);
    } catch (error: any) {
      console.error('Error fetching jobs:', error);
      showError('Failed to fetch background jobs');
    } finally {
      setLoading(false);
    }
  };

  // Cancel a job
  const handleCancelJob = async (jobId: string) => {
    try {
      await apiClient.post(`/jobs/${jobId}/cancel`);
      showSuccess('Job cancelled successfully');
      fetchJobs();
    } catch (error: any) {
      showError(`Failed to cancel job: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Pause a job
  const handlePauseJob = async (jobId: string) => {
    try {
      await apiClient.post(`/jobs/${jobId}/pause`);
      showSuccess('Job pause requested');
      fetchJobs();
    } catch (error: any) {
      showError(`Failed to pause job: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Resume a job
  const handleResumeJob = async (jobId: string) => {
    try {
      await apiClient.post(`/jobs/${jobId}/resume`);
      showSuccess('Job resume requested');
      fetchJobs();
    } catch (error: any) {
      showError(`Failed to resume job: ${error.response?.data?.detail || error.message}`);
    }
  };

  // Get job type display name
  const getJobTypeDisplay = (jobType: string): string => {
    const typeMap: Record<string, string> = {
      scoping_recommendations: 'LLM Recommendations',
      profiling_execution: 'Data Profiling',
      sample_generation: 'Sample Generation',
      document_analysis: 'Document Analysis',
      pde_classification: 'PDE Classification',
      data_quality_check: 'Data Quality Check',
      unknown: 'Unknown Job',
    };
    return typeMap[jobType] || jobType;
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <PendingIcon color="action" />;
      case 'running':
        return <RunningIcon color="primary" />;
      case 'completed':
        return <CheckCircleIcon color="success" />;
      case 'failed':
        return <ErrorIcon color="error" />;
      case 'cancelled':
        return <CancelIcon color="disabled" />;
      case 'paused':
      case 'pausing':
        return <PauseIcon color="warning" />;
      default:
        return <InfoIcon color="action" />;
    }
  };

  // Get status color
  const getStatusColor = (status: string): "default" | "primary" | "success" | "error" | "warning" => {
    switch (status) {
      case 'pending':
        return 'default';
      case 'running':
        return 'primary';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
      case 'paused':
      case 'pausing':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Filter jobs
  const getFilteredJobs = () => {
    let filtered = jobs;
    
    // Status filter
    if (filter === 'active') {
      filtered = filtered.filter(job => ['pending', 'running', 'paused', 'pausing'].includes(job.status));
    } else if (filter === 'completed') {
      filtered = filtered.filter(job => ['completed', 'failed', 'cancelled'].includes(job.status));
    }
    
    // Job type filter
    if (jobTypeFilter !== 'all') {
      filtered = filtered.filter(job => job.job_type === jobTypeFilter);
    }
    
    return filtered;
  };

  // Get unique job types
  const getJobTypes = () => {
    const types = new Set(jobs.map(job => job.job_type));
    return Array.from(types);
  };

  // Calculate runtime
  const getRuntime = (job: BackgroundJob): string => {
    if (!job.started_at) return '-';
    
    try {
      // Parse timestamps, assuming they might be in UTC without timezone info
      let startTime: Date;
      if (job.started_at.includes('Z') || job.started_at.includes('+')) {
        startTime = new Date(job.started_at);
      } else {
        // Assume UTC if no timezone specified
        startTime = new Date(job.started_at + 'Z');
      }
      
      const endTime = job.completed_at 
        ? (job.completed_at.includes('Z') || job.completed_at.includes('+') 
          ? new Date(job.completed_at) 
          : new Date(job.completed_at + 'Z'))
        : new Date();
        
      const diffMs = endTime.getTime() - startTime.getTime();
      
      // If negative or unreasonably large, show elapsed time from start
      if (diffMs < 0 || diffMs > 24 * 60 * 60 * 1000) { // More than 24 hours
        const elapsedMs = new Date().getTime() - startTime.getTime();
        if (elapsedMs < 0) {
          return 'Starting...';
        }
        const seconds = Math.floor(elapsedMs / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) {
          return `${hours}h ${minutes % 60}m`;
        } else if (minutes > 0) {
          return `${minutes}m ${seconds % 60}s`;
        } else {
          return `${seconds}s`;
        }
      }
      
      const seconds = Math.floor(diffMs / 1000);
      const minutes = Math.floor(seconds / 60);
      const hours = Math.floor(minutes / 60);
      
      if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
      } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
      } else {
        return `${seconds}s`;
      }
    } catch (error) {
      console.error('Error calculating runtime:', error, job);
      return '-';
    }
  };

  useEffect(() => {
    fetchJobs();
    
    // Set up auto-refresh every 2 seconds for active jobs
    const interval = setInterval(() => {
      const hasActiveJobs = jobs.some(job => ['pending', 'running', 'paused', 'pausing'].includes(job.status));
      if (hasActiveJobs) {
        fetchJobs();
      }
    }, 2000);
    
    setRefreshInterval(interval);
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, []);

  const filteredJobs = getFilteredJobs();
  const activeJobsCount = jobs.filter(job => ['pending', 'running', 'paused', 'pausing'].includes(job.status)).length;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Background Jobs Monitor
      </Typography>
      
      {/* Summary Cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2, mb: 3 }}>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Total Jobs
            </Typography>
            <Typography variant="h4">
              {jobs.length}
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Active Jobs
            </Typography>
            <Typography variant="h4" color="primary">
              {activeJobsCount}
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Completed
            </Typography>
            <Typography variant="h4" color="success.main">
              {jobs.filter(job => job.status === 'completed').length}
            </Typography>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <Typography color="textSecondary" gutterBottom>
              Failed
            </Typography>
            <Typography variant="h4" color="error.main">
              {jobs.filter(job => job.status === 'failed').length}
            </Typography>
          </CardContent>
        </Card>
      </Box>
      
      {/* Filters */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2, alignItems: 'center' }}>
        <TextField
          select
          label="Status Filter"
          value={filter}
          onChange={(e) => setFilter(e.target.value as any)}
          size="small"
          sx={{ minWidth: 150 }}
        >
          <MenuItem value="all">All Jobs</MenuItem>
          <MenuItem value="active">Active Only</MenuItem>
          <MenuItem value="completed">Completed Only</MenuItem>
        </TextField>
        
        <TextField
          select
          label="Job Type"
          value={jobTypeFilter}
          onChange={(e) => setJobTypeFilter(e.target.value)}
          size="small"
          sx={{ minWidth: 200 }}
        >
          <MenuItem value="all">All Types</MenuItem>
          {getJobTypes().map(type => (
            <MenuItem key={type} value={type}>
              {getJobTypeDisplay(type)}
            </MenuItem>
          ))}
        </TextField>
        
        <Box sx={{ flexGrow: 1 }} />
        
        <Button
          startIcon={<RefreshIcon />}
          onClick={fetchJobs}
          variant="outlined"
          size="small"
        >
          Refresh
        </Button>
      </Box>
      
      {/* Jobs Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Status</TableCell>
              <TableCell>Job Type</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Current Step</TableCell>
              <TableCell>Runtime</TableCell>
              <TableCell>Started</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : filteredJobs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="textSecondary">No jobs found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredJobs.map((job) => (
                <TableRow key={job.job_id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getStatusIcon(job.status)}
                      <Chip
                        label={job.status.toUpperCase()}
                        color={getStatusColor(job.status)}
                        size="small"
                      />
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {getJobTypeDisplay(job.job_type)}
                    </Typography>
                    {job.metadata && (
                      <Typography variant="caption" color="textSecondary">
                        Cycle {job.metadata.cycle_id}, Report {job.metadata.report_id}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Box sx={{ flexGrow: 1, minWidth: 100 }}>
                        <LinearProgress
                          variant="determinate"
                          value={job.progress_percentage}
                          color={job.status === 'failed' ? 'error' : 'primary'}
                        />
                      </Box>
                      <Typography variant="body2">
                        {job.progress_percentage}%
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                      {job.current_step || job.message}
                    </Typography>
                    {job.error && (
                      <Tooltip title={job.error}>
                        <Typography variant="caption" color="error" noWrap>
                          Error: {job.error}
                        </Typography>
                      </Tooltip>
                    )}
                  </TableCell>
                  <TableCell>{getRuntime(job)}</TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {(() => {
                        if (!job.started_at) return '-';
                        
                        try {
                          const startDate = new Date(job.started_at);
                          const now = new Date();
                          const diffMs = now.getTime() - startDate.getTime();
                          
                          // If the time is in the future, show absolute time instead
                          if (diffMs < 0) {
                            return startDate.toLocaleTimeString();
                          }
                          
                          return formatDistanceToNow(startDate, { addSuffix: true });
                        } catch (error) {
                          console.error('Error formatting start time:', error);
                          return 'Invalid date';
                        }
                      })()}
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                      {/* Pause button for running jobs */}
                      {job.status === 'running' && job.metadata?.celery_task_id && (
                        <Tooltip title="Pause Job">
                          <IconButton
                            size="small"
                            onClick={() => handlePauseJob(job.job_id)}
                            color="warning"
                          >
                            <PauseIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      
                      {/* Resume button for paused jobs */}
                      {['paused', 'pausing'].includes(job.status) && (
                        <Tooltip title="Resume Job">
                          <IconButton
                            size="small"
                            onClick={() => handleResumeJob(job.job_id)}
                            color="primary"
                          >
                            <ResumeIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      
                      {/* Cancel button for pending, running, and paused jobs */}
                      {['pending', 'running', 'paused', 'pausing'].includes(job.status) && (
                        <Tooltip title="Cancel Job">
                          <IconButton
                            size="small"
                            onClick={() => handleCancelJob(job.job_id)}
                            color="error"
                          >
                            <CancelIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default BackgroundJobsPage;