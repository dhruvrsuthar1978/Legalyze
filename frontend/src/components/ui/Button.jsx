import { Button as HeadlessButton } from '@headlessui/react';

function Button({ 
  variant = 'primary', 
  size = 'md', 
  children, 
  className = '', 
  disabled = false,
  loading = false,
  ...props 
}) {
  const baseStyles = 'inline-flex items-center justify-center font-semibold transition-all duration-300 focus:outline-hidden focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed smooth-transition';
  
  const variants = {
    primary: 'bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)] focus:ring-[var(--color-primary-500)] shadow-sm hover:shadow-lg active:scale-95',
    secondary: 'bg-[var(--color-accent-blue)] text-white hover:bg-[var(--color-primary-700)] focus:ring-[var(--color-accent-blue)] shadow-sm hover:shadow-lg active:scale-95',
    outline: 'border-2 border-[var(--color-primary-600)] text-[var(--color-primary-600)] hover:bg-[var(--color-primary-50)] focus:ring-[var(--color-primary-500)] active:scale-95 dark:border-[var(--color-primary-400)] dark:text-[var(--color-primary-400)] dark:hover:bg-[var(--color-neutral-200)]',
    ghost: 'text-[var(--color-text-primary)] hover:bg-[var(--color-neutral-100)] focus:ring-[var(--color-neutral-400)] active:scale-95',
    danger: 'bg-[var(--color-error)] text-white hover:bg-red-700 focus:ring-red-500 shadow-sm hover:shadow-lg active:scale-95',
    success: 'bg-[var(--color-success)] text-white hover:bg-emerald-700 focus:ring-emerald-500 shadow-sm hover:shadow-lg active:scale-95',
  };
  
  const sizes = {
    xs: 'px-3 py-1.5 text-xs rounded-md',
    sm: 'px-4 py-2 text-sm rounded-lg',
    md: 'px-5 py-2.5 text-base rounded-lg',
    lg: 'px-6 py-3 text-lg rounded-xl',
    xl: 'px-8 py-4 text-xl rounded-xl',
  };

  return (
    <HeadlessButton
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && (
        <svg 
          className="animate-spin -ml-1 mr-2 h-4 w-4" 
          xmlns="http://www.w3.org/2000/svg" 
          fill="none" 
          viewBox="0 0 24 24"
        >
          <circle 
            className="opacity-25" 
            cx="12" 
            cy="12" 
            r="10" 
            stroke="currentColor" 
            strokeWidth="4"
          />
          <path 
            className="opacity-75" 
            fill="currentColor" 
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </HeadlessButton>
  );
}

export default Button;