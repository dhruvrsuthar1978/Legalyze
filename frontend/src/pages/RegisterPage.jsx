import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { registerStart, registerSuccess, registerFailure } from '../store/authSlice';
import { showToast } from '../store/uiSlice';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { authService } from '../services/authService';
import Card from '../components/ui/Card';
import { Eye, EyeOff } from 'lucide-react';

function RegisterPage() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { loading } = useSelector(state => state.auth);
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    accountType: 'client',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    
    if (!formData.name) {
      newErrors.name = 'Full name is required';
    } else if (formData.name.length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    } else if (!/^[a-zA-Z\s\-'.]+$/.test(formData.name)) {
      newErrors.name = 'Name can only include letters, spaces, hyphens, apostrophes, and periods';
    }
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    } else if (!/[A-Z]/.test(formData.password)) {
      newErrors.password = 'Password must include at least one uppercase letter';
    } else if (!/[a-z]/.test(formData.password)) {
      newErrors.password = 'Password must include at least one lowercase letter';
    } else if (!/\d/.test(formData.password)) {
      newErrors.password = 'Password must include at least one number';
    } else if (!/[!@#$%^&*(),.?":{}|<>]/.test(formData.password)) {
      newErrors.password = 'Password must include at least one special character';
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) return;

    dispatch(registerStart());

    try {
      // Register user via API
      await authService.register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
        confirm_password: formData.confirmPassword,
        role: formData.accountType,
      });

      // Auto-login after registration
      const loginData = await authService.login({ email: formData.email, password: formData.password });
      const profile = await authService.getProfile();

      dispatch(registerSuccess({ user: profile, token: loginData.access_token || loginData.token }));
      dispatch(showToast({ type: 'success', title: 'Account Created', message: 'Welcome to Legalyze!' }));
      navigate('/dashboard');

    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Registration failed';
      dispatch(registerFailure(message));
      dispatch(showToast({ type: 'error', title: 'Registration Failed', message }));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <Card className="w-full max-w-md" glass>
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-md flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary-600)' }}>
              <span className="text-white font-bold text-2xl">L</span>
            </div>
            <span className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Legalyze</span>
          </div>
          <h1 className="text-3xl font-bold mb-3">Create Account</h1>
          <p className="text-lg" style={{ color: 'var(--color-neutral-600)' }}>Get started with Legalyze today</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            label="Full Name"
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={errors.name}
            placeholder="John Doe"
            autoComplete="name"
          />

          <Input
            label="Email Address"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={errors.email}
            placeholder="you@example.com"
            autoComplete="email"
          />

          <div>
            <label className="label-text mb-2 block">Account Type</label>
            <select
              value={formData.accountType}
              onChange={(e) => setFormData({ ...formData, accountType: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-[var(--color-neutral-300)] bg-white"
            >
              <option value="client">Client (Self-register)</option>
              <option value="lawyer" disabled>Lawyer (Assigned by admin)</option>
              <option value="admin" disabled>Admin (Assigned by admin)</option>
            </select>
            <p className="text-xs mt-2" style={{ color: 'var(--color-neutral-500)' }}>
              New accounts are created as Client. Lawyer/Admin roles are granted by admin only.
            </p>
          </div>

          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              error={errors.password}
              placeholder="Min. 8 characters"
              autoComplete="new-password"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          <Input
            label="Confirm Password"
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            error={errors.confirmPassword}
            placeholder="Confirm your password"
            autoComplete="new-password"
          />

          <Button type="submit" className="w-full" size="lg" loading={loading}>
            Create Account
          </Button>
        </form>

        <div className="mt-8 text-center" style={{ color: 'var(--color-neutral-600)' }}>
          Already have an account?{' '}
          <Link to="/login" className="font-bold smooth-transition" style={{ color: 'var(--color-primary-600)' }}>
            Sign In
          </Link>
        </div>
      </Card>
    </div>
  );
}

export default RegisterPage;
