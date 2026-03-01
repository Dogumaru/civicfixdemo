import axios from 'axios';

// In production (Vercel), VITE_API_URL points to the Render backend.
// In dev, it defaults to '/api' which Vite proxies to the backend.
const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
});

// ── Reports ───────────────────────────────────────────────
export async function uploadReport(file, latitude, longitude, address, neighborhood, reporterName) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('latitude', latitude);
  formData.append('longitude', longitude);
  if (address) formData.append('address', address);
  if (neighborhood) formData.append('neighborhood', neighborhood);
  if (reporterName) formData.append('reporter_name', reporterName);

  const res = await api.post('/reports', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function classifyOnly(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/classify', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function fetchReports(params = {}) {
  const res = await api.get('/reports', { params });
  return res.data;
}

export async function fetchReport(id) {
  const res = await api.get(`/reports/${id}`);
  return res.data;
}

export async function updateReport(id, data) {
  const res = await api.patch(`/reports/${id}`, data);
  return res.data;
}

// ── Dashboard ─────────────────────────────────────────────
export async function fetchDashboardStats() {
  const res = await api.get('/dashboard/stats');
  return res.data;
}

export async function fetchHeatmapData() {
  const res = await api.get('/dashboard/heatmap');
  return res.data;
}

export async function fetchNeighborhoods() {
  const res = await api.get('/neighborhoods');
  return res.data;
}

export default api;
