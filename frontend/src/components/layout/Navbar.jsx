import { Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { logout } from '../../store/authSlice';
import { toggleSidebar, toggleTheme } from '../../store/uiSlice';
import { Menu, LogOut, Settings, User, Moon, Sun } from 'lucide-react';
import { Menu as HeadlessMenu, MenuButton, MenuItems, MenuItem } from '@headlessui/react';
import Button from '../ui/Button';

function Navbar() {
  const dispatch = useDispatch();
  const { isAuthenticated, user } = useSelector(state => state.auth);
  const { theme } = useSelector(state => state.ui);

  const handleLogout = () => {
    dispatch(logout());
  };

  return (
    <nav className="flex-shrink-0 px-6 py-4 backdrop-blur-md" style={{ borderBottom: 'var(--border-thin) solid var(--color-neutral-200)', backgroundColor: 'var(--color-bg-primary)' }}>
      <div className="flex items-center justify-between max-w-[1600px] mx-auto">
        <div className="flex items-center gap-4">
          {isAuthenticated && (
            <button
              onClick={() => dispatch(toggleSidebar())}
              className="lg:hidden p-2 hover:bg-[var(--color-neutral-100)] rounded-lg smooth-transition"
            >
              <Menu className="w-5 h-5" style={{ color: 'var(--color-neutral-600)' }} />
            </button>
          )}
          {!isAuthenticated && (
            <Link to="/" className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[var(--color-primary-600)] to-[var(--color-accent-blue)] rounded-xl flex items-center justify-center shadow-md">
                <span className="text-white font-bold text-xl">L</span>
              </div>
              <span className="text-xl font-bold gradient-text">Legalyze</span>
            </Link>
          )}
        </div>

        <div className="flex items-center gap-4">
          <button
            onClick={() => dispatch(toggleTheme())}
            className="p-2.5 rounded-xl hover:bg-[var(--color-neutral-100)] smooth-transition"
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
              <MenuButton className="flex items-center gap-3 px-4 py-2 rounded-xl hover:bg-[var(--color-neutral-100)] smooth-transition">
                <div className="w-9 h-9 bg-gradient-to-br from-[var(--color-primary-100)] to-[var(--color-primary-200)] rounded-lg flex items-center justify-center">
                  <User className="w-5 h-5" style={{ color: 'var(--color-primary-600)' }} />
                </div>
                <span className="text-sm font-semibold hidden sm:block" style={{ color: 'var(--color-neutral-700)' }}>
                  {user?.name || 'User'}
                </span>
              </MenuButton>
              <MenuItems 
                anchor="bottom end"
                className="floating-island mt-2 w-56 overflow-hidden focus:outline-hidden"
              >
                <MenuItem>
                  <Link
                    to="/profile"
                    className="flex items-center gap-3 px-4 py-3 text-sm font-medium hover:bg-[var(--color-neutral-50)] smooth-transition"
                    style={{ color: 'var(--color-neutral-700)' }}
                  >
                    <User className="w-4 h-4" />
                    Profile
                  </Link>
                </MenuItem>
                <MenuItem>
                  <Link
                    to="/settings"
                    className="flex items-center gap-3 px-4 py-3 text-sm font-medium hover:bg-[var(--color-neutral-50)] smooth-transition"
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
                    className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium hover:bg-red-50 smooth-transition"
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