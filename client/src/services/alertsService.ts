import axios from 'axios';
import { getToken } from './authService';

// API base URL - using relative path for proxy
const API_URL = '/api/v1/alerts';

/**
 * Alert interface representing an alert from the backend
 */
export interface Alert {
  id: number;
  anomaly_id: number;
  raised_at: string;
  cleared_at: string | null;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  acknowledged: boolean;
  device_id?: string;
  model_id?: string;
}

/**
 * Alert statistics interface for dashboard visualization
 */
export interface AlertStatistics {
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  daily: Record<string, number>;
  total: number;
}

/**
 * Get all alerts with optional filtering
 * 
 * @param limit Maximum number of alerts to return
 * @param offset Pagination offset
 * @param severity Optional severity filter
 * @param acknowledged Optional acknowledgment status filter
 * @returns Promise with array of alerts
 */
export const getAlerts = async (
  limit = 100,
  offset = 0,
  severity?: string,
  acknowledged?: boolean
): Promise<Alert[]> => {
  try {
    // Build query parameters
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    
    if (severity) {
      params.append('severity', severity);
    }
    
    if (acknowledged !== undefined) {
      params.append('acknowledged', acknowledged.toString());
    }
    
    const response = await axios.get<Alert[]>(
      `${API_URL}?${params.toString()}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return [];
  }
};

/**
 * Get alert statistics for dashboard visualization
 * 
 * @param days Number of days to include in statistics
 * @returns Promise with alert statistics
 */
export const getAlertStatistics = async (days = 7): Promise<AlertStatistics> => {
  try {
    const response = await axios.get<AlertStatistics>(
      `${API_URL}/statistics?days=${days}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    
    return response.data;
  } catch (error) {
    console.error('Error fetching alert statistics:', error);
    return {
      by_severity: {},
      by_status: {},
      daily: {},
      total: 0
    };
  }
};

/**
 * Get a specific alert by ID
 * 
 * @param alertId ID of the alert to retrieve
 * @returns Promise with the alert or null if not found
 */
export const getAlertById = async (alertId: number): Promise<Alert | null> => {
  try {
    const response = await axios.get<Alert>(
      `${API_URL}/${alertId}`,
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    
    return response.data;
  } catch (error) {
    console.error(`Error fetching alert ${alertId}:`, error);
    return null;
  }
};

/**
 * Acknowledge an alert
 * 
 * @param alertId ID of the alert to acknowledge
 * @returns Promise with the updated alert or null if failed
 */
export const acknowledgeAlert = async (alertId: number): Promise<Alert | null> => {
  try {
    const response = await axios.patch<Alert>(
      `${API_URL}/${alertId}`,
      { acknowledged: true },
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    
    return response.data;
  } catch (error) {
    console.error(`Error acknowledging alert ${alertId}:`, error);
    return null;
  }
};

/**
 * Acknowledge all alerts, optionally filtered by severity
 * 
 * @param severity Optional severity filter
 * @returns Promise with the number of acknowledged alerts
 */
export const acknowledgeAllAlerts = async (severity?: string): Promise<number> => {
  try {
    const params = new URLSearchParams();
    
    if (severity) {
      params.append('severity', severity);
    }
    
    const response = await axios.post<{ acknowledged: number }>(
      `${API_URL}/acknowledge-all?${params.toString()}`,
      {},
      { headers: { Authorization: `Bearer ${getToken()}` } }
    );
    
    return response.data.acknowledged;
  } catch (error) {
    console.error('Error acknowledging all alerts:', error);
    return 0;
  }
};
