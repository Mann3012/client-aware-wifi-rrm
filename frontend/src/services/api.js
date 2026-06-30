import axios from 'axios';
import { API_BASE_URL, USE_MOCK_DATA, USE_DEMO_MODE } from '../config';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

let demoCounter = 0;

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error);
    return Promise.reject(error);
  }
);

// Mock Data Generators (matching exact backend schemas)
const getMockTelemetry = () => ([{
  id: 1,
  timestamp: new Date().toISOString(),
  ap_id: "AP-MOCK-001",
  channel: 36,
  rssi: -65.5,
  snr: 30.5,
  noise_floor: -96.0,
  airtime_utilization: 0.45,
  retry_rate: 0.05,
  client_count: 12,
  qoe_score: 85.0,
  qoe_category: "Excellent",
  interference_type: "None"
}]);

const getMockAlerts = () => ([{
  id: 1,
  timestamp: new Date().toISOString(),
  ap_id: "AP-MOCK-001",
  alert_type: "retry_spike",
  metric: "retry_rate",
  value: 0.15,
  threshold: 0.10,
  description: "High retry rate detected"
}]);

const getMockRecommendations = () => ([{
  id: 1,
  timestamp: new Date().toISOString(),
  ap_id: "AP-MOCK-001",
  action: "CHANNEL_CHANGE",
  current_value: "36",
  recommended_value: "44",
  confidence: 0.95,
  reason: "High interference on channel 36"
}]);

const getMockAPStatus = () => ([{
  ap_id: "AP-MOCK-001",
  channel: 36,
  client_count: 12,
  status: "Healthy",
  active_alert_count: 0,
  recent_recommendation: "None"
}]);

export const fetchTelemetry = async (ap_id = null, limit = 100) => {
  if (USE_MOCK_DATA) return getMockTelemetry();
  const params = { limit };
  if (ap_id) params.ap_id = ap_id;
  const res = await apiClient.get('/telemetry', { params });
  
  let data = res.data;
  if (USE_DEMO_MODE && data && data.length > 0) {
    demoCounter++;
    const isInterference = demoCounter % 10 >= 5;
    
    if (isInterference) {
      data[0] = {
        ...data[0],
        interference_type: 'Microwave',
        noise_floor: -75,
        snr: 10,
        retry_rate: 0.45,
        qoe_score: 35.0,
        qoe_category: 'Poor'
      };
    }
  }
  return data;
};

export const fetchAlerts = async (ap_id = null, active_only = false, limit = 50) => {
  if (USE_MOCK_DATA) return getMockAlerts();
  
  if (USE_DEMO_MODE && demoCounter % 10 >= 5) {
    return [{ id: 999, timestamp: new Date().toISOString(), ap_id, metric: 'noise_floor', alert_type: 'interference', value: -75, threshold: -85, description: 'Microwave interference detected' }];
  }

  const params = { active_only, limit };
  if (ap_id) params.ap_id = ap_id;
  const res = await apiClient.get('/alerts', { params });
  return res.data;
};

export const fetchRecommendations = async (ap_id = null, limit = 50) => {
  if (USE_MOCK_DATA) return getMockRecommendations();

  if (USE_DEMO_MODE && demoCounter % 10 >= 5) {
    return [{
      id: 999,
      timestamp: new Date().toISOString(),
      ap_id,
      action: 'CHANNEL_CHANGE',
      reason: 'Microwave interference detected causing severe QoE drop.',
      confidence: 0.95,
      current_value: '36',
      recommended_value: '44'
    }];
  }

  const params = { limit };
  if (ap_id) params.ap_id = ap_id;
  const res = await apiClient.get('/recommendations', { params });
  return res.data;
};

export const fetchAPStatus = async () => {
  if (USE_MOCK_DATA) return getMockAPStatus();
  const res = await apiClient.get('/ap-status');
  return res.data;
};

export default apiClient;
