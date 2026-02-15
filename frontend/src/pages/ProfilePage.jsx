import { useEffect, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import { Pencil, Trash2, Download, Eye } from 'lucide-react';
import { setUser } from '../store/authSlice';
import { showToast } from '../store/uiSlice';
import { authService } from '../services/authService';
import { contractService } from '../services/contractService';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import Input from '../components/ui/Input';

function ProfilePage() {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [contracts, setContracts] = useState([]);
  const [loadingContracts, setLoadingContracts] = useState(true);
  const [profileForm, setProfileForm] = useState({
    name: '',
    phone: '',
    organization: '',
    job_title: '',
  });

  useEffect(() => {
    setProfileForm({
      name: user?.name || '',
      phone: user?.profile?.phone || '',
      organization: user?.profile?.organization || '',
      job_title: user?.profile?.job_title || '',
    });
  }, [user]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await contractService.getContracts(0, 20);
        if (!mounted) return;
        setContracts(res.contracts || []);
      } catch {
        if (!mounted) return;
        setContracts([]);
      } finally {
        if (mounted) setLoadingContracts(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload = {
        name: profileForm.name,
        phone: profileForm.phone || null,
        organization: profileForm.organization || null,
        job_title: profileForm.job_title || null,
      };
      const updated = await authService.updateProfile(payload);
      dispatch(setUser(updated));
      setEditing(false);
      dispatch(showToast({ type: 'success', title: 'Profile Updated', message: 'Your profile has been saved.' }));
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to update profile';
      dispatch(showToast({ type: 'error', title: 'Update Failed', message }));
    } finally {
      setSaving(false);
    }
  };

  const memberSince = useMemo(() => {
    if (!user?.created_at) return '-';
    return new Date(user.created_at).toLocaleDateString();
  }, [user]);

  const handleDownload = async (contractId) => {
    try {
      const res = await contractService.downloadContract(contractId);
      if (res?.download_url) {
        window.open(res.download_url, '_blank', 'noopener,noreferrer');
      }
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Download failed';
      dispatch(showToast({ type: 'error', title: 'Download Failed', message }));
    }
  };

  const handleDelete = async (contractId) => {
    try {
      await contractService.deleteContract(contractId);
      setContracts((prev) => prev.filter((c) => c.id !== contractId));
      dispatch(showToast({ type: 'success', title: 'Deleted', message: 'Contract deleted successfully.' }));
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Delete failed';
      dispatch(showToast({ type: 'error', title: 'Delete Failed', message }));
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Profile & History</h1>
        <p className="text-gray-600 mt-1">Manage your account and contracts</p>
      </div>

      <Card>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-gray-900">User Information</h2>
          <Button variant="outline" size="sm" onClick={() => setEditing((v) => !v)} className="gap-2">
            <Pencil className="w-4 h-4" style={{ color: '#4b5563' }} />
            {editing ? 'Cancel' : 'Edit'}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Input
            label="Full Name"
            value={profileForm.name}
            disabled={!editing}
            onChange={(e) => setProfileForm((p) => ({ ...p, name: e.target.value }))}
          />
          <Input label="Email" value={user?.email || ''} disabled />
          <Input
            label="Phone (E.164)"
            value={profileForm.phone}
            disabled={!editing}
            onChange={(e) => setProfileForm((p) => ({ ...p, phone: e.target.value }))}
            placeholder="+14155552671"
          />
          <Input
            label="Organization"
            value={profileForm.organization}
            disabled={!editing}
            onChange={(e) => setProfileForm((p) => ({ ...p, organization: e.target.value }))}
          />
          <Input
            label="Job Title"
            value={profileForm.job_title}
            disabled={!editing}
            onChange={(e) => setProfileForm((p) => ({ ...p, job_title: e.target.value }))}
          />
          <Input label="Member Since" value={memberSince} disabled />
        </div>

        {editing && (
          <div className="mt-6 flex gap-3">
            <Button loading={saving} onClick={handleSave}>Save Changes</Button>
            <Button variant="outline" onClick={() => setEditing(false)}>Cancel</Button>
          </div>
        )}
      </Card>

      <Card>
        <h2 className="text-xl font-semibold text-gray-900 mb-6">Contract History</h2>
        {loadingContracts ? (
          <p className="text-gray-600">Loading contracts...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Contract</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Uploaded</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Risk Score</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {contracts.map((contract) => (
                  <tr key={contract.id} className="hover:bg-gray-50">
                    <td className="px-4 py-4 text-sm font-medium text-gray-900">{contract.title || contract.filename}</td>
                    <td className="px-4 py-4 text-sm text-gray-600">
                      {new Date(contract.uploaded_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-4 text-sm">
                      <Badge variant={contract.analysis_status === 'completed' ? 'success' : 'warning'}>
                        {contract.analysis_status}
                      </Badge>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-600">{contract.overall_risk_score ?? 0}</td>
                    <td className="px-4 py-4 text-sm">
                      <div className="flex items-center gap-2">
                        <Link to={`/contract/${contract.id}`} className="p-1.5 hover:bg-gray-100 rounded text-gray-600 hover:text-blue-600 transition-colors">
                          <Eye className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={() => handleDownload(contract.id)}
                          className="p-1.5 hover:bg-gray-100 rounded text-gray-600 hover:text-blue-600 transition-colors"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(contract.id)}
                          className="p-1.5 hover:bg-gray-100 rounded text-gray-600 hover:text-red-600 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {contracts.length === 0 && <p className="text-gray-600 py-6">No contracts uploaded yet.</p>}
          </div>
        )}
      </Card>
    </div>
  );
}

export default ProfilePage;
