import api from './api';

export const contractService = {
  // Upload contract
  uploadContract: async (file, title, description) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) formData.append('description', description);

    const response = await api.post('/api/contracts/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Chunked upload helpers
  initiateChunkedUpload: async (filename, totalSize) => {
    const response = await api.post('/api/contracts/upload/initiate', null, {
      params: { filename, total_size: totalSize }
    });
    return response.data;
  },

  uploadChunk: async (uploadId, chunkIndex, chunkFile) => {
    const formData = new FormData();
    formData.append('chunk', chunkFile);

    // retry logic
    const maxRetries = 3;
    let attempt = 0;
    let lastErr = null;

    while (attempt < maxRetries) {
      try {
        const response = await api.post(`/api/contracts/upload/${uploadId}/part`, formData, {
          params: { chunk_index: chunkIndex },
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
      } catch (err) {
        lastErr = err;
        attempt += 1;
        // exponential backoff
        await new Promise(res => setTimeout(res, 500 * Math.pow(2, attempt)));
      }
    }

    throw lastErr;
  },

  completeChunkedUpload: async (uploadId, filename, title, tags) => {
    const params = { filename };
    if (title) params.title = title;
    if (tags) params.tags = tags.join(',');
    const response = await api.post(`/api/contracts/upload/${uploadId}/complete`, null, { params });
    return response.data;
  },

  getUploadStatus: async (uploadId) => {
    const response = await api.get(`/api/contracts/upload/${uploadId}/status`);
    return response.data;
  },

  // Get all contracts
  getContracts: async (skip = 0, limit = 100) => {
    const page = Math.floor(skip / Math.max(limit, 1)) + 1;
    const response = await api.get(`/api/contracts/?page=${page}&limit=${limit}`);
    return response.data;
  },

  // Get contract statistics
  getContractStats: async () => {
    const response = await api.get('/api/contracts/stats');
    return response.data;
  },

  // Get contract by ID
  getContract: async (contractId) => {
    const response = await api.get(`/api/contracts/${contractId}`);
    return response.data;
  },

  // Get contract analysis
  getContractAnalysis: async (contractId) => {
    const response = await api.get(`/api/analysis/${contractId}`);
    return response.data;
  },

  // Get processing status
  getProcessingStatus: async (contractId) => {
    const response = await api.get(`/api/contracts/${contractId}`);
    return {
      status: response.data?.analysis_status || 'pending',
      analysis_status: response.data?.analysis_status || 'pending',
      progress: null,
      contract: response.data
    };
  },

  // Update contract
  updateContract: async (contractId, updateData) => {
    const response = await api.patch(`/api/contracts/${contractId}`, updateData);
    return response.data;
  },

  // Delete contract
  deleteContract: async (contractId) => {
    const response = await api.delete(`/api/contracts/${contractId}`);
    return response.data;
  },

  // Compare contracts
  compareContracts: async (a, b) => {
    const formData = new FormData();
    formData.append('file1', a);
    formData.append('file2', b);

    const response = await api.post('/api/contracts/compare', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },

  // Download contract
  downloadContract: async (contractId) => {
    const response = await api.get(`/api/contracts/${contractId}/download`);
    return response.data;
  }
};
