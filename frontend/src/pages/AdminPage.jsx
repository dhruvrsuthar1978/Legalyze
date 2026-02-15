import { Users, Activity, AlertCircle, TrendingUp } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { useSelector } from 'react-redux';
import { Navigate } from 'react-router-dom';

function AdminPage() {
  const { user } = useSelector(state => state.auth);

  // Only allow Admin users to access this page
  if (!user || (user.role || '').toLowerCase() !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }
  const stats = [
    { label: 'Total Users', value: '1,234', icon: Users, color: 'blue' },
    { label: 'Active Today', value: '89', icon: Activity, color: 'green' },
    { label: 'System Alerts', value: '3', icon: AlertCircle, color: 'red' },
    { label: 'Success Rate', value: '96%', icon: TrendingUp, color: 'green' },
  ];

  const users = [
    { id: 1, name: 'John Doe', email: 'john@example.com', role: 'Lawyer', status: 'Active', contracts: 15 },
    { id: 2, name: 'Jane Smith', email: 'jane@example.com', role: 'Client', status: 'Active', contracts: 8 },
    { id: 3, name: 'Bob Johnson', email: 'bob@example.com', role: 'Admin', status: 'Active', contracts: 42 },
  ];

  const auditLogs = [
    { id: 1, user: 'John Doe', action: 'Contract uploaded', timestamp: '2025-01-15 10:30 AM' },
    { id: 2, user: 'Jane Smith', action: 'Role changed to Lawyer', timestamp: '2025-01-15 09:15 AM' },
    { id: 3, user: 'Bob Johnson', action: 'User deleted', timestamp: '2025-01-14 04:20 PM' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
        <p className="text-gray-600 mt-1">Manage users, view audit logs, and monitor system health</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          const colors = {
            blue: 'bg-blue-100 text-blue-600',
            red: 'bg-red-100 text-red-600',
            green: 'bg-green-100 text-green-600',
          };
          
          return (
            <Card key={index}>
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
                  <p className="text-3xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colors[stat.color]}`}>
                  <Icon className="w-6 h-6" />
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* User Management */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
          <Button size="sm">Add New User</Button>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Email</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Role</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Contracts</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4 text-sm font-medium text-gray-900">{user.name}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{user.email}</td>
                  <td className="px-4 py-4 text-sm">
                    <Badge variant="info">{user.role}</Badge>
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <Badge variant="success">{user.status}</Badge>
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">{user.contracts}</td>
                  <td className="px-4 py-4 text-sm">
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline">Edit</Button>
                      <Button size="sm" variant="danger">Delete</Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Audit Logs */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Audit Logs</h2>
        <div className="space-y-3">
          {auditLogs.map((log) => (
            <div key={log.id} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="text-sm font-medium text-gray-900">{log.action}</p>
                <p className="text-xs text-gray-600 mt-1">by {log.user}</p>
              </div>
              <p className="text-xs text-gray-500">{log.timestamp}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

export default AdminPage;
