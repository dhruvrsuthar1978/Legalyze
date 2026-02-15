function Badge({ variant = 'default', children, className = '' }) {
  const variants = {
    default: 'bg-[var(--color-neutral-100)] text-[var(--color-neutral-700)]',
    low: 'risk-badge-low',
    medium: 'risk-badge-medium',
    high: 'risk-badge-high',
    success: 'bg-[var(--color-success-light)] text-[var(--color-success)]',
    error: 'bg-[var(--color-error-light)] text-[var(--color-error)]',
    warning: 'bg-[var(--color-warning-light)] text-[var(--color-warning)]',
    info: 'bg-[var(--color-info-light)] text-[var(--color-info)]',
  };

  return (
    <span className={`inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wide ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
}

export default Badge;