import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

function DashboardLayout() {
  return (
    <div className="min-h-screen flex" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Navbar />
        <main className="flex-1 p-8 max-w-[1600px] mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;