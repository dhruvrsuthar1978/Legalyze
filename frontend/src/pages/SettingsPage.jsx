import { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { toggleTheme } from '../store/uiSlice';
import { setUser, logout } from '../store/authSlice';
import { User, Lock, Bell, Moon, Sun, Save, Trash2 } from 'lucide-react';
import { authService } from '../services/authService';
import { showToast } from '../store/uiSlice';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';

function SettingsPage() {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const { theme } = useSelector((state) => state.ui);

  const [savingProfile, setSavingProfile] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);
  const [profileData, setProfileData] = useState({
    name: '',
    phone: '',
    organization: '',
    job_title: '',
  });
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    contractUploaded: true,
    analysisComplete: true,
    riskAlerts: true,
    weeklyReport: false,
  });

  useEffect(() => {
    setProfileData({
      name: user?.name || '',
      phone: user?.profile?.phone || '',
      organization: user?.profile?.organization || '',
      job_title: user?.profile?.job_title || '',
    });
  }, [user]);

  const handleSaveProfile = async () => {
    setSavingProfile(true);
    try {
      const payload = {
        name: profileData.name,
        phone: profileData.phone || null,
        organization: profileData.organization || null,
        job_title: profileData.job_title || null,
      };
      const updated = await authService.updateProfile(payload);
      dispatch(setUser(updated));
      dispatch(showToast({ type: 'success', title: 'Profile Saved', message: 'Settings updated successfully.' }));
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to update profile';
      dispatch(showToast({ type: 'error', title: 'Update Failed', message }));
    } finally {
      setSavingProfile(false);
    }
  };

  const handleChangePassword = async () => {
    if (!passwordData.currentPassword || !passwordData.newPassword || !passwordData.confirmPassword) {
      dispatch(showToast({ type: 'error', title: 'Missing Fields', message: 'Fill all password fields.' }));
      return;
    }
    setSavingPassword(true);
    try {
      await authService.changePassword({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
        confirm_password: passwordData.confirmPassword,
      });
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      dispatch(showToast({ type: 'success', title: 'Password Changed', message: 'Please log in again.' }));
      dispatch(logout());
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to change password';
      dispatch(showToast({ type: 'error', title: 'Password Change Failed', message }));
    } finally {
      setSavingPassword(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div>
        <h1 className="text-4xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>Settings</h1>
        <p className="text-lg" style={{ color: 'var(--color-text-tertiary)' }}>Manage your account and preferences</p>
      </div>

      <Card>
        <div className="flex items-center gap-3 mb-6">
          <User className="w-6 h-6" />
          <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Profile Settings</h2>
        </div>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input label="Full Name" value={profileData.name} onChange={(e) => setProfileData((p) => ({ ...p, name: e.target.value }))} />
            <Input label="Email Address" value={user?.email || ''} disabled />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input label="Phone (E.164)" value={profileData.phone} onChange={(e) => setProfileData((p) => ({ ...p, phone: e.target.value }))} placeholder="+14155552671" />
            <Input label="Organization" value={profileData.organization} onChange={(e) => setProfileData((p) => ({ ...p, organization: e.target.value }))} />
          </div>
          <Input label="Job Title" value={profileData.job_title} onChange={(e) => setProfileData((p) => ({ ...p, job_title: e.target.value }))} />
          <div className="flex justify-end pt-2">
            <Button onClick={handleSaveProfile} loading={savingProfile} className="gap-2">
              <Save className="w-4 h-4" style={{ color: 'white' }} />
              Save Profile
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <div className="flex items-center gap-3 mb-6">
          <Lock className="w-6 h-6" />
          <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Security</h2>
        </div>
        <div className="space-y-4">
          <Input label="Current Password" type="password" value={passwordData.currentPassword} onChange={(e) => setPasswordData((p) => ({ ...p, currentPassword: e.target.value }))} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input label="New Password" type="password" value={passwordData.newPassword} onChange={(e) => setPasswordData((p) => ({ ...p, newPassword: e.target.value }))} />
            <Input label="Confirm New Password" type="password" value={passwordData.confirmPassword} onChange={(e) => setPasswordData((p) => ({ ...p, confirmPassword: e.target.value }))} />
          </div>
          <div className="flex justify-end pt-2">
            <Button onClick={handleChangePassword} loading={savingPassword} className="gap-2">
              <Lock className="w-4 h-4" style={{ color: 'white' }} />
              Change Password
            </Button>
          </div>
        </div>
      </Card>

      <Card>
        <div className="flex items-center gap-3 mb-6">
          {theme === 'dark' ? <Moon className="w-6 h-6" /> : <Sun className="w-6 h-6" />}
          <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Appearance</h2>
        </div>
        <div className="flex items-center justify-between p-4 rounded-xl" style={{ background: 'var(--color-bg-tertiary)' }}>
          <p style={{ color: 'var(--color-text-primary)' }}>Dark Mode</p>
          <button
            onClick={() => dispatch(toggleTheme())}
            className={`relative inline-flex h-8 w-14 items-center rounded-full ${theme === 'dark' ? 'bg-[var(--color-primary-600)]' : 'bg-[var(--color-neutral-300)]'}`}
          >
            <span className={`inline-block h-6 w-6 transform rounded-full bg-white ${theme === 'dark' ? 'translate-x-7' : 'translate-x-1'}`} />
          </button>
        </div>
      </Card>

      <Card>
        <div className="flex items-center gap-3 mb-6">
          <Bell className="w-6 h-6" />
          <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Notifications</h2>
        </div>
        <div className="space-y-3">
          {[
            { key: 'emailNotifications', label: 'Email Notifications' },
            { key: 'contractUploaded', label: 'Contract Uploaded' },
            { key: 'analysisComplete', label: 'Analysis Complete' },
            { key: 'riskAlerts', label: 'Risk Alerts' },
            { key: 'weeklyReport', label: 'Weekly Report' },
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between p-3 rounded-xl hover:bg-[var(--color-bg-tertiary)]">
              <p style={{ color: 'var(--color-text-primary)' }}>{item.label}</p>
              <button
                onClick={() => setNotifications((p) => ({ ...p, [item.key]: !p[item.key] }))}
                className={`relative inline-flex h-8 w-14 items-center rounded-full ${notifications[item.key] ? 'bg-[var(--color-primary-600)]' : 'bg-[var(--color-neutral-300)]'}`}
              >
                <span className={`inline-block h-6 w-6 transform rounded-full bg-white ${notifications[item.key] ? 'translate-x-7' : 'translate-x-1'}`} />
              </button>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <div className="flex items-center gap-3 mb-6">
          <Trash2 className="w-6 h-6" />
          <h2 className="text-2xl font-bold" style={{ color: 'var(--color-error)' }}>Danger Zone</h2>
        </div>
        <p style={{ color: 'var(--color-text-tertiary)' }}>Account deletion is not exposed by API yet.</p>
      </Card>
    </div>
  );
}

export default SettingsPage;
