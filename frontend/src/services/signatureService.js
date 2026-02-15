import api from './api';

export const signatureService = {
  signContract: async (contractId, versionId = null) => {
    const params = new URLSearchParams();
    if (versionId) params.append('version_id', versionId);

    const response = await api.post(`/api/signatures/${contractId}/sign${params.toString() ? `?${params.toString()}` : ''}`);
    return response.data;
  },

  verifySignature: async (contractId, versionId = null) => {
    const params = new URLSearchParams();
    if (versionId) params.append('version_id', versionId);

    const response = await api.post(`/api/signatures/${contractId}/verify${params.toString() ? `?${params.toString()}` : ''}`);
    return response.data;
  },

  getSignatureInfo: async (contractId) => {
    const response = await api.get(`/api/signatures/${contractId}`);
    return response.data;
  },

  requestCountersign: async (contractId, payload) => {
    const response = await api.post(`/api/signatures/${contractId}/countersign/request`, payload);
    return response.data;
  },

  getCountersignStatus: async (contractId) => {
    const response = await api.get(`/api/signatures/${contractId}/countersign/status`);
    return response.data;
  },

  revokeSignature: async (contractId, reason = null) => {
    const url = reason ? `/api/signatures/${contractId}/revoke?reason=${encodeURIComponent(reason)}` : `/api/signatures/${contractId}/revoke`;
    const response = await api.delete(url);
    return response.data;
  },
};
