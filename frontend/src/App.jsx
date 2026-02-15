import { Provider } from 'react-redux';
import { RouterProvider } from 'react-router-dom';
import { useEffect } from 'react';
import store from './store';
import router from './router';
import Toast from './components/ui/Toast';
import ThemeInitializer from './components/ThemeInitializer';
import { setUser, logout } from './store/authSlice';
import { authService } from './services/authService';

function App() {
  useEffect(() => {
    const token = authService.getToken();
    if (!token) return;

    authService
      .getProfile()
      .then((profile) => {
        store.dispatch(setUser(profile));
      })
      .catch(() => {
        store.dispatch(logout());
      });
  }, []);

  return (
    <Provider store={store}>
      <ThemeInitializer />
      <main id="main" role="main">
        <RouterProvider router={router} />
      </main>
      <Toast />
    </Provider>
  );
}

export default App;
