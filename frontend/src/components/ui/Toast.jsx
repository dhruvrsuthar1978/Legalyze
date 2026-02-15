import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { hideToast } from '../../store/uiSlice';
import { Check, X, Info, TriangleAlert } from 'lucide-react';

function Toast() {
  const dispatch = useDispatch();
  const toast = useSelector(state => state.ui.toast);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => {
        dispatch(hideToast());
      }, toast.duration || 3000);
      return () => clearTimeout(timer);
    }
  }, [toast, dispatch]);

  if (!toast) return null;

  const icons = {
    success: <Check className="w-5 h-5" />,
    error: <X className="w-5 h-5" />,
    warning: <TriangleAlert className="w-5 h-5" />,
    info: <Info className="w-5 h-5" />,
  };

  const styles = {
    success: {
      bg: 'bg-gradient-to-r from-emerald-50 to-green-50',
      border: 'border-emerald-300',
      text: 'text-emerald-900',
      iconBg: 'bg-emerald-100',
      iconColor: 'var(--color-success)',
    },
    error: {
      bg: 'bg-gradient-to-r from-red-50 to-rose-50',
      border: 'border-red-300',
      text: 'text-red-900',
      iconBg: 'bg-red-100',
      iconColor: 'var(--color-error)',
    },
    warning: {
      bg: 'bg-gradient-to-r from-amber-50 to-orange-50',
      border: 'border-amber-300',
      text: 'text-amber-900',
      iconBg: 'bg-amber-100',
      iconColor: 'var(--color-warning)',
    },
    info: {
      bg: 'bg-gradient-to-r from-blue-50 to-sky-50',
      border: 'border-blue-300',
      text: 'text-blue-900',
      iconBg: 'bg-blue-100',
      iconColor: 'var(--color-info)',
    },
  };

  const currentStyle = styles[toast.type || 'info'];

  return (
    <div className="fixed top-20 right-6 z-50 animate-slide-in" aria-live="polite">
      <div role="status" className={`floating-island flex items-center gap-4 px-5 py-4 min-w-[320px] ${currentStyle.bg} ${currentStyle.border} border-2`}>
        <div className={`shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${currentStyle.iconBg}`}>
          <div style={{ color: currentStyle.iconColor }}>
            {icons[toast.type || 'info']}
          </div>
        </div>
        <div className={`flex-1 ${currentStyle.text}`}>
          {toast.title && (
            <p className="font-bold text-sm mb-0.5">{toast.title}</p>
          )}
          {toast.message && (
            <p className="text-sm opacity-90">{toast.message}</p>
          )}
        </div>
        <button
          onClick={() => dispatch(hideToast())}
          className="shrink-0 p-1.5 rounded-lg hover:bg-white/50 smooth-transition"
          aria-label="Dismiss notification"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default Toast;