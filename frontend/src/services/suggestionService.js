import api from './api';

export const suggestionService = {
  getSuggestions: async (contractId, filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.riskLevel) params.append('risk_level', filters.riskLevel);
    if (filters.clauseType) params.append('clause_type', filters.clauseType);

    const query = params.toString();
    const url = `/api/suggestions/${contractId}${query ? `?${query}` : ''}`;
    const response = await api.get(url);
    return response.data;
  },

  acceptSuggestion: async (contractId, clauseId) => {
    const response = await api.patch(`/api/suggestions/${contractId}/clause/${clauseId}/accept`);
    return response.data;
  },

  rejectSuggestion: async (contractId, clauseId) => {
    const response = await api.patch(`/api/suggestions/${contractId}/clause/${clauseId}/reject`);
    return response.data;
  },
};

