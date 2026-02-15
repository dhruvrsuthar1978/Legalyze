import api from './api';

export const ragService = {
  // Ask questions about contracts using RAG
  query: async (query, contractId = null) => {
    const response = await api.post('/api/rag/query', {
      query,
      contract_id: contractId
    });
    return response.data;
  },

  // Get contract insights
  getContractInsights: async (contractId) => {
    const response = await api.get(`/api/rag/contract/${contractId}/insights`);
    return response.data;
  },

  // Ask specific questions about a contract
  askAboutContract: async (contractId, question) => {
    const response = await api.post(`/api/rag/contract/${contractId}/ask?question=${encodeURIComponent(question)}`);
    return response.data;
  },

  // Find similar clauses
  findSimilarClauses: async (clauseText, clauseType, limit = 3) => {
    const params = new URLSearchParams({
      clause_text: clauseText,
      clause_type: clauseType,
      limit: limit.toString()
    });

    const response = await api.get(`/api/rag/similar-clauses?${params.toString()}`);
    return response.data;
  },

  // Explain legal concepts
  explainConcept: async (concept, context = null) => {
    const params = new URLSearchParams({ concept });
    if (context) params.append('context', context);

    const response = await api.post(`/api/rag/explain?${params.toString()}`);
    return response.data;
  },

  // Get knowledge base stats
  getKnowledgeBaseStats: async () => {
    const response = await api.get('/api/rag/knowledge-base/stats');
    return response.data;
  }
};