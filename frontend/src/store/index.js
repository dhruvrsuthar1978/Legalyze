import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import contractsReducer from './contractsSlice';
import uiReducer from './uiSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    contracts: contractsReducer,
    ui: uiReducer,
  },
});

export default store;