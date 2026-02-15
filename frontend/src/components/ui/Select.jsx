import { Listbox, ListboxButton, ListboxOptions, ListboxOption, Field, Label, Description } from '@headlessui/react';
import { ChevronDown, Check } from 'lucide-react';

function Select({ 
  label, 
  options = [], 
  value, 
  onChange, 
  error, 
  helperText,
  placeholder = 'Select an option',
  className = '',
  ...props 
}) {
  const selectedOption = options.find(opt => opt.value === value);

  return (
    <Field>
      {label && (
        <Label className="label-text mb-2 block">
          {label}
        </Label>
      )}
      <Listbox value={value} onChange={onChange} {...props}>
        <div className="relative">
          <ListboxButton 
            className={`w-full px-4 py-3 rounded-xl focus:outline-hidden focus:ring-2 focus:ring-[var(--color-primary-500)] smooth-transition bg-white text-left flex items-center justify-between font-medium
              ${error ? 'border-2 border-[var(--color-error)]' : 'border border-[var(--color-neutral-300)] hover:border-[var(--color-neutral-400)]'}
              ${className}`}
          >
            <span style={{ color: selectedOption ? 'var(--color-text-primary)' : 'var(--color-neutral-400)' }}>
              {selectedOption ? selectedOption.label : placeholder}
            </span>
            <ChevronDown className="w-5 h-5" style={{ color: 'var(--color-neutral-500)' }} />
          </ListboxButton>
          <ListboxOptions 
            anchor="bottom start"
            className="floating-island mt-2 w-[var(--button-width)] max-h-60 overflow-auto focus:outline-hidden z-50"
          >
            {options.map((option) => (
              <ListboxOption
                key={option.value}
                value={option.value}
                className="px-4 py-3 cursor-pointer smooth-transition data-[focus]:bg-[var(--color-primary-50)] data-[selected]:bg-[var(--color-primary-100)] flex items-center justify-between font-medium"
              >
                <span>{option.label}</span>
                {value === option.value && (
                  <Check className="w-5 h-5" style={{ color: 'var(--color-primary-600)' }} />
                )}
              </ListboxOption>
            ))}
          </ListboxOptions>
        </div>
      </Listbox>
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

export default Select;