import { Box, Grid, CircularProgress, Typography, Container } from "@mui/material";
import DeviceList from "../DeviceList";
import DataVisualization from "../DataVisualization";
import AnomalyDetection from "../AnomalyDetection";
import Navigation from "../Navigation";
import KPIDashboard from "../KPIDashboard";
import ModelControls from "../ModelControls";
import { DeviceData, FormattedAnomaly, Device } from "../../types";

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

    return (
        <Container maxWidth="xl" sx={{ mt: 2 }}>
            <Grid container spacing={2}>
                {/* Navigation sidebar */}
                <Grid item xs={12} md={2}>
                    <Navigation />
                </Grid>
                
                {/* Main content */}
                <Grid item xs={12} md={10}>
                    <Box sx={{ height: 'calc(100vh - 160px)', minHeight: '580px', display: 'flex', flexDirection: 'column', gap: 2, mb: 2, overflow: 'auto' }}>
                        {/* KPI Dashboard */}
                        <KPIDashboard />
                        
                        {/* Model Controls */}
                        <ModelControls />
                        
                        <Box sx={{ display: 'flex', gap: 2, height: '40%' }}>
                            <DeviceList
                                devices={devices}
                                selectedDevice={selectedDevice}
                                onSelectDevice={setSelectedDevice}
                                anomalies={anomalies}
                                deviceAnomaliesMap={deviceAnomaliesMap}
                            />
                            <DataVisualization data={mappedDeviceData} />
                        </Box>
                        <AnomalyDetection
                            anomalies={anomalies}
                            deviceData={mappedDeviceData}
                        />
                    </Box>
                </Grid>
            </Grid>
        </Container>
    )
}

export default DashboardBody;