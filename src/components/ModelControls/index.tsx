import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Slider,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  SelectChangeEvent,
  Tooltip
} from '@mui/material';
import {
  Tune as TuneIcon,
  Refresh as RefreshIcon,
  Check as CheckIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import axios from 'axios';

// Define API URL and auth header function
const API_URL = '/api/v1';
const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

// Model settings interface
interface ModelSettings {
  threshold: number;
  selectedModel: string;
  lastTrained: string;
  accuracy: number;
  status: string;
}

/**
 * Model Controls component for adjusting anomaly detection settings
 */
const ModelControls: React.FC = () => {
  // State for model settings
  const [settings, setSettings] = useState<ModelSettings>({
    threshold: 0.7,
    selectedModel: 'both',
    lastTrained: '',
    accuracy: 0,
    status: 'idle'
  });
  
  const [loading, setLoading] = useState(false);
  const [retraining, setRetraining] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Interface for model info response
  interface ModelInfoResponse {
    threshold: number;
    current_model: string;
    last_trained: string;
    accuracy: number;
    status: string;
  }

  // Fetch current model settings
  const fetchModelSettings = async () => {
    try {
      setLoading(true);
      
      const response = await axios.get<ModelInfoResponse>(
        `${API_URL}/model/info`,
        { headers: getAuthHeader() }
      );
      
      setSettings({
        threshold: response.data.threshold,
        selectedModel: response.data.current_model,
        lastTrained: response.data.last_trained,
        accuracy: response.data.accuracy,
        status: response.data.status
      });
      
      setError(null);
    } catch (err) {
      console.error('Error fetching model settings:', err);
      setError('Failed to load model settings');
      
      // Use default settings if API fails
      setSettings({
        threshold: 0.7,
        selectedModel: 'both',
        lastTrained: new Date().toISOString(),
        accuracy: 92.5,
        status: 'idle'
      });
    } finally {
      setLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    fetchModelSettings();
  }, []);

  // Handle threshold change
  const handleThresholdChange = (_event: Event, newValue: number | number[]) => {
    setSettings({
      ...settings,
      threshold: newValue as number
    });
  };

  // Handle model selection change
  const handleModelChange = (event: SelectChangeEvent) => {
    setSettings({
      ...settings,
      selectedModel: event.target.value
    });
  };

  // Handle saving settings
  const handleSaveSettings = async () => {
    try {
      setLoading(true);
      
      await axios.post(
        `${API_URL}/model/settings`,
        {
          threshold: settings.threshold,
          model: settings.selectedModel
        },
        { headers: getAuthHeader() }
      );
      
      setSuccess('Settings saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Error saving settings:', err);
      setError('Failed to save settings');
      setTimeout(() => setError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  // Handle model retraining
  const handleRetrainModel = async () => {
    try {
      setRetraining(true);
      
      await axios.post(
        `${API_URL}/model/retrain`,
        { model: settings.selectedModel },
        { headers: getAuthHeader() }
      );
      
      setSuccess('Model retraining initiated');
      setTimeout(() => setSuccess(null), 3000);
      
      // Refresh settings after a delay to get updated training status
      setTimeout(fetchModelSettings, 2000);
    } catch (err) {
      console.error('Error retraining model:', err);
      setError('Failed to initiate model retraining');
      setTimeout(() => setError(null), 5000);
    } finally {
      setRetraining(false);
    }
  };

  // Format the last trained date
  const formatLastTrained = (dateString: string) => {
    if (!dateString) return 'Never';
    
    try {
      const date = new Date(dateString);
      return date.toLocaleString();
    } catch (err) {
      return dateString;
    }
  };

  return (
    <Card elevation={2} sx={{ mb: 3 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <TuneIcon color="primary" sx={{ mr: 1 }} />
          <Typography variant="h6" component="div">
            Model Controls
          </Typography>
        </Box>
        
        {(error || success) && (
          <Alert 
            severity={error ? 'error' : 'success'} 
            sx={{ mb: 2 }}
            onClose={() => error ? setError(null) : setSuccess(null)}
          >
            {error || success}
          </Alert>
        )}
        
        <Grid container spacing={3}>
          {/* Model Selection */}
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel id="model-select-label">Detection Model</InputLabel>
              <Select
                labelId="model-select-label"
                value={settings.selectedModel}
                label="Detection Model"
                onChange={handleModelChange}
                disabled={loading || retraining}
              >
                <MenuItem value="isolation_forest">Isolation Forest</MenuItem>
                <MenuItem value="local_outlier_factor">Local Outlier Factor</MenuItem>
                <MenuItem value="both">Ensemble (Both)</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          {/* Threshold Slider */}
          <Grid item xs={12} md={8}>
            <Typography gutterBottom>Anomaly Threshold: {settings.threshold}</Typography>
            <Tooltip title="Lower values increase sensitivity (more anomalies detected)" placement="top">
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Slider
                  value={settings.threshold}
                  onChange={handleThresholdChange}
                  step={0.05}
                  marks
                  min={0.1}
                  max={0.95}
                  disabled={loading || retraining}
                  valueLabelDisplay="auto"
                  sx={{ mr: 1 }}
                />
                <InfoIcon color="action" fontSize="small" />
              </Box>
            </Tooltip>
          </Grid>
          
          {/* Model Info */}
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Typography variant="body2" color="text.secondary">
                Last Trained: {formatLastTrained(settings.lastTrained)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Current Accuracy: {settings.accuracy.toFixed(1)}%
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
                  Status:
                </Typography>
                <Chip 
                  size="small" 
                  label={settings.status} 
                  color={settings.status === 'idle' ? 'success' : 'warning'}
                />
              </Box>
            </Box>
          </Grid>
          
          {/* Action Buttons */}
          <Grid item xs={12} md={6} sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'flex-end' }}>
            <Button
              variant="outlined"
              color="primary"
              onClick={handleSaveSettings}
              disabled={loading || retraining}
              startIcon={loading ? <CircularProgress size={20} /> : <CheckIcon />}
              sx={{ mr: 2 }}
            >
              Save Settings
            </Button>
            <Button
              variant="contained"
              color="secondary"
              onClick={handleRetrainModel}
              disabled={loading || retraining}
              startIcon={retraining ? <CircularProgress size={20} /> : <RefreshIcon />}
            >
              Retrain Model
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default ModelControls;
