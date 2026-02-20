import api from './api';

export const ragService = {
  query: async (query, contractId = null) => {
    const response = await api.post('/api/rag/query', {
      query,
      contract_id: contractId || undefined,
    });
    return response.data;
  },

  askContract: async (contractId, question) => {
    const response = await api.post(
      `/api/rag/contract/${contractId}/ask?question=${encodeURIComponent(question)}`
    );
    return response.data;
  },
};

