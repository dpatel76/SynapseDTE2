/**
 * File Upload Section Component
 * Handles data file uploads for profiling with validation and progress tracking
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  CloudUpload as UploadIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CheckCircle,
  Error as ErrorIcon,
  Description as FileIcon,
  Refresh as RefreshIcon,
  Send as SendIcon
} from '@mui/icons-material';
import { dataProfilingApi, DataFile } from '../../api/dataProfiling';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../api/client';

interface FileUploadSectionProps {
  cycleId: number;
  reportId: number;
  onFilesChange?: () => void;
}

const FileUploadSection: React.FC<FileUploadSectionProps> = ({
  cycleId,
  reportId,
  onFilesChange
}) => {
  const { user } = useAuth();
  const [files, setFiles] = useState<DataFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [uploadDialog, setUploadDialog] = useState(false);
  const [selectedDelimiter, setSelectedDelimiter] = useState(',');
  const [requestingData, setRequestingData] = useState(false);
  const [dataRequested, setDataRequested] = useState(false);
  const [assignmentCreated, setAssignmentCreated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<{open: boolean, file: DataFile | null}>({open: false, file: null});
  const [assignments, setAssignments] = useState<any[]>([]);
  const [completingAssignment, setCompletingAssignment] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadFiles();
    loadAssignments();
  }, [cycleId, reportId]);

  const loadFiles = async () => {
    try {
      const response = await dataProfilingApi.getFiles(cycleId, reportId);
      setFiles(response);
    } catch (error) {
      console.error('Error loading files:', error);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const performUpload = async () => {
    if (!selectedFile) return;
    await handleFileUpload(selectedFile);
    setSelectedFile(null);
    setUploadDialog(false);
  };

  const handleDeleteFile = async (file: DataFile) => {
    try {
      await dataProfilingApi.deleteFile(cycleId, reportId, file.file_id);
      setFiles(files.filter(f => f.file_id !== file.file_id));
      setDeleteConfirmDialog({open: false, file: null});
      if (onFilesChange) {
        onFilesChange();
      }
    } catch (error: any) {
      console.error('Error deleting file:', error);
      setError('Failed to delete file. Please try again.');
    }
  };

  const loadAssignments = async () => {
    try {
      // Use the new universal assignments endpoint
      const response = await apiClient.get(`/data-profiling/cycles/${cycleId}/reports/${reportId}/universal-assignments`);
      setAssignments(response.data);
      
      // Check if any assignments are completed (for Testers to see)
      const completedAssignments = response.data.filter((a: any) => a.status === 'Completed');
      if (completedAssignments.length > 0 && !canUploadFiles()) {
        // This is a Tester viewing completed assignments - show success message
        setDataRequested(true);
      }
    } catch (error: any) {
      console.error('Error loading assignments:', error);
      // Set empty assignments on error
      setAssignments([]);
    }
  };

  const completeAssignment = async (assignmentId: string) => {
    try {
      setCompletingAssignment(true);
      setError(null);
      
      const completionNotes = `Data files have been uploaded and validated for Report ${reportId}. Total files uploaded: ${files.length}. Assignment completed successfully.`;
      
      // Complete the assignment using the new universal assignment endpoint
      await apiClient.post(`/data-profiling/cycles/${cycleId}/reports/${reportId}/complete-assignment/${assignmentId}`, {
        completion_notes: completionNotes
      });
      
      // Refresh assignments and files
      await loadAssignments();
      await loadFiles();
      
      // Trigger parent component refresh to update workflow status
      if (onFilesChange) {
        onFilesChange();
      }
      
      setError(null);
    } catch (error: any) {
      console.error('Error completing assignment:', error);
      setError('Failed to complete assignment. Please try again.');
    } finally {
      setCompletingAssignment(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    try {
      setUploading(true);
      setUploadProgress(0);
      
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const response = await dataProfilingApi.uploadFile(cycleId, reportId, file, selectedDelimiter);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (response.success) {
        await loadFiles();
        onFilesChange?.();
        setUploadDialog(false);
      }
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const validateFiles = async () => {
    try {
      setValidating(true);
      await dataProfilingApi.validateFiles(cycleId, reportId);
      await loadFiles();
    } catch (error) {
      console.error('Error validating files:', error);
    } finally {
      setValidating(false);
    }
  };

  const getFileStatusChip = (file: DataFile) => {
    if (file.is_validated) {
      if (file.validation_errors && file.validation_errors.length > 0) {
        return (
          <Chip
            icon={<ErrorIcon />}
            label="Validation Issues"
            color="warning"
            size="small"
          />
        );
      } else {
        return (
          <Chip
            icon={<CheckCircle />}
            label="Validated"
            color="success"
            size="small"
          />
        );
      }
    } else {
      return (
        <Chip
          label="Pending Validation"
          color="default"
          size="small"
        />
      );
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const canUploadFiles = () => {
    return user?.role && ['Report Owner', 'Report Owner Executive', 'Admin'].includes(user.role);
  };

  const requestDataFromReportOwner = async () => {
    try {
      setRequestingData(true);
      setError(null);
      
      // Calculate due date (7 days from now)
      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() + 7);
      
      // Create standardized assignment for report owner
      const assignmentDetails = {
        request_type: 'Data Upload Request',
        description: `Data files are required for profiling analysis of Report ${reportId}. Please upload the necessary data files including sample datasets, test data, or production data extracts as appropriate for this testing cycle.`,
        priority: 'High',
        due_date: dueDate.toISOString()
      };
      
      // Use the new universal assignment endpoint with query parameters
      const response = await apiClient.post('/assignments/data-upload', {}, {
        params: {
          cycle_id: cycleId,
          report_id: reportId,
          description: assignmentDetails.description,
          priority: assignmentDetails.priority
        }
      });
      
      console.log('Assignment created:', response);
      setDataRequested(true);
      setAssignmentCreated(true);
      
      // Also refresh files in case any were already uploaded
      await loadFiles();
      onFilesChange?.();
      
    } catch (error: any) {
      console.error('Error creating assignment:', error);
      
      // Handle validation errors (which come as arrays)
      let errorMessage = 'Failed to create universal assignment. Please try again.';
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((err: any) => err.msg).join(', ');
        } else {
          errorMessage = error.response.data.detail;
        }
      }
      setError(errorMessage);
    } finally {
      setRequestingData(false);
    }
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Data File Upload
      </Typography>
      
      {/* Upload Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h4" color="primary">
                {files.length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Files Uploaded
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h4" color="success.main">
                {files.filter(f => f.is_validated && (!f.validation_errors || f.validation_errors.length === 0)).length}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Valid Files
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h4" color="info.main">
                {files.reduce((sum, f) => sum + (f.row_count || 0), 0).toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Records
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center', py: 2 }}>
              <Typography variant="h4" color="secondary.main">
                {files.reduce((sum, f) => sum + (f.column_count || 0), 0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Columns
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Success Alert */}
      {dataRequested && !error && (
        <Alert 
          severity="warning" 
          onClose={() => {setDataRequested(false); setAssignmentCreated(false);}} 
          sx={{ mb: 3 }}
          action={
            <Button 
              color="inherit" 
              size="small" 
              onClick={() => {setDataRequested(false); setAssignmentCreated(false);}}
            >
              Send Another Request
            </Button>
          }
        >
          <Typography variant="body2">
            {assignmentCreated ? (
              <>
                <strong>Assignment created successfully!</strong> A data upload assignment has been created for the Report Owner with a 7-day deadline. The Report Owner will receive a notification and can view this assignment in their dashboard.
              </>
            ) : (
              <>
                <strong>Data request recorded!</strong> The request has been logged in the system. However, <strong>no trackable assignment was created</strong> because the assignment framework is not yet implemented for data profiling. The Report Owner will need to check this workflow directly or be contacted separately.
              </>
            )}
            {' '}You can refresh this page to check for uploaded files.
          </Typography>
        </Alert>
      )}

      {/* Assignment Completion Section - For Report Owners */}
      {canUploadFiles() && assignments.length > 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2" gutterBottom>
            <strong>Active Assignment:</strong> You have {assignments.length} pending assignment(s) for data upload.
          </Typography>
          {assignments.map((assignment) => (
            <Box key={assignment.assignment_id} sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="body2" fontWeight="medium" gutterBottom>
                📋 {assignment.title}
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Due: {assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : 'No due date'} • 
                Priority: {assignment.priority} • 
                Status: {assignment.status}
              </Typography>
              {assignment.status === 'Assigned' && files.length > 0 && (
                <Button
                  variant="contained"
                  color="success"
                  size="small"
                  startIcon={completingAssignment ? <CircularProgress size={16} color="inherit" /> : <CheckCircle />}
                  onClick={() => completeAssignment(assignment.assignment_id)}
                  disabled={completingAssignment}
                  sx={{ mt: 1 }}
                >
                  {completingAssignment ? 'Completing...' : 'Complete Assignment'}
                </Button>
              )}
              {assignment.status === 'Completed' && (
                <Chip 
                  label="✅ Assignment Completed" 
                  color="success" 
                  size="small" 
                  sx={{ mt: 1 }}
                />
              )}
            </Box>
          ))}
        </Alert>
      )}

      {/* Assignment Status Section - For Testers to see completed assignments */}
      {!canUploadFiles() && assignments.length > 0 && (
        <Alert 
          severity={assignments.some((a: any) => a.status === 'Completed') ? "success" : "info"} 
          sx={{ mb: 3, border: assignments.some((a: any) => a.status === 'Completed') ? 2 : 1, borderColor: assignments.some((a: any) => a.status === 'Completed') ? 'success.main' : 'info.main' }}
        >
          {assignments.some((a: any) => a.status === 'Completed') ? (
            <Typography variant="body2" gutterBottom>
              <strong>🎉 Data Upload Completed!</strong> The Report Owner has uploaded the required data files and completed the assignment.
            </Typography>
          ) : (
            <Typography variant="body2" gutterBottom>
              <strong>Assignment Status:</strong> Data upload assignments for this report.
            </Typography>
          )}
          {assignments.map((assignment) => (
            <Box key={assignment.assignment_id} sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Typography variant="body2" fontWeight="medium" gutterBottom>
                📋 {assignment.title}
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Assigned: {assignment.assigned_at ? new Date(assignment.assigned_at).toLocaleDateString() : 'Unknown'} • 
                Status: {assignment.status}
                {assignment.completed_at && ` • Completed: ${new Date(assignment.completed_at).toLocaleDateString()}`}
              </Typography>
              {assignment.status === 'Completed' && (
                <Box sx={{ mt: 1 }}>
                  <Chip 
                    label="✅ Assignment Completed" 
                    color="success" 
                    size="small"
                  />
                  <Typography variant="body2" color="success.main" fontWeight="medium" sx={{ mt: 1 }}>
                    ✓ Ready to proceed with file validation and rule generation
                  </Typography>
                  {assignment.completion_notes && (
                    <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                      Notes: {assignment.completion_notes}
                    </Typography>
                  )}
                </Box>
              )}
              {assignment.status === 'Assigned' && (
                <Chip 
                  label="⏳ Pending" 
                  color="warning" 
                  size="small"
                  sx={{ mt: 1 }}
                />
              )}
            </Box>
          ))}
          
          {/* Show next steps for completed assignments */}
          {assignments.some((a: any) => a.status === 'Completed') && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'success.50', borderRadius: 1, border: 1, borderColor: 'success.main' }}>
              <Typography variant="body2" fontWeight="medium" gutterBottom>
                🚀 Next Steps:
              </Typography>
              <Typography variant="caption" color="text.secondary">
                • Check uploaded files in the table below<br/>
                • Validate files using the "Validate Files" button<br/>
                • Generate profiling rules once validation is complete<br/>
                • Proceed with data profiling execution
              </Typography>
            </Box>
          )}
        </Alert>
      )}

      {/* Role-based Action Section - Only show if data hasn't been requested yet */}
      {!canUploadFiles() && !dataRequested && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2" gutterBottom>
            <strong>Data Upload Workflow:</strong> As a {user?.role}, you can request data from the Report Owner who will upload the necessary files for profiling.
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={requestingData ? <CircularProgress size={16} color="inherit" /> : <SendIcon />}
              onClick={requestDataFromReportOwner}
              disabled={requestingData}
            >
              {requestingData ? 'Sending Request...' : 'Request Data from Report Owner'}
            </Button>
          </Box>
        </Alert>
      )}

      {/* Upload Actions - Only for authorized roles */}
      {canUploadFiles() && (
        <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialog(true)}
            disabled={uploading}
          >
            Upload New File
          </Button>
        
          {files.length > 0 && (
            <Button
              variant="outlined"
              startIcon={<CheckCircle />}
              onClick={validateFiles}
              disabled={validating}
            >
              {validating ? 'Validating...' : 'Validate All Files'}
            </Button>
          )}
          
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadFiles}
          >
            Refresh
          </Button>
        </Box>
      )}

      {/* Refresh button for non-upload users */}
      {!canUploadFiles() && files.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadFiles}
          >
            Refresh Files
          </Button>
        </Box>
      )}

      {/* Files Table */}
      {files.length > 0 && (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>File Name</strong></TableCell>
                <TableCell><strong>Format</strong></TableCell>
                <TableCell><strong>Size</strong></TableCell>
                <TableCell><strong>Records</strong></TableCell>
                <TableCell><strong>Columns</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Uploaded</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {files.map((file) => (
                <TableRow key={file.file_id} hover>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <FileIcon color="action" sx={{ mr: 1 }} />
                      <Typography variant="body2" fontWeight="medium">
                        {file.file_name}
                      </Typography>
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Chip 
                      label={file.file_format.toUpperCase()} 
                      size="small" 
                      color="primary"
                      variant="outlined"
                    />
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2">
                      {formatFileSize(file.file_size)}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {file.row_count?.toLocaleString() || 'Unknown'}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2">
                      {file.column_count || 'Unknown'}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    {getFileStatusChip(file)}
                    {file.validation_errors && file.validation_errors.length > 0 && (
                      <Box sx={{ mt: 0.5 }}>
                        <Typography variant="caption" color="error">
                          {file.validation_errors.length} issue(s)
                        </Typography>
                      </Box>
                    )}
                  </TableCell>
                  
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {new Date(file.uploaded_at).toLocaleDateString()}
                    </Typography>
                  </TableCell>
                  
                  <TableCell>
                    <Box display="flex" gap={1}>
                      <Tooltip title="View details">
                        <IconButton size="small">
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete file">
                        <IconButton 
                          size="small" 
                          color="error"
                          onClick={() => setDeleteConfirmDialog({open: true, file})}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {files.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          {canUploadFiles() ? 
            'No files uploaded yet. Upload data files to begin profiling analysis.' :
            'No files uploaded yet. Request data from the Report Owner to begin profiling analysis.'
          }
        </Alert>
      )}

      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Upload Data File</DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {/* Drag and Drop Area */}
            <Box
              sx={{
                border: `2px dashed ${dragActive ? 'primary.main' : 'grey.300'}`,
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                bgcolor: dragActive ? 'action.hover' : 'background.paper',
                cursor: 'pointer',
                mb: 3
              }}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <UploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Drag and drop files here
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                or click to select files
              </Typography>
              <Button variant="outlined">
                Select Files
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                style={{ display: 'none' }}
                accept=".csv,.xlsx,.xls"
                onChange={handleFileSelect}
              />
            </Box>

            {/* File Format Options */}
            <Divider sx={{ my: 2 }} />
            
            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>CSV Delimiter</InputLabel>
              <Select
                value={selectedDelimiter}
                label="CSV Delimiter"
                onChange={(e) => setSelectedDelimiter(e.target.value)}
              >
                <MenuItem value=",">Comma (,)</MenuItem>
                <MenuItem value=";">Semicolon (;)</MenuItem>
                <MenuItem value="\t">Tab</MenuItem>
                <MenuItem value="|">Pipe (|)</MenuItem>
              </Select>
            </FormControl>

            {/* Selected File Display */}
            {selectedFile && (
              <Box sx={{ mt: 2, p: 2, bgcolor: 'success.50', borderRadius: 1, border: 1, borderColor: 'success.main' }}>
                <Typography variant="body2" fontWeight="medium" gutterBottom>
                  Selected File:
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  📄 {selectedFile.name} ({formatFileSize(selectedFile.size)})
                </Typography>
              </Box>
            )}

            {/* Upload Progress */}
            {uploading && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" gutterBottom>
                  Uploading file... {uploadProgress}%
                </Typography>
                <LinearProgress variant="determinate" value={uploadProgress} />
              </Box>
            )}

            <Alert severity="info" sx={{ mt: 2 }}>
              Supported formats: CSV, Excel (.xlsx, .xls)
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setSelectedFile(null);
            setUploadDialog(false);
          }}>Cancel</Button>
          <Button 
            variant="contained" 
            onClick={performUpload}
            disabled={!selectedFile || uploading}
            startIcon={uploading ? <CircularProgress size={16} /> : <UploadIcon />}
          >
            {uploading ? 'Uploading...' : 'Upload File'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog 
        open={deleteConfirmDialog.open} 
        onClose={() => setDeleteConfirmDialog({open: false, file: null})}
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the file "{deleteConfirmDialog.file?.file_name}"?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmDialog({open: false, file: null})}>
            Cancel
          </Button>
          <Button 
            variant="contained" 
            color="error" 
            onClick={() => deleteConfirmDialog.file && handleDeleteFile(deleteConfirmDialog.file)}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FileUploadSection;