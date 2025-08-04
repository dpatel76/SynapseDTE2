import React from 'react';
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Box,
  Typography,
  SelectChangeEvent,
} from '@mui/material';
import { RFIVersionListItem, VersionStatus } from '../../types/rfiVersions';

interface RFIVersionSelectorProps {
  versions: RFIVersionListItem[];
  selectedVersionId: string;
  onVersionChange: (versionId: string) => void;
  disabled?: boolean;
}

const getVersionStatusColor = (status: VersionStatus): 'default' | 'primary' | 'success' | 'error' | 'warning' => {
  switch (status) {
    case VersionStatus.DRAFT:
      return 'primary';
    case VersionStatus.PENDING_APPROVAL:
      return 'warning';
    case VersionStatus.APPROVED:
      return 'success';
    case VersionStatus.REJECTED:
      return 'error';
    case VersionStatus.SUPERSEDED:
      return 'default';
    default:
      return 'default';
  }
};

const formatVersionStatus = (status: VersionStatus): string => {
  return status.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ');
};

export const RFIVersionSelector: React.FC<RFIVersionSelectorProps> = ({
  versions,
  selectedVersionId,
  onVersionChange,
  disabled = false,
}) => {
  const handleChange = (event: SelectChangeEvent<string>) => {
    onVersionChange(event.target.value);
  };

  if (versions.length === 0) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No versions available
        </Typography>
      </Box>
    );
  }

  return (
    <FormControl size="small" sx={{ minWidth: 250 }}>
      <InputLabel>Version</InputLabel>
      <Select
        value={selectedVersionId}
        onChange={handleChange}
        label="Version"
        disabled={disabled}
      >
        {versions.map((version) => (
          <MenuItem key={version.version_id} value={version.version_id}>
            <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', gap: 1 }}>
              <Typography variant="body2">
                v{version.version_number}
              </Typography>
              {version.is_current && (
                <Chip
                  label="Current"
                  size="small"
                  color="primary"
                  variant="outlined"
                  sx={{ height: 20, fontSize: '0.7rem' }}
                />
              )}
              <Chip
                label={formatVersionStatus(version.version_status)}
                size="small"
                color={getVersionStatusColor(version.version_status)}
                sx={{ height: 20, fontSize: '0.7rem' }}
              />
              {version.can_be_edited && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>
                  (Editable)
                </Typography>
              )}
            </Box>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};