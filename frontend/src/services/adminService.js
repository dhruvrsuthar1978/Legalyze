import api from './api';

export const adminService = {
  getSystemStats: async () => {
    const response = await api.get('/stats');
    return response.data;
  },

  getSystemHealth: async () => {
    const response = await api.get('/health');
    return response.data;
  },

  getUsers: async (page = 1, limit = 20, q = '') => {
    const query = q ? `&q=${encodeURIComponent(q)}` : '';
    const response = await api.get(`/api/admin/users?page=${page}&limit=${limit}${query}`);
    return response.data;
  },

  updateUserRole: async (userId, role) => {
    const response = await api.patch(`/api/admin/users/${userId}/role?role=${encodeURIComponent(role)}`);
    return response.data;
  },

  updateUserStatus: async (userId, accountStatus) => {
    const response = await api.patch(`/api/admin/users/${userId}/status?status=${encodeURIComponent(accountStatus)}`);
    return response.data;
  },

  getAuditLogs: async (limit = 25) => {
    const response = await api.get(`/api/admin/audit-logs?limit=${limit}`);
    return response.data;
  },
};
