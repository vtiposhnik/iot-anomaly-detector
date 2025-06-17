import { FC, useEffect, useState } from "react";

import DeviceList from '@/components/DeviceList';
import DataVisualization from '@/components/DataVisualization';
import api from '@/services/api';
import AnomalyDetection from '@/components/AnomalyDetection';
import KPIDashboard from '@/components/KPIDashboard';
import socketService from '@/services/socket';
import { Container, Box, Grid, CircularProgress, Alert, Snackbar } from '@mui/material';
import { DeviceData, FormattedAnomaly, Device } from '@/types';
import DashboardHeader from '@/components/DashboardHeader';
import DashboardBody from '@/components/DashboardBody';

const Dashboard: FC = () => {
    const [devices, setDevices] = useState<Device[]>([]);
    const [selectedDevice, setSelectedDevice] = useState<number | null>(null);
    const [deviceData, setDeviceData] = useState<DeviceData[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [anomalies, setAnomalies] = useState<FormattedAnomaly[]>([]);
    // Store all device anomalies in a map for quick access and persistence
    const [deviceAnomaliesMap, setDeviceAnomaliesMap] = useState<Record<string, FormattedAnomaly[]>>({});
    const [error, setError] = useState<string | null>(null);
    const [notification, setNotification] = useState<{
        open: boolean;
        message: string;
        severity: 'success' | 'info' | 'warning' | 'error';
    }>({
        open: false,
        message: '',
        severity: 'info'
    });

    // Initialize socket connection
    useEffect(() => {
        socketService.connect();

        // Listen for anomaly alerts
        socketService.addEventListener('anomaly_alert', (data: FormattedAnomaly) => {
            setNotification({
                open: true,
                message: `Anomaly detected: ${data.description}`,
                severity: data.severity === 'high' ? 'error' : data.severity === 'medium' ? 'warning' : 'info'
            });

            // Update both the current anomalies and the device anomalies map
            const deviceId = data.deviceId;

            // Update current anomalies if it's for the selected device
            if (selectedDevice?.toString() === deviceId) {
                setAnomalies(prev => [data, ...prev]);
            }

            // Always update the map to keep it in sync
            setDeviceAnomaliesMap(prev => ({
                ...prev,
                [deviceId]: [data, ...(prev[deviceId] || [])]
            }));
        });

        // Listen for data updates
        socketService.addEventListener('data_update', (data: DeviceData) => {
            if (data.id === selectedDevice?.toString()) {
                setDeviceData(prev => [data, ...prev].slice(0, 100));
            }
        });

        // Cleanup on unmount
        return () => {
            socketService.disconnect();
        };
    }, [selectedDevice]);

    // Load devices from API and their anomalies (only once at startup)
    useEffect(() => {
        const loadDevices = async () => {
            try {
                setLoading(true);
                const devicesData = await api.fetchDevices();
                setDevices(devicesData);

                // Fetch anomalies for all devices in parallel
                const anomalyPromises = devicesData.map(device =>
                    api.fetchDeviceAnomalies(device.deviceId.toString(), { resolved: false })
                        .then(anomalies => ({ deviceId: device.deviceId.toString(), anomalies }))
                        .catch(err => {
                            console.error(`Error fetching anomalies for device ${device.deviceId}:`, err);
                            return { deviceId: device.deviceId.toString(), anomalies: [] };
                        })
                );

                const results = await Promise.all(anomalyPromises);

                // Build the device anomalies map
                const anomaliesMap: Record<string, FormattedAnomaly[]> = {};
                results.forEach(result => {
                    anomaliesMap[result.deviceId] = result.anomalies;
                });

                setDeviceAnomaliesMap(anomaliesMap);

                // Set the first device as selected by default
                if (devicesData.length > 0 && !selectedDevice) {
                    const firstDeviceId = devicesData[0].deviceId;
                    setSelectedDevice(firstDeviceId);
                    // Set anomalies for the first device
                    setAnomalies(anomaliesMap[firstDeviceId.toString()] || []);
                }

                setLoading(false);
            } catch (error) {
                console.error('Error loading devices:', error);
                setError('Failed to load devices. Please try again later.');
                setLoading(false);
            }
        };

        loadDevices();
    }, []);

    // Load device data when a device is selected
    useEffect(() => {
        const loadDeviceData = async () => {
            if (!selectedDevice) return;

            try {
                setLoading(true);
                const deviceId = selectedDevice.toString();

                // Fetch device data
                const data = await api.fetchDeviceData(deviceId, 100);
                setDeviceData(data);

                // Use cached anomalies if available, otherwise fetch them
                if (deviceAnomaliesMap[deviceId]) {
                    setAnomalies(deviceAnomaliesMap[deviceId]);
                    setLoading(false);
                } else {
                    // Only fetch anomalies if we don't have them cached
                    const anomaliesData = await api.fetchDeviceAnomalies(deviceId, { resolved: false });

                    // Update both the current anomalies and the map
                    setAnomalies(anomaliesData);
                    setDeviceAnomaliesMap(prev => ({
                        ...prev,
                        [deviceId]: anomaliesData
                    }));

                    setLoading(false);
                }
            } catch (error) {
                console.error('Error loading device data:', error);
                setError('Failed to load device data. Please try again later.');
                setLoading(false);
            }
        };

        loadDeviceData();
    }, [selectedDevice, deviceAnomaliesMap]);

    // Handle notification close
    const handleNotificationClose = () => {
        setNotification({ ...notification, open: false });
    };

    // Map data to the format expected by components
    const mappedDeviceData = deviceData.map(data => ({
        id: data.id,
        timestamp: data.timestamp,
        packetSize: data.packetSize,
        origBytes: data.origBytes,
        respBytes: data.respBytes,
        duration: data.duration,
        status: data.status,
        network: data.network
    }));

    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <DashboardHeader />
            <DashboardBody
                devices={devices}
                selectedDevice={selectedDevice}
                setSelectedDevice={setSelectedDevice}
                anomalies={anomalies}
                deviceAnomaliesMap={deviceAnomaliesMap}
                mappedDeviceData={mappedDeviceData}
                isLoading={loading}
            />

            <Snackbar
                open={notification.open}
                autoHideDuration={6000}
                onClose={handleNotificationClose}
            >
                <Alert
                    onClose={handleNotificationClose}
                    severity={notification.severity}
                    sx={{ width: '100%' }}
                >
                    {notification.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default Dashboard;