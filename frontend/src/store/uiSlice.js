import { createSlice } from '@reduxjs/toolkit';

const getInitialTheme = () => {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme) return savedTheme;
  
  // Check system preference
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
};

const initialState = {
  toast: null,
  modal: null,
  sidebarOpen: true,
  theme: getInitialTheme(),
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    showToast: (state, action) => {
      state.toast = action.payload;
    },
    hideToast: (state) => {
      state.toast = null;
    },
    showModal: (state, action) => {
      state.modal = action.payload;
    },
    hideModal: (state) => {
      state.modal = null;
    },
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    setSidebarOpen: (state, action) => {
      state.sidebarOpen = action.payload;
    },
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
      localStorage.setItem('theme', state.theme);
      document.documentElement.classList.toggle('dark', state.theme === 'dark');
    },
    setTheme: (state, action) => {
      state.theme = action.payload;
      localStorage.setItem('theme', action.payload);
      document.documentElement.classList.toggle('dark', action.payload === 'dark');
    },
  },
});

export const {
  showToast,
  hideToast,
  showModal,
  hideModal,
  toggleSidebar,
  setSidebarOpen,
  toggleTheme,
  setTheme,
} = uiSlice.actions;

export default uiSlice.reducer;