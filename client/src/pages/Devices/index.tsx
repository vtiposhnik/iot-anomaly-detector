import { useEffect, useState, FC } from 'react';
import { Box, Typography, Table, TableHead, TableRow, TableCell, TableBody, TableContainer, Paper, CircularProgress } from '@mui/material';
import api from '@/services/api';
import { Device } from '@/types';

const Devices: FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDevices = async () => {
      try {
        const data = await api.fetchDevices();
        setDevices(data);
      } catch (err) {
        console.error('Failed to load devices', err);
        setError('Failed to load devices');
      } finally {
        setLoading(false);
      }
    };

    loadDevices();
  }, []);

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Devices
      </Typography>
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>IP Address</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Last Seen</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {devices.map(device => (
              <TableRow key={device.deviceId} hover>
                <TableCell>{device.deviceId}</TableCell>
                <TableCell>{device.name || `Device ${device.deviceId}`}</TableCell>
                <TableCell>{device.type || 'N/A'}</TableCell>
                <TableCell>{device.ipAddress}</TableCell>
                <TableCell>{device.status ? 'Online' : 'Offline'}</TableCell>
                <TableCell>{new Date(device.lastSeen).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default Devices;
