import { Textarea as HeadlessTextarea, Field, Label, Description } from '@headlessui/react';

function Textarea({ 
  label, 
  error, 
  helperText,
  rows = 4,
  className = '',
  ...props 
}) {
  return (
    <Field>
      {label && (
        <Label className="label-text mb-2 block">
          {label}
        </Label>
      )}
      <HeadlessTextarea
        rows={rows}
        className={`w-full px-4 py-3 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-[var(--color-primary-500)] smooth-transition font-medium resize-y
          ${error ? 'border-2 border-[var(--color-error)]' : 'border border-[var(--color-neutral-300)]'}
          ${props.disabled ? 'bg-[var(--color-neutral-100)] cursor-not-allowed' : 'bg-white hover:border-[var(--color-neutral-400)]'}
          ${className}`}
        style={{ color: 'var(--color-text-primary)' }}
        {...props}
      />
      {error && (
        <Description className="mt-2 text-sm font-medium" style={{ color: 'var(--color-error)' }}>
          {error}
        </Description>
      )}
      {helperText && !error && (
        <Description className="mt-2 text-sm" style={{ color: 'var(--color-neutral-500)' }}>
          {helperText}
        </Description>
      )}
    </Field>
  );
}

export default Textarea;