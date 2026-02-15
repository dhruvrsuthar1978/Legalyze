import api from './api';

export const generationService = {
  adhocPreview: async (payload) => {
    const response = await api.post('/api/generate/adhoc/preview', payload);
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
  }
};
