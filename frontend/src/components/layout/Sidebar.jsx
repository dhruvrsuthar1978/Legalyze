import { Link, useLocation } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { toggleSidebar } from '../../store/uiSlice';
import { 
  Home, 
  Upload, 
  FileText, 
  FileCheck, 
  Users, 
  Settings,
  PenTool,
  User,
  X
} from 'lucide-react';

function Sidebar() {
  const location = useLocation();
  const dispatch = useDispatch();
  const { sidebarOpen } = useSelector(state => state.ui);
  const { user } = useSelector(state => state.auth);

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/upload', label: 'Upload Contract', icon: Upload },
    { path: '/generate', label: 'Generate Contract', icon: FileCheck },
    { path: '/compare', label: 'Compare Contracts', icon: FileText },
    { path: '/signature', label: 'Digital Signature', icon: PenTool },
    { path: '/profile', label: 'Profile & History', icon: User },
  ];

  if ((user?.role || '').toLowerCase() === 'admin') {
    menuItems.push({ path: '/admin', label: 'Admin Panel', icon: Users });
  }

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/30 backdrop-blur-sm z-30 lg:hidden"
          onClick={() => dispatch(toggleSidebar())}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed lg:sticky top-0 left-0 h-screen transition-transform duration-300 z-40 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } w-72 flex flex-col`}
        style={{ 
          borderRight: 'var(--border-thin) solid var(--color-neutral-200)',
          backgroundColor: 'var(--color-bg-primary)'
        }}
      >
        {/* Brand Header - Fixed at top */}
        <div className="flex-shrink-0 px-6 py-6" style={{ borderBottom: 'var(--border-thin) solid var(--color-neutral-200)' }}>
          <div className="flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[var(--color-primary-600)] to-[var(--color-accent-blue)] rounded-xl flex items-center justify-center shadow-lg">
                <span className="text-white font-bold text-xl">L</span>
              </div>
              <div>
                <span className="text-xl font-bold block gradient-text-animated">Legalyze</span>
                <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>AI Contract Analysis</span>
              </div>
            </Link>
            <button
              onClick={() => dispatch(toggleSidebar())}
              className="lg:hidden p-2 hover:bg-[var(--color-neutral-100)] rounded-lg transition-colors"
            >
              <X className="w-5 h-5" style={{ color: 'var(--color-neutral-600)' }} />
            </button>
          </div>
        </div>

        {/* Scrollable Navigation */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-2">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-3 px-4 py-3.5 rounded-xl smooth-transition font-medium ${
                    isActive
                      ? 'bg-gradient-to-r from-[var(--color-primary-600)] to-[var(--color-accent-blue)] text-white shadow-lg'
                      : 'hover:bg-[var(--color-neutral-100)]'
                  }`}
                  style={!isActive ? { color: 'var(--color-text-primary)' } : {}}
                >
                  <Icon className="w-5 h-5" style={{ color: isActive ? 'white' : 'var(--color-neutral-600)' }} />
                  <span className="text-sm">{item.label}</span>
                </Link>
              );
            })}
        </nav>

        {/* Footer - Fixed at bottom */}
        <div className="flex-shrink-0 px-3 py-4" style={{ borderTop: 'var(--border-thin) solid var(--color-neutral-200)' }}>
          <Link
            to="/settings"
            className="flex items-center gap-3 px-4 py-3.5 rounded-xl hover:bg-[var(--color-neutral-100)] smooth-transition font-medium text-sm"
            style={{ color: 'var(--color-text-primary)' }}
          >
            <Settings className="w-5 h-5" style={{ color: 'var(--color-neutral-600)' }} />
            <span>Settings</span>
          </Link>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
