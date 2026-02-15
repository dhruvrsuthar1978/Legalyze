import api from './api';

export const authService = {
  // Register new user
  register: async (userData) => {
    const response = await api.post('/api/v1/auth/register', userData);
    return response.data;
  },

  // Login user
  login: async (credentials) => {
    const response = await api.post('/api/v1/auth/login', credentials);
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
    }
    return response.data;
  },

  // Get current user profile
  getProfile: async () => {
    const response = await api.get('/api/v1/auth/me');
    return response.data;
  },

  // Update user profile
  updateProfile: async (userData) => {
    const response = await api.put('/api/v1/auth/me', userData);
    return response.data;
  },

  // Change password
  changePassword: async (passwordData) => {
    const response = await api.post('/api/v1/auth/change-password', passwordData);
    return response.data;
  },

  // Logout
  logout: () => {
    localStorage.removeItem('token');
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },

  // Get stored token
  getToken: () => {
    return localStorage.getItem('token');
  }
};