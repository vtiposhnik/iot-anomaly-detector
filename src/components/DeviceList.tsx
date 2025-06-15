import React from 'react';
import { List, Typography, Box, ListItemButton, ListItemText, ListItemIcon, Divider, Chip } from '@mui/material';
import WarningIcon from '@mui/icons-material/Warning';
import DevicesIcon from '@mui/icons-material/Devices';
import RouterIcon from '@mui/icons-material/Router';
import VideocamIcon from '@mui/icons-material/Videocam';
import SmartToyIcon from '@mui/icons-material/SmartToy';

interface Anomaly {
  id: string;
  deviceId: string;
  timestamp: string;
  type: string;
  severity: string;
  value: number;
  threshold: number;
  description: string;
  resolved: boolean;
}

interface DeviceListProps {
  devices: Array<{deviceId: number; name?: string; type?: string; location?: string}>;
  selectedDevice: number | null;
  onSelectDevice: (deviceId: number) => void;
  anomalies: Anomaly[];
  deviceAnomaliesMap: Record<string, Anomaly[]>;
}

const DeviceList: React.FC<DeviceListProps> = ({ 
  devices, 
  selectedDevice, 
  onSelectDevice,
  // We don't use anomalies directly anymore, but keep it in props for compatibility
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  anomalies,
  deviceAnomaliesMap 
}) => {
  // Get a list of all devices with anomalies from the map
  const devicesWithAnomalies = Object.keys(deviceAnomaliesMap);
  
  // Function to get appropriate icon based on device type
  const getDeviceIcon = (type?: string) => {
    switch(type?.toLowerCase()) {
      case 'camera':
        return <VideocamIcon />;
      case 'router':
        return <RouterIcon />;
      case 'bot':
        return <SmartToyIcon />;
      default:
        return <DevicesIcon />;
    }
  };
  
  // Function to get severity color based on the device anomalies map
  const getSeverityColor = (deviceId: string) => {
    const deviceAnomalies = deviceAnomaliesMap[deviceId] || [];
    if (deviceAnomalies.some(a => a.severity === 'high' || a.severity === 'critical')) {
      return 'error';
    } else if (deviceAnomalies.some(a => a.severity === 'medium')) {
      return 'warning';
    }
    return 'info';
  };

  console.log(devices);
  
  return (
    <Box sx={{ 
      borderRadius: 2,
      overflow: 'hidden',
      height: '100%',
      display: 'flex',
      minWidth: '25%',
      flexDirection: 'column',
      bgcolor: 'background.paper',
      border: '1px solid rgba(0, 0, 0, 0.08)',
    }}>
      <Typography variant="h6" component="h2" sx={{ p: 2, borderBottom: '1px solid rgba(0, 0, 0, 0.08)' }}>
        Devices
      </Typography>
      
      <List 
        sx={{ 
          width: '100%', 
          bgcolor: 'background.paper',
          overflow: 'auto',
          flex: 1,
          '& .MuiListItemButton-root': {
            borderLeft: '3px solid transparent',
            transition: 'all 0.2s ease',
            mb: 0.5,
          },
          '& .MuiListItemButton-root:hover': {
            bgcolor: 'rgba(52, 152, 219, 0.08)',
          },
          '& .MuiListItemButton-root.Mui-selected': {
            bgcolor: 'rgba(52, 152, 219, 0.12)',
            borderLeft: '3px solid #3498db',
          },
          '& .MuiListItemButton-root.Mui-selected:hover': {
            bgcolor: 'rgba(52, 152, 219, 0.18)',
          },
        }}
      >
        {devices.map((device, index) => {
          const deviceId = device.deviceId.toString();
          const isSelected = selectedDevice === device.deviceId;
          
          return (
            <React.Fragment key={device.deviceId}>
              {index > 0 && <Divider variant="inset" component="li" />}
              <ListItemButton
                onClick={() => onSelectDevice(device.deviceId)}
                selected={isSelected}
                sx={{
                  borderRadius: 1,
                  mb: 0.5,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.light',
                    '&:hover': {
                      backgroundColor: 'primary.light',
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  {getDeviceIcon(device.type)}
                </ListItemIcon>
                <ListItemText 
                  primary={device.name || `Device ${deviceId}`}
                  secondary={device.location || device.type || `ID: ${deviceId}`}
                  primaryTypographyProps={{ fontWeight: isSelected ? 600 : 400 }}
                />
                
                {devicesWithAnomalies.includes(deviceId) && (
                  <Chip 
                    label={deviceAnomaliesMap[deviceId]?.length || 0}
                    size="small" 
                    color={getSeverityColor(deviceId)}
                    icon={<WarningIcon fontSize="small" />}
                    sx={{ ml: 1, minWidth: 70 }}
                  />
                )}
              </ListItemButton>
            </React.Fragment>
          );
        })}
      </List>
      
      {devices.length === 0 && (
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Typography variant="body2" color="text.secondary">
            No devices found
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default DeviceList;