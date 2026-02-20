import api from './api';

export const generationService = {
  adhocPreview: async (payload) => {
    const response = await api.post('/api/generate/adhoc/preview', payload);
    return response.data;
  },

  getTemplates: async () => {
    const response = await api.get('/api/generate/templates');
    return response.data;
  },

  previewFromTemplate: async (templateId, data) => {
    const response = await api.post('/api/generate/templates/preview', {
      template_id: templateId,
      data,
    });
    return response.data;
  },

  generateFromContract: async (contractId, format = 'pdf', includeSummary = true) => {
    const response = await api.post(
      `/api/generate/${contractId}?format=${encodeURIComponent(format)}&include_summary=${includeSummary}`
    );
    return response.data;
  },

  previewFromContract: async (contractId) => {
    const response = await api.get(`/api/generate/${contractId}/preview`);
    return response.data;
  },

  getVersions: async (contractId, page = 1, limit = 10) => {
    const response = await api.get(
      `/api/generate/${contractId}/versions?page=${page}&limit=${limit}`
    );
    return response.data;
  },

  downloadVersion: async (contractId, versionId) => {
    const response = await api.get(`/api/generate/${contractId}/versions/${versionId}/download`);
    return response.data;
  },

  deleteVersion: async (contractId, versionId) => {
    const response = await api.delete(`/api/generate/${contractId}/versions/${versionId}`);
    return response.data;
  }
};
