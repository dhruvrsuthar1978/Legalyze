import { useCallback, useEffect, useMemo, useState } from 'react';
import { Database, FileText, Activity, ServerCog } from 'lucide-react';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Button from '../components/ui/Button';
import { useDispatch, useSelector } from 'react-redux';
import { Navigate } from 'react-router-dom';
import { adminService } from '../services/adminService';
import { contractService } from '../services/contractService';
import { showToast } from '../store/uiSlice';

function AdminPage() {
  const dispatch = useDispatch();
  const { user } = useSelector(state => state.auth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [systemStats, setSystemStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [contractStats, setContractStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [usersPage, setUsersPage] = useState(1);
  const [usersTotalPages, setUsersTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [actionLoading, setActionLoading] = useState({});

  const loadAdminData = useCallback(async (page = 1, query = '') => {
    setLoading(true);
    setError(null);
    try {
      const [statsRes, healthRes, contractStatsRes, usersRes, auditRes] = await Promise.all([
        adminService.getSystemStats(),
        adminService.getSystemHealth(),
        contractService.getContractStats(),
        adminService.getUsers(page, 25, query),
        adminService.getAuditLogs(25),
      ]);

      setSystemStats(statsRes);
      setHealth(healthRes);
      setContractStats(contractStatsRes);
      setUsers(usersRes.users || []);
      setUsersPage(usersRes.page || 1);
      setUsersTotalPages(usersRes.total_pages || 1);
      setAuditLogs(auditRes.logs || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load admin data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAdminData(usersPage, searchQuery);
  }, [loadAdminData, usersPage, searchQuery]);

  const stats = useMemo(() => {
    const db = systemStats?.database || {};

    return [
      {
        label: 'Total Contracts',
        value: String(contractStats?.total_contracts ?? 0),
        icon: FileText,
        color: 'blue'
      },
      {
        label: 'Uploads (30d)',
        value: String(contractStats?.contracts_last_30_days ?? 0),
        icon: Activity,
        color: 'green'
      },
      {
        label: 'DB Collections',
        value: String(db.collections ?? 0),
        icon: Database,
        color: 'yellow'
      },
      {
        label: 'System Status',
        value: health?.status === 'healthy' ? 'Healthy' : 'Degraded',
        icon: ServerCog,
        color: health?.status === 'healthy' ? 'green' : 'red'
      },
    ];
  }, [systemStats, contractStats, health]);

  // Only allow Admin users to access this page
  if (!user || (user.role || '').toLowerCase() !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  const handleRoleToggle = async (targetUser) => {
    const nextRole = targetUser.role === 'admin' ? 'user' : 'admin';
    try {
      setActionLoading(prev => ({ ...prev, [targetUser.id]: 'role' }));
      await adminService.updateUserRole(targetUser.id, nextRole);
      dispatch(showToast({
        type: 'success',
        title: 'Role Updated',
        message: `${targetUser.email} is now ${nextRole}.`,
      }));
      await loadAdminData(usersPage, searchQuery);
    } catch (err) {
      dispatch(showToast({
        type: 'error',
        title: 'Role Update Failed',
        message: err.response?.data?.detail || err.message || 'Could not update role.',
      }));
    } finally {
      setActionLoading(prev => ({ ...prev, [targetUser.id]: null }));
    }
  };

  const handleStatusToggle = async (targetUser) => {
    const nextStatus = targetUser.account_status === 'active' ? 'suspended' : 'active';
    try {
      setActionLoading(prev => ({ ...prev, [targetUser.id]: 'status' }));
      await adminService.updateUserStatus(targetUser.id, nextStatus);
      dispatch(showToast({
        type: 'success',
        title: 'Status Updated',
        message: `${targetUser.email} is now ${nextStatus}.`,
      }));
      await loadAdminData(usersPage, searchQuery);
    } catch (err) {
      dispatch(showToast({
        type: 'error',
        title: 'Status Update Failed',
        message: err.response?.data?.detail || err.message || 'Could not update status.',
      }));
    } finally {
      setActionLoading(prev => ({ ...prev, [targetUser.id]: null }));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Panel</h1>
        <p className="text-gray-600 mt-1">Live system metrics and platform health</p>
      </div>

      {loading && (
        <Card>
          <p className="text-gray-600">Loading admin data...</p>
        </Card>
      )}

      {error && (
        <Card>
          <p className="text-red-600 font-medium">Failed to load admin data</p>
          <p className="text-gray-600 mt-1">{error}</p>
        </Card>
      )}

      {/* Stats Grid */}
      {!loading && !error && (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          const colors = {
            blue: 'bg-blue-100 text-blue-600',
            red: 'bg-red-100 text-red-600',
            green: 'bg-green-100 text-green-600',
            yellow: 'bg-yellow-100 text-yellow-600',
          };
          
          return (
            <Card key={stat.label}>
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
      )}

      {/* User Management */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
          <Button size="sm" variant="outline" onClick={() => loadAdminData(usersPage, searchQuery)} loading={loading}>
            Refresh
          </Button>
        </div>
        <div className="flex items-center gap-3 mb-4">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search by name or email"
            className="w-full max-w-md px-3 py-2 rounded-lg border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <Button
            size="sm"
            onClick={() => {
              setUsersPage(1);
              setSearchQuery(searchInput.trim());
            }}
          >
            Search
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setSearchInput('');
              setSearchQuery('');
              setUsersPage(1);
            }}
          >
            Clear
          </Button>
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
              {users.map((row) => (
                <tr key={row.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4 text-sm font-medium text-gray-900">{row.name}</td>
                  <td className="px-4 py-4 text-sm text-gray-600">{row.email}</td>
                  <td className="px-4 py-4 text-sm">
                    <Badge variant={row.role === 'admin' ? 'warning' : 'info'}>{row.role}</Badge>
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <Badge variant={row.account_status === 'active' ? 'success' : 'error'}>
                      {row.account_status}
                    </Badge>
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">{row.contracts}</td>
                  <td className="px-4 py-4 text-sm">
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleRoleToggle(row)}
                        disabled={row.id === user?.id}
                        loading={actionLoading[row.id] === 'role'}
                      >
                        {row.role === 'admin' ? 'Make User' : 'Make Admin'}
                      </Button>
                      <Button
                        size="sm"
                        variant={row.account_status === 'active' ? 'danger' : 'success'}
                        onClick={() => handleStatusToggle(row)}
                        disabled={row.id === user?.id}
                        loading={actionLoading[row.id] === 'status'}
                      >
                        {row.account_status === 'active' ? 'Suspend' : 'Activate'}
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td className="px-4 py-6 text-sm text-gray-600" colSpan={6}>No users found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-end gap-2 mt-4">
          <Button
            size="sm"
            variant="outline"
            disabled={usersPage <= 1 || loading}
            onClick={() => setUsersPage(prev => Math.max(1, prev - 1))}
          >
            Previous
          </Button>
          <span className="text-sm text-gray-600">
            Page {usersPage} of {usersTotalPages}
          </span>
          <Button
            size="sm"
            variant="outline"
            disabled={usersPage >= usersTotalPages || loading}
            onClick={() => setUsersPage(prev => Math.min(usersTotalPages, prev + 1))}
          >
            Next
          </Button>
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
                <p className="text-xs text-gray-600 mt-1">
                  by {log.actor}{log.target ? ` -> ${log.target}` : ''}
                </p>
              </div>
              <p className="text-xs text-gray-500">
                {log.timestamp ? new Date(log.timestamp).toLocaleString() : 'Unknown'}
              </p>
            </div>
          ))}
          {auditLogs.length === 0 && (
            <p className="text-sm text-gray-600">No audit events yet.</p>
          )}
        </div>
      </Card>
    </div>
  );
}

export default AdminPage;
