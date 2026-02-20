import { Link, useLocation } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { toggleSidebar, toggleSidebarCollapsed } from '../../store/uiSlice';
import { 
  Home, 
  Upload, 
  FileText, 
  FileCheck, 
  Users, 
  Settings,
  PenTool,
  User,
  X,
  MessageSquare,
  ChevronsLeft,
  ChevronsRight
} from 'lucide-react';
import Logo from '../ui/Logo';

function Sidebar() {
  const location = useLocation();
  const dispatch = useDispatch();
  const { sidebarOpen, sidebarCollapsed } = useSelector(state => state.ui);
  const { user } = useSelector(state => state.auth);
  const role = (user?.role || 'user').toLowerCase();

  const menuItems = [
    { path: '/dashboard', label: 'Dashboard', icon: Home },
    { path: '/upload', label: 'Upload Contract', icon: Upload },
    { path: '/assistant', label: 'Contract Assistant', icon: MessageSquare },
    { path: '/signature', label: 'Digital Signature', icon: PenTool },
    { path: '/profile', label: 'Profile & History', icon: User },
  ];

  if (['admin', 'lawyer', 'client'].includes(role)) {
    menuItems.splice(2, 0, { path: '/generate', label: 'Generate Contract', icon: FileCheck });
  }

  if (['admin', 'lawyer'].includes(role)) {
    menuItems.splice(3, 0, { path: '/compare', label: 'Compare Contracts', icon: FileText });
  }

  if (role === 'admin') {
    menuItems.push({ path: '/admin', label: 'Admin Panel', icon: Users });
  }

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/30 z-30 lg:hidden"
          onClick={() => dispatch(toggleSidebar())}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed lg:sticky top-0 left-0 h-screen transition-transform duration-300 z-40 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        } w-72 ${sidebarCollapsed ? 'lg:w-20' : 'lg:w-72'} flex flex-col transition-[width] duration-300`}
        style={{ 
          borderRight: 'var(--border-thin) solid var(--color-neutral-200)',
          backgroundColor: 'var(--color-bg-primary)'
        }}
      >
        {/* Brand Header - Fixed at top */}
        <div
          className={`flex-shrink-0 py-5 ${sidebarCollapsed ? 'px-3' : 'px-6'}`}
          style={{ borderBottom: 'var(--border-thin) solid var(--color-neutral-200)' }}
        >
          <div className="flex items-center justify-between">
            <div className={`flex ${sidebarCollapsed ? 'items-center justify-center w-full' : 'items-center gap-2 min-w-0'}`}>
              <Link to="/" className={`flex items-center ${sidebarCollapsed ? '' : 'gap-3'} min-w-0`}>
                <Logo size="md" />
                <div className={`${sidebarCollapsed ? 'lg:hidden' : 'block'} min-w-0`}>
                  <span className="text-xl font-bold block" style={{ color: 'var(--color-text-primary)' }}>Legalyze</span>
                  <span className="text-xs" style={{ color: 'var(--color-text-tertiary)' }}>
                    {role === 'admin' ? 'Admin Workspace' : role === 'lawyer' ? 'Lawyer Workspace' : role === 'client' ? 'Client Workspace' : 'AI Contract Analysis'}
                  </span>
                </div>
              </Link>
              <button
                onClick={() => dispatch(toggleSidebarCollapsed())}
                className={`hidden lg:inline-flex h-9 w-9 items-center justify-center rounded-md border hover:bg-[var(--color-neutral-100)] transition-colors ${
                  sidebarCollapsed ? 'ml-2' : ''
                }`}
                style={{ borderColor: 'var(--color-neutral-200)', color: 'var(--color-neutral-600)' }}
                title={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                aria-label="Toggle sidebar collapse"
              >
                {sidebarCollapsed ? (
                  <ChevronsRight className="w-4 h-4" />
                ) : (
                  <ChevronsLeft className="w-4 h-4" />
                )}
              </button>
            </div>
            <button
              onClick={() => dispatch(toggleSidebar())}
              className="lg:hidden p-2 hover:bg-[var(--color-neutral-100)] rounded-md transition-colors"
              aria-label="Close sidebar"
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
                  className={`flex items-center ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : 'gap-3 px-4'} py-3.5 rounded-md smooth-transition font-medium ${
                    isActive
                      ? 'text-white'
                      : 'hover:bg-[var(--color-neutral-100)]'
                  }`}
                  style={isActive ? { backgroundColor: 'var(--color-primary-600)' } : { color: 'var(--color-text-primary)' }}
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  <Icon className="w-5 h-5" style={{ color: isActive ? 'white' : 'var(--color-neutral-600)' }} />
                  <span className={`text-sm ${sidebarCollapsed ? 'lg:hidden' : ''}`}>{item.label}</span>
                </Link>
              );
            })}
        </nav>

        {/* Footer - Fixed at bottom */}
        <div className="flex-shrink-0 px-3 py-4" style={{ borderTop: 'var(--border-thin) solid var(--color-neutral-200)' }}>
          <Link
            to="/settings"
            className={`flex items-center ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : 'gap-3 px-4'} py-3.5 rounded-md hover:bg-[var(--color-neutral-100)] smooth-transition font-medium text-sm`}
            style={{ color: 'var(--color-text-primary)' }}
            title={sidebarCollapsed ? 'Settings' : undefined}
          >
            <Settings className="w-5 h-5" style={{ color: 'var(--color-neutral-600)' }} />
            <span className={sidebarCollapsed ? 'lg:hidden' : ''}>Settings</span>
          </Link>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;
