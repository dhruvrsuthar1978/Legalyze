import api from './api';

export const contractService = {
  // Upload contract
  uploadContract: async (file, title, description) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) formData.append('description', description);

    const response = await api.post('/api/v1/contracts/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get all contracts
  getContracts: async (skip = 0, limit = 100) => {
    const response = await api.get(`/api/v1/contracts/?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  // Get contract by ID
  getContract: async (contractId) => {
    const response = await api.get(`/api/v1/contracts/${contractId}`);
    return response.data;
  },

  // Get contract analysis
  getContractAnalysis: async (contractId) => {
    const response = await api.get(`/api/v1/contracts/${contractId}/analysis`);
    return response.data;
  },

  // Get processing status
  getProcessingStatus: async (contractId) => {
    const response = await api.get(`/api/v1/contracts/${contractId}/status`);
    return response.data;
  },

  // Update contract
  updateContract: async (contractId, updateData) => {
    const response = await api.put(`/api/v1/contracts/${contractId}`, updateData);
    return response.data;
  },

  // Delete contract
  deleteContract: async (contractId) => {
    const response = await api.delete(`/api/v1/contracts/${contractId}`);
    return response.data;
  },

  // Compare contracts
  compareContracts: async (contractId1, contractId2) => {
    const formData = new FormData();
    formData.append('contract_id1', contractId1);
    formData.append('contract_id2', contractId2);

    const response = await api.post('/api/v1/contracts/compare', formData);
    return response.data;
  },

  // Download contract
  downloadContract: async (contractId) => {
    const response = await api.get(`/api/v1/contracts/${contractId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  }
};