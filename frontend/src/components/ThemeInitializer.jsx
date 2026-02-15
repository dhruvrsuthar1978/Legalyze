import { useEffect } from 'react';
import { useSelector } from 'react-redux';

function ThemeInitializer() {
  const theme = useSelector(state => state.ui.theme);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  return null;
}

export default ThemeInitializer;