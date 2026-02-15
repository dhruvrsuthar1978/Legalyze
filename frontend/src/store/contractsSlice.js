import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  contracts: [],
  selectedContract: null,
  loading: false,
  error: null,
  uploadProgress: 0,
};

const contractsSlice = createSlice({
  name: 'contracts',
  initialState,
  reducers: {
    fetchContractsStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    fetchContractsSuccess: (state, action) => {
      state.loading = false;
      state.contracts = action.payload;
    },
    fetchContractsFailure: (state, action) => {
      state.loading = false;
      state.error = action.payload;
    },
    selectContract: (state, action) => {
      state.selectedContract = action.payload;
    },
    uploadStart: (state) => {
      state.loading = true;
      state.uploadProgress = 0;
      state.error = null;
    },
    uploadProgress: (state, action) => {
      state.uploadProgress = action.payload;
    },
    uploadSuccess: (state, action) => {
      state.loading = false;
      state.uploadProgress = 100;
      state.contracts.unshift(action.payload);
    },
    uploadFailure: (state, action) => {
      state.loading = false;
      state.uploadProgress = 0;
      state.error = action.payload;
    },
    deleteContract: (state, action) => {
      state.contracts = state.contracts.filter(c => c.id !== action.payload);
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  fetchContractsStart,
  fetchContractsSuccess,
  fetchContractsFailure,
  selectContract,
  uploadStart,
  uploadProgress,
  uploadSuccess,
  uploadFailure,
  deleteContract,
  clearError,
} = contractsSlice.actions;

export default contractsSlice.reducer;