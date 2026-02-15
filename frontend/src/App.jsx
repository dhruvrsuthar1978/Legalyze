import { Provider } from 'react-redux';
import { RouterProvider } from 'react-router-dom';
import { useEffect } from 'react';
import store from './store';
import router from './router';
import Toast from './components/ui/Toast';
import ThemeInitializer from './components/ThemeInitializer';

function App() {
  return (
    <Provider store={store}>
      <ThemeInitializer />
      <RouterProvider router={router} />
      <Toast />
    </Provider>
  );
}

export default App;