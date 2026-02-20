import React from 'react';

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
type Size = 'sm' | 'md' | 'lg';

const variantStyles: Record<Variant, string> = {
  primary: 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-lg shadow-cyan-500/20',
  secondary: 'bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600',
  danger: 'bg-red-600/80 hover:bg-red-500 text-white',
  ghost: 'hover:bg-gray-700/50 text-gray-400 hover:text-gray-200',
  outline: 'border border-gray-600 hover:border-cyan-500/50 text-gray-300 hover:text-cyan-400',
};

const sizeStyles: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  icon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  className = '',
  disabled,
  ...props
}) => (
  <button
    className={`inline-flex items-center justify-center gap-2 font-medium rounded-xl transition-all duration-200
      ${variantStyles[variant]} ${sizeStyles[size]}
      ${disabled || loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      ${className}`}
    disabled={disabled || loading}
    {...props}
  >
    {loading ? (
      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    ) : icon ? (
      icon
    ) : null}
    {children}
  </button>
);
