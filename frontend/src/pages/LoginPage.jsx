import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { loginStart, loginSuccess, loginFailure } from '../store/authSlice';
import { showToast } from '../store/uiSlice';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
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

    // Simulate API call
    setTimeout(() => {
      // Mock authentication - in real app, call API
      if (formData.email === 'demo@legalyze.com' && formData.password === 'password123') {
        dispatch(loginSuccess({
          user: { name: 'Demo User', email: formData.email, role: 'Lawyer' },
          token: 'mock-jwt-token-' + Date.now(),
        }));
        dispatch(showToast({
          type: 'success',
          title: 'Login Successful',
          message: 'Welcome back!',
        }));
        navigate('/dashboard');
      } else {
        dispatch(loginFailure('Invalid credentials'));
        dispatch(showToast({
          type: 'error',
          title: 'Login Failed',
          message: 'Invalid email or password',
        }));
      }
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 aurora-bg relative overflow-hidden">
      {/* Decorative blobs */}
      <div className="absolute top-20 left-20 w-96 h-96 rounded-full filter blur-3xl opacity-20 animate-blob" style={{ background: 'var(--color-primary-400)' }}></div>
      <div className="absolute bottom-20 right-20 w-96 h-96 rounded-full filter blur-3xl opacity-15 animate-blob animation-delay-4000" style={{ background: 'var(--color-accent-purple)' }}></div>
      
      <Card className="w-full max-w-md relative z-10" glass>
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-8">
            <div className="w-14 h-14 bg-gradient-to-br from-[var(--color-primary-600)] to-[var(--color-accent-blue)] rounded-2xl flex items-center justify-center shadow-2xl animate-pulse-scale">
              <span className="text-white font-bold text-2xl">L</span>
            </div>
            <span className="text-3xl font-bold gradient-text-animated">Legalyze</span>
          </div>
          <h1 className="text-4xl font-bold mb-4">Welcome Back</h1>
          <p className="text-lg" style={{ color: 'var(--color-text-tertiary)' }}>Sign in to continue to your dashboard</p>
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
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
            </button>
          </div>

          <div className="flex items-center justify-between text-sm">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input type="checkbox" className="rounded-md border-2 w-4 h-4 smooth-transition" style={{ borderColor: 'var(--color-neutral-300)' }} />
              <span style={{ color: 'var(--color-neutral-600)' }} className="group-hover:text-[var(--color-neutral-900)] smooth-transition">Remember me</span>
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

        <div className="mt-6 p-4 rounded-xl" style={{ backgroundColor: 'var(--color-info-light)', border: '2px solid var(--color-info)', color: 'var(--color-info)' }}>
          <p className="font-bold mb-2 text-sm">Demo Credentials:</p>
          <p className="text-sm">Email: demo@legalyze.com</p>
          <p className="text-sm">Password: password123</p>
        </div>
      </Card>
    </div>
  );
}

export default LoginPage;