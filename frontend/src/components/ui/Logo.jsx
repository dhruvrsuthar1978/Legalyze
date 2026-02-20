function Logo({ className = '', size = 'md' }) {
  const sizes = {
    sm: { container: 'w-8 h-8', text: 'text-base' },
    md: { container: 'w-10 h-10', text: 'text-xl' },
    lg: { container: 'w-12 h-12', text: 'text-2xl' },
  };

  const sizeClasses = sizes[size] || sizes.md;

  return (
    <div className={`${sizeClasses.container} rounded-lg flex items-center justify-center ${className}`} style={{ backgroundColor: 'var(--color-primary-600)' }}>
      <span className={`${sizeClasses.text} font-bold text-white`}>L</span>
    </div>
  );
}

export default Logo;
