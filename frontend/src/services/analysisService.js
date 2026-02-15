import api from './api';

export const analysisService = {
  // Run analysis for a contract
  runAnalysis: async (contractId, mode = 'async') => {
    const response = await api.post(`/api/analysis/${contractId}/run?mode=${mode}`);
    return response.data;
  },

  // Get full analysis result for a contract
  getClauseAnalysis: async (contractId) => {
    const response = await api.get(`/api/analysis/${contractId}`);
    return response.data;
  },

  // Get summary analysis
  getSummary: async (contractId) => {
    const response = await api.get(`/api/analysis/${contractId}/summary`);
    return response.data;
  },

  // Get clauses by risk (Low | Medium | High)
  getClausesByRisk: async (contractId, level, clauseType = null) => {
    let url = `/api/analysis/${contractId}/risk?level=${encodeURIComponent(level)}`;
    if (clauseType) {
      url += `&clause_type=${encodeURIComponent(clauseType)}`;
    }
    const response = await api.get(url);
    return response.data;
  },

  // Get specific clause by clause ID
  getClause: async (contractId, clauseId) => {
    const response = await api.get(`/api/analysis/${contractId}/clauses/${clauseId}`);
    return response.data;
  },

  // Re-run analysis
  reanalyze: async (contractId) => {
    const response = await api.post(`/api/analysis/${contractId}/reanalyze`);
    return response.data;
  }
};
