import { Link, useLocation } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '../../store/authSlice';
import { toggleSidebar, toggleTheme } from '../../store/uiSlice';
import { Menu, LogOut, Settings, User, Moon, Sun } from 'lucide-react';
import { Menu as HeadlessMenu, MenuButton, MenuItems, MenuItem } from '@headlessui/react';
import Button from '../ui/Button';
import Logo from '../ui/Logo';

function Navbar() {
  const dispatch = useDispatch();
  const location = useLocation();
  const { isAuthenticated, user } = useSelector(state => state.auth);
  const { theme } = useSelector(state => state.ui);

  const handleLogout = () => {
    dispatch(logout());
  };

  return (
    <nav
      className="shrink-0 px-4 py-3 border-b sticky top-0 z-40 backdrop-blur-md"
      style={{ borderColor: 'var(--color-neutral-200)', backgroundColor: 'var(--glass-bg)' }}
    >
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-3">
          {isAuthenticated && (
            <>
              <button
                onClick={() => dispatch(toggleSidebar())}
                className="lg:hidden p-2 rounded-md hover:bg-neutral-100"
                aria-label="Toggle mobile sidebar"
              >
                <Menu className="w-5 h-5" style={{ color: 'var(--color-neutral-600)' }} />
              </button>
            </>
          )}
          {!isAuthenticated && (
            <Link to="/" className="flex items-center gap-2">
              <Logo size="md" />
              <span className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>Legalyze</span>
            </Link>
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => dispatch(toggleTheme())}
            className="p-2 rounded-md hover:bg-neutral-100"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-5 h-5" style={{ color: 'var(--color-primary-500)' }} />
            ) : (
              <Moon className="w-5 h-5" style={{ color: 'var(--color-neutral-600)' }} />
            )}
          </button>
          {isAuthenticated ? (
            <HeadlessMenu as="div" className="relative">
              <MenuButton className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-neutral-100">
                <div className="w-8 h-8 rounded-md flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary-100)' }}>
                  <User className="w-5 h-5" style={{ color: 'var(--color-primary-600)' }} />
                </div>
                <span className="text-sm font-medium hidden sm:block" style={{ color: 'var(--color-neutral-700)' }}>
                  {user?.name || 'User'}
                </span>
              </MenuButton>
              <MenuItems 
                anchor="bottom end"
                className="mt-2 w-56 overflow-hidden rounded-md border bg-white shadow-sm focus:outline-hidden"
                style={{ borderColor: 'var(--color-neutral-200)', backgroundColor: 'var(--glass-bg)' }}
              >
                <MenuItem>
                  <Link
                    to="/profile"
                    className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-neutral-50"
                    style={{ color: 'var(--color-neutral-700)' }}
                  >
                    <User className="w-4 h-4" />
                    Profile
                  </Link>
                </MenuItem>
                <MenuItem>
                  <Link
                    to="/settings"
                    className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-neutral-50"
                    style={{ color: 'var(--color-neutral-700)' }}
                  >
                    <Settings className="w-4 h-4" />
                    Settings
                  </Link>
                </MenuItem>
                <div style={{ borderTop: 'var(--border-thin) solid var(--color-neutral-200)' }} />
                <MenuItem>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-red-50"
                    style={{ color: 'var(--color-error)' }}
                  >
                    <LogOut className="w-4 h-4" />
                    Logout
                  </button>
                </MenuItem>
              </MenuItems>
            </HeadlessMenu>
          ) : (
            <div className="flex items-center gap-3">
              {location.pathname === '/about' ? (
                <Link to="/">
                  <Button variant="ghost" size="sm">Home</Button>
                </Link>
              ) : (
                <Link to="/about">
                  <Button variant="ghost" size="sm">About</Button>
                </Link>
              )}
              <Link to="/login">
                <Button variant="ghost" size="sm">Login</Button>
              </Link>
              <Link to="/register">
                <Button size="sm">Get Started</Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

