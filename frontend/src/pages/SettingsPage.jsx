import { useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { toggleTheme } from '../store/uiSlice';
import { User, Lock, Bell, Moon, Sun, Key, CreditCard, Trash2, Save, Mail, Phone } from 'lucide-react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';

function SettingsPage() {
  const dispatch = useDispatch();
  const { user } = useSelector(state => state.auth);
  const { theme } = useSelector(state => state.ui);
  
  // Profile Settings
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    phone: '',
    company: '',
  });

  // Password Settings
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  // Notification Settings
  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    contractUploaded: true,
    analysisComplete: true,
    riskAlerts: true,
    weeklyReport: false,
  });

  const [saving, setSaving] = useState(false);

  const handleSaveProfile = () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      // Show success toast
    }, 1000);
  };

  const handleChangePassword = () => {
    setSaving(true);
    setTimeout(() => {
      setSaving(false);
      setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
    }, 1000);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>Settings</h1>
        <p className="text-lg" style={{ color: 'var(--color-text-tertiary)' }}>
          Manage your account preferences and settings
        </p>
      </div>

      {/* Profile Settings */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--color-primary-500), var(--color-accent-blue))' }}>
            <User className="w-6 h-6" style={{ color: 'white' }} />
          </div>
          <div>
            <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Profile Settings</h2>
            <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Update your personal information</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Full Name"
              value={profileData.name}
              onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
              placeholder="John Doe"
            />
            <Input
              label="Email Address"
              type="email"
              value={profileData.email}
              onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
              placeholder="john@example.com"
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="Phone Number"
              type="tel"
              value={profileData.phone}
              onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
              placeholder="+1 (555) 000-0000"
            />
            <Input
              label="Company Name"
              value={profileData.company}
              onChange={(e) => setProfileData({ ...profileData, company: e.target.value })}
              placeholder="ABC Law Firm"
            />
          </div>
          <div className="flex justify-end pt-4">
            <Button onClick={handleSaveProfile} loading={saving} className="gap-2">
              <Save className="w-4 h-4" style={{ color: 'white' }} />
              Save Changes
            </Button>
          </div>
        </div>
      </Card>

      {/* Security Settings */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--color-error), #DC2626)' }}>
            <Lock className="w-6 h-6" style={{ color: 'white' }} />
          </div>
          <div>
            <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Security</h2>
            <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Manage your password and security settings</p>
          </div>
        </div>

        <div className="space-y-4">
          <Input
            label="Current Password"
            type="password"
            value={passwordData.currentPassword}
            onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
            placeholder="Enter current password"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              label="New Password"
              type="password"
              value={passwordData.newPassword}
              onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
              placeholder="Enter new password"
              helperText="Minimum 8 characters"
            />
            <Input
              label="Confirm New Password"
              type="password"
              value={passwordData.confirmPassword}
              onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
              placeholder="Confirm new password"
            />
          </div>
          <div className="flex justify-end pt-4">
            <Button onClick={handleChangePassword} loading={saving} className="gap-2">
              <Lock className="w-4 h-4" style={{ color: 'white' }} />
              Change Password
            </Button>
          </div>
        </div>
      </Card>

      {/* Appearance */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--color-accent-purple), #8B5CF6)' }}>
            {theme === 'dark' ? <Moon className="w-6 h-6" style={{ color: 'white' }} /> : <Sun className="w-6 h-6" style={{ color: 'white' }} />}
          </div>
          <div>
            <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Appearance</h2>
            <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Customize how Legalyze looks</p>
          </div>
        </div>

        <div className="flex items-center justify-between p-4 rounded-xl" style={{ background: 'var(--color-bg-tertiary)' }}>
          <div className="flex items-center gap-3">
            {theme === 'dark' ? <Moon className="w-5 h-5" style={{ color: 'var(--color-text-secondary)' }} /> : <Sun className="w-5 h-5" style={{ color: 'var(--color-text-secondary)' }} />}
            <div>
              <p className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>Dark Mode</p>
              <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Use dark theme for the interface</p>
            </div>
          </div>
          <button
            onClick={() => dispatch(toggleTheme())}
            className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
              theme === 'dark' ? 'bg-[var(--color-primary-600)]' : 'bg-[var(--color-neutral-300)]'
            }`}
          >
            <span
              className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                theme === 'dark' ? 'translate-x-7' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </Card>

      {/* Notifications */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--color-accent-teal), #14B8A6)' }}>
            <Bell className="w-6 h-6" style={{ color: 'white' }} />
          </div>
          <div>
            <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Notifications</h2>
            <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Choose what notifications you receive</p>
          </div>
        </div>

        <div className="space-y-3">
          {[
            { key: 'emailNotifications', label: 'Email Notifications', desc: 'Receive notifications via email' },
            { key: 'contractUploaded', label: 'Contract Uploaded', desc: 'Notify when a contract is uploaded' },
            { key: 'analysisComplete', label: 'Analysis Complete', desc: 'Notify when analysis is finished' },
            { key: 'riskAlerts', label: 'Risk Alerts', desc: 'Get alerts for high-risk contracts' },
            { key: 'weeklyReport', label: 'Weekly Report', desc: 'Receive weekly summary of activities' },
          ].map((item) => (
            <div key={item.key} className="flex items-center justify-between p-4 rounded-xl hover:bg-[var(--color-bg-tertiary)] transition-colors">
              <div>
                <p className="font-semibold" style={{ color: 'var(--color-text-primary)' }}>{item.label}</p>
                <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>{item.desc}</p>
              </div>
              <button
                onClick={() => setNotifications({ ...notifications, [item.key]: !notifications[item.key] })}
                className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                  notifications[item.key] ? 'bg-[var(--color-primary-600)]' : 'bg-[var(--color-neutral-300)]'
                }`}
              >
                <span
                  className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                    notifications[item.key] ? 'translate-x-7' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </Card>

      {/* API Access */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'linear-gradient(135deg, var(--color-accent-orange), #F97316)' }}>
            <Key className="w-6 h-6" style={{ color: 'white' }} />
          </div>
          <div>
            <h2 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>API Access</h2>
            <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Manage your API keys for integrations</p>
          </div>
        </div>

        <div className="p-6 rounded-xl" style={{ background: 'var(--color-bg-tertiary)', border: '2px dashed var(--color-neutral-300)' }}>
          <div className="text-center">
            <Key className="w-12 h-12 mx-auto mb-4" style={{ color: 'var(--color-neutral-400)' }} />
            <h3 className="text-lg font-bold mb-2" style={{ color: 'var(--color-text-primary)' }}>No API Keys Yet</h3>
            <p className="text-sm mb-6" style={{ color: 'var(--color-text-tertiary)' }}>
              Generate an API key to integrate Legalyze with your applications
            </p>
            <Button variant="outline">Generate API Key</Button>
          </div>
        </div>
      </Card>

      {/* Danger Zone */}
      <Card>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: 'var(--color-error)' }}>
            <Trash2 className="w-6 h-6" style={{ color: 'white' }} />
          </div>
          <div>
            <h2 className="text-2xl font-bold" style={{ color: 'var(--color-error)' }}>Danger Zone</h2>
            <p className="text-sm" style={{ color: 'var(--color-text-tertiary)' }}>Irreversible account actions</p>
          </div>
        </div>

        <div className="p-6 rounded-xl" style={{ background: 'var(--color-error-light)', border: '2px solid var(--color-error)' }}>
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-bold mb-2" style={{ color: 'var(--color-error)' }}>Delete Account</h3>
              <p className="text-sm" style={{ color: 'var(--color-error)' }}>
                Once you delete your account, there is no going back. All your data will be permanently deleted.
              </p>
            </div>
            <Button variant="danger" className="flex-shrink-0">
              Delete Account
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

export default SettingsPage;