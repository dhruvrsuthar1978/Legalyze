import { Dialog, DialogPanel, DialogTitle, Description } from '@headlessui/react';
import { X } from 'lucide-react';
import Button from './Button';

function Modal({ 
  isOpen, 
  onClose, 
  title, 
  children, 
  footer,
  size = 'md',
  showCloseButton = true 
}) {
  const sizes = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-md" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel className={`w-full ${sizes[size]} floating-island smooth-transition`}>
          <div className="flex items-center justify-between p-6" style={{ borderBottom: 'var(--border-thin) solid var(--color-neutral-200)' }}>
            <DialogTitle className="text-2xl font-bold">
              {title}
            </DialogTitle>
            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-[var(--color-neutral-100)] smooth-transition"
                style={{ color: 'var(--color-neutral-500)' }}
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
          
          <div className="p-6">
            {children}
          </div>
          
          {footer && (
            <div className="flex items-center justify-end gap-3 p-6 rounded-b-xl" style={{ borderTop: 'var(--border-thin) solid var(--color-neutral-200)', backgroundColor: 'var(--color-neutral-50)' }}>
              {footer}
            </div>
          )}
        </DialogPanel>
      </div>
    </Dialog>
  );
}

export default Modal;