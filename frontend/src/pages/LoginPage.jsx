import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { loginStart, loginSuccess, loginFailure } from '../store/authSlice';
import { showToast } from '../store/uiSlice';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { authService } from '../services/authService';
import Card from '../components/ui/Card';
import { Eye, EyeOff } from 'lucide-react';

function LoginPage() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { loading, error } = useSelector(state => state.auth);
  
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) return;

    dispatch(loginStart());
    try {
      const data = await authService.login({ email: formData.email, password: formData.password });

      // Fetch user profile
      const profile = await authService.getProfile();

      dispatch(loginSuccess({
        user: profile,
        token: data.access_token || data.token || null,
      }));

      dispatch(showToast({ type: 'success', title: 'Login Successful', message: 'Welcome back!' }));
      navigate('/dashboard');

    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Login failed';
      dispatch(loginFailure(message));
      dispatch(showToast({ type: 'error', title: 'Login Failed', message }));
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ backgroundColor: 'var(--color-bg-secondary)' }}>
      <Card className="w-full max-w-md" glass>
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="w-12 h-12 rounded-md flex items-center justify-center" style={{ backgroundColor: 'var(--color-primary-600)' }}>
              <span className="text-white font-bold text-2xl">L</span>
            </div>
            <span className="text-3xl font-bold" style={{ color: 'var(--color-text-primary)' }}>Legalyze</span>
          </div>
          <h1 className="text-3xl font-bold mb-3">Welcome Back</h1>
          <p className="text-base" style={{ color: 'var(--color-text-tertiary)' }}>Sign in to continue to your dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <Input
            label="Email Address"
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={errors.email}
            placeholder="you@example.com"
            autoComplete="email"
          />

          <div className="relative">
            <Input
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              error={errors.password}
              placeholder="Enter your password"
              autoComplete="current-password"
              className="pr-12"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-[2.75rem] text-gray-400 hover:text-gray-600 transition-colors"
              style={{ color: 'var(--color-neutral-500)' }}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input type="checkbox" className="rounded border w-4 h-4 smooth-transition" style={{ borderColor: 'var(--color-neutral-300)' }} />
              <span style={{ color: 'var(--color-neutral-600)' }} className="group-hover:text-neutral-900 smooth-transition">Remember me</span>
            </label>
            <Link to="/forgot-password" className="font-medium smooth-transition" style={{ color: 'var(--color-primary-600)' }}>
              Forgot Password?
            </Link>
          </div>

          {error && (
            <div className="p-4 rounded-xl" style={{ backgroundColor: 'var(--color-error-light)', border: '2px solid var(--color-error)', color: 'var(--color-error)' }}>
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" size="lg" loading={loading}>
            Sign In
          </Button>
        </form>

        <div className="mt-8 text-center" style={{ color: 'var(--color-neutral-600)' }}>
          Don&apos;t have an account?{' '}
          <Link to="/register" className="font-bold smooth-transition" style={{ color: 'var(--color-primary-600)' }}>
            Create Account
          </Link>
        </div>

      </Card>
    </div>
  );
}

export default LoginPage;
