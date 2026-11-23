import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

export const reportAnalyzerApi = {
  /**
   * Submit a medical report (PDF or Image) for deterministic analysis & timeline syncing.
   * Note: Do NOT set explicit Content-Type: multipart/form-data; axios handles boundary automatically.
   */
  analyzeReport: (formData, onProgress) => {
    return client.post('/api/v1/report-analyzer/analyze', formData, {
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
  },

  /**
   * Retrieve historical patient medical timeline using the 3-table SQL JOIN:
   * Mst_Patients -> HC_Patient_Health_Timeline -> HC_Timeline_Parameters
   * Supports optional parameterId filter for dynamic historical graphing.
   */
  getPatientTimeline: (patientId, parameterId = null) => {
    const url = parameterId
      ? `/api/v1/report-analyzer/timeline/${patientId}?parameter_id=${parameterId}`
      : `/api/v1/report-analyzer/timeline/${patientId}`;
    return client.get(url);
  },

  /**
   * Fetch aggregate summary metrics for the dashboard top cards.
   */
  getDashboardMetrics: () => {
    return client.get('/api/v1/report-analyzer/metrics');
  },

  /**
   * Fetch all 63 registered master clinical parameters from HC_Timeline_Parameters.
   */
  getMasterParameters: () => {
    return client.get('/api/v1/report-analyzer/parameters');
  },

  /**
   * Fetch registered patients from Mst_Patients for safe patient linking & timeline review.
   */
  getPatients: () => {
    return client.get('/api/v1/report-analyzer/patients');
  },

  /**
   * List available sample test reports.
   */
  getSamples: () => {
    return client.get('/api/v1/report-analyzer/samples');
  },

  /**
   * Download sample test report file as Blob.
   */
  fetchSampleBlob: (filename) => {
    return client.get(`/api/v1/report-analyzer/samples/${encodeURIComponent(filename)}`, {
      responseType: 'blob',
    });
  },

  /**
   * Check backend health status.
   */
  checkHealth: async () => {
    try {
      const res = await client.get('/api/health');
      return res.data;
    } catch {
      try {
        const fallback = await client.get('/api/v1/health');
        return fallback.data;
      } catch {
        return null;
      }
    }
  },
};

export default reportAnalyzerApi;
