import axios from 'axios';

// In production (Cloud Run), API is served from same origin at /api
// In development, proxy through Vite to localhost:8000
const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export default api;
export { API_BASE };
