import api from './api';

export const analysisService = {
  // Get contract clauses
  getContractClauses: async (contractId, clauseType = null, riskLevel = null) => {
    let url = `/api/v1/analysis/contract/${contractId}/clauses`;
    const params = new URLSearchParams();
    
    if (clauseType) params.append('clause_type', clauseType);
    if (riskLevel) params.append('risk_level', riskLevel);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    const response = await api.get(url);
    return response.data;
  },

  // Get clause analysis
  getClauseAnalysis: async (contractId) => {
    const response = await api.get(`/api/v1/analysis/contract/${contractId}/analysis`);
    return response.data;
  },

  // Get specific clause
  getClause: async (clauseId) => {
    const response = await api.get(`/api/v1/analysis/clause/${clauseId}`);
    return response.data;
  },

  // Re-analyze clause
  reanalyzeClause: async (clauseId) => {
    const response = await api.post(`/api/v1/analysis/clause/${clauseId}/reanalyze`);
    return response.data;
  },

  // Get risk distribution stats
  getRiskStats: async () => {
    const response = await api.get('/api/v1/analysis/stats/risk-distribution');
    return response.data;
  }
};