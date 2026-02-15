import { useState } from 'react';
import { useSelector } from 'react-redux';
import { Pencil, Trash2, Download, Eye } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Input from '../components/ui/Input';

function ProfilePage() {
  const { user } = useSelector(state => state.auth);
  const [editing, setEditing] = useState(false);

  const contracts = [
    { id: 1, name: 'Employment Agreement.pdf', uploadedAt: '2025-01-15', status: 'Signed', risk: 'low' },
    { id: 2, name: 'NDA Document.pdf', uploadedAt: '2025-01-10', status: 'Analyzed', risk: 'medium' },
    { id: 3, name: 'Service Contract.docx', uploadedAt: '2025-01-05', status: 'Pending', risk: 'high' },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Profile & History</h1>
        <p className="text-gray-600 mt-1">Manage your account and view contract history</p>
      </div>

      {/* User Info */}
      <Card>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">User Information</h2>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setEditing(!editing)}
            className="gap-2"
          >
            <Pencil className="w-4 h-4" style={{ color: '#4b5563' }} />
            {editing ? 'Cancel' : 'Edit'}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Full Name"
            value={user?.name || ''}
            disabled={!editing}
          />
          <Input
            label="Email"
            value={user?.email || ''}
            disabled={!editing}
          />
          <Input
            label="Role"
            value={user?.role || ''}
            disabled
          />
          <Input
            label="Member Since"
            value="January 2025"
            disabled
          />
        </div>

        {editing && (
          <div className="mt-6 flex gap-3">
            <Button>Save Changes</Button>
            <Button variant="outline" onClick={() => setEditing(false)}>
              Cancel
            </Button>
          </div>
        )}
      </Card>

      {/* Contract History */}
      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Contract History</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Contract Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Uploaded</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Risk</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {contracts.map((contract) => (
                <tr key={contract.id} className="hover:bg-gray-50">
                  <td className="px-4 py-4 text-sm font-medium text-gray-900">
                    {contract.name}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-600">
                    {contract.uploadedAt}
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <Badge variant={contract.status === 'Signed' ? 'success' : 'warning'}>
                      {contract.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <Badge variant={contract.risk}>
                      {contract.risk}
                    </Badge>
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <div className="flex items-center gap-2">
                      <button className="p-1.5 hover:bg-gray-100 rounded text-gray-600 hover:text-blue-600 transition-colors">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="p-1.5 hover:bg-gray-100 rounded text-gray-600 hover:text-blue-600 transition-colors">
                        <Download className="w-4 h-4" />
                      </button>
                      <button className="p-1.5 hover:bg-gray-100 rounded text-gray-600 hover:text-red-600 transition-colors">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

export default ProfilePage;