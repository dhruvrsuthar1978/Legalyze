import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { registerStart, registerSuccess, registerFailure } from '../store/authSlice';
import { showToast } from '../store/uiSlice';
import Input from '../components/ui/Input';
import Select from '../components/ui/Select';
import Button from '../components/ui/Button';
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
    role: 'Lawyer',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState({});

  const roleOptions = [
    { value: 'Admin', label: 'Admin' },
    { value: 'Lawyer', label: 'Lawyer' },
    { value: 'Client', label: 'Client' },
  ];

  const validate = () => {
    const newErrors = {};
    
    if (!formData.name) {
      newErrors.name = 'Full name is required';
    } else if (formData.name.length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
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
    }
    
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    if (!formData.role) {
      newErrors.role = 'Please select a role';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validate()) return;

    dispatch(registerStart());

    // Simulate API call
    setTimeout(() => {
      dispatch(registerSuccess({
        user: { 
          name: formData.name, 
          email: formData.email, 
          role: formData.role 
        },
        token: 'mock-jwt-token-' + Date.now(),
      }));
      dispatch(showToast({
        type: 'success',
        title: 'Account Created',
        message: 'Welcome to Legalyze!',
      }));
      navigate('/dashboard');
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <Card className="w-full max-w-md" glass>
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-6">
            <div className="w-12 h-12 bg-gradient-to-br from-[var(--color-primary-600)] to-[var(--color-accent-blue)] rounded-2xl flex items-center justify-center shadow-xl">
              <span className="text-white font-bold text-2xl">L</span>
            </div>
            <span className="text-3xl font-bold gradient-text">Legalyze</span>
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

          <Select
            label="Role"
            options={roleOptions}
            value={formData.role}
            onChange={(value) => setFormData({ ...formData, role: value })}
            error={errors.role}
          />

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