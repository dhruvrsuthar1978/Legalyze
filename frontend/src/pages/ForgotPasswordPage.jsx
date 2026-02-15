import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import Card from '../components/ui/Card';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { authService } from '../services/authService';
import { showToast } from '../store/uiSlice';

function ForgotPasswordPage() {
  const dispatch = useDispatch();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    try {
      const res = await authService.forgotPassword(email);
      dispatch(showToast({ type: 'success', title: 'Request Sent', message: res.message || 'If this email exists, a reset link was sent.' }));
    } catch (err) {
      const message = err.response?.data?.detail || err.message || 'Failed to send reset request';
      dispatch(showToast({ type: 'error', title: 'Request Failed', message }));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <Card className="w-full max-w-md" glass>
        <h1 className="text-2xl font-bold mb-2">Forgot Password</h1>
        <p className="text-sm mb-6" style={{ color: 'var(--color-text-tertiary)' }}>
          Enter your email and we&apos;ll send a reset link if the account exists.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
          />
          <Button type="submit" className="w-full" loading={loading}>Send Reset Link</Button>
        </form>
        <div className="mt-4 text-sm">
          <Link to="/login" style={{ color: 'var(--color-primary-600)' }}>Back to Login</Link>
        </div>
      </Card>
    </div>
  );
}

export default ForgotPasswordPage;
