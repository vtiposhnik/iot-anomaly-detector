import { Box, CircularProgress, Typography, Container, Drawer, Button, Fab, Tooltip } from "@mui/material";
import DeviceList from "../DeviceList";
import DataVisualization from "../DataVisualization";
import AnomalyDetection from "../AnomalyDetection";
import Navigation from "../Navigation";
import KPIDashboard from "../KPIDashboard";
import ModelControls from "../ModelControls";
import { DeviceData, FormattedAnomaly, Device } from "../../types";
import { useState } from "react";
import { Menu as MenuIcon, Dashboard as DashboardIcon } from "@mui/icons-material";

interface DashboardBodyProps {
    devices: Device[];
    selectedDevice: number | null;
    setSelectedDevice: (device: number) => void;
    anomalies: FormattedAnomaly[];
    deviceAnomaliesMap: Record<string, FormattedAnomaly[]>;
    mappedDeviceData: DeviceData[];
    isLoading: boolean;
}

const DashboardBody = ({
    devices,
    selectedDevice,
    setSelectedDevice,
    anomalies,
    deviceAnomaliesMap,
    mappedDeviceData,
    isLoading
}: DashboardBodyProps) => {
    const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
    const [isKPIDrawerOpen, setIsKPIDrawerOpen] = useState<boolean>(false);

    if (isLoading) {
        return (
            <Box
                display="flex"
                flexDirection="column"
                justifyContent="center"
                alignItems="center"
                height="60vh"
            >
                <CircularProgress size={48} thickness={4} sx={{ mb: 2 }} />
                <Typography variant="body2" color="text.secondary">
                    Loading data...
                </Typography>
            </Box>
        )
    }

    const toggleDrawer = (isOpen: boolean) => {
        setIsDrawerOpen(isOpen);
    }

    const toggleKPIDrawer = (isOpen: boolean) => {
        setIsKPIDrawerOpen(isOpen);
    }

    return (
        <Container maxWidth="xl" sx={{ mt: 2 }}>
            <Box sx={{ position: 'fixed', left: 20, top: '50%', transform: 'translateY(-50%)', display: 'flex', flexDirection: 'column', gap: 2, zIndex: 1100 }}>
                <Tooltip title="Navigation" placement="right">
                    <Fab 
                        color="primary" 
                        aria-label="navigation" 
                        onClick={() => toggleDrawer(true)}
                        sx={{ bgcolor: 'primary.main' }}
                    >
                        <MenuIcon />
                    </Fab>
                </Tooltip>
                
                <Tooltip title="KPI Dashboard" placement="right">
                    <Fab 
                        color="secondary" 
                        aria-label="kpi dashboard" 
                        onClick={() => toggleKPIDrawer(true)}
                        sx={{ bgcolor: 'primary.main' }}
                    >
                        <DashboardIcon />
                    </Fab>
                </Tooltip>
            </Box>
            
            <Drawer open={isDrawerOpen} onClose={() => toggleDrawer(false)} anchor="left">
                <Navigation />
            </Drawer>
            
            <Drawer open={isKPIDrawerOpen} onClose={() => toggleKPIDrawer(false)} anchor="right">
                <KPIDashboard />
            </Drawer>
            <Box sx={{ mb: 2 }}>
                <Box sx={{ display: 'flex', gap: 2, height: '80vh' }}>
                    <DeviceList
                        devices={devices}
                        selectedDevice={selectedDevice}
                        onSelectDevice={setSelectedDevice}
                        anomalies={anomalies}
                        deviceAnomaliesMap={deviceAnomaliesMap}
                    />
                    <DataVisualization data={mappedDeviceData} />
                </Box>
            </Box>
            <AnomalyDetection
                anomalies={anomalies}
                deviceData={mappedDeviceData}
            />
        </Container>
    )
}

export default DashboardBody;