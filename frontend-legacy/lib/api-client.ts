import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api', // Update with your FastAPI URL
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;