import { Alert, Box, Typography, Container, AppBar, Toolbar, Button } from '@mui/material'
import { Notifications as NotificationsIcon } from '@mui/icons-material'
import { Link as RouterLink } from 'react-router-dom'
import AuthHeader from '../AuthHeader'

const DashboardHeader = ({ error }: { error?: string | null }) => (
    <Box sx={{ flexGrow: 1 }}>
        <AppBar position="static" color="default" elevation={1}>
            <Toolbar>
                <Typography
                    variant="h6"
                    component="div"
                    sx={{ 
                        flexGrow: 1,
                        fontWeight: 700,
                        color: 'primary.main',
                    }}
                >
                    IoT Anomaly Detection System
                </Typography>
                <Button
                    component={RouterLink}
                    to="/alerts"
                    color="primary"
                    startIcon={<NotificationsIcon />}
                    sx={{ mr: 2 }}
                >
                    Alerts
                </Button>
                <AuthHeader />
            </Toolbar>
        </AppBar>
        
        <Container maxWidth="lg" sx={{ mt: 3, mb: 2 }}>
            <Typography
                variant="h4"
                component="h1"
                align="center"
                sx={{
                    fontWeight: 700,
                    color: 'primary.main',
                    mb: 0.5,
                    fontSize: { xs: '1.5rem', sm: '1.75rem', md: '2rem' }
                }}
            >
                IoT Anomaly Detection Dashboard
            </Typography>
            <Typography
                variant="subtitle2"
                align="center"
                color="text.secondary"
                sx={{ mb: 2, fontWeight: 500 }}
            >
                Monitoring network traffic for suspicious patterns
            </Typography>

            {error && (
                <Alert
                    severity="error"
                    sx={{
                        mb: 3,
                        borderRadius: 2,
                        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.05)'
                    }}
                >
                    {error}
                </Alert>
            )}
        </Container>
    </Box>
)

export default DashboardHeader;