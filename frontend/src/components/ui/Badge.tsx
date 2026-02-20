import React from 'react';

type Variant = 'success' | 'danger' | 'warning' | 'info' | 'default';

const variants: Record<Variant, string> = {
  success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  danger: 'bg-red-500/10 text-red-400 border-red-500/20',
  warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  info: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
  default: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
};

interface BadgeProps {
  children: React.ReactNode;
  variant?: Variant;
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'default', dot = false, className = '' }) => (
  <span
    className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 text-xs font-medium rounded-full border ${variants[variant]} ${className}`}
  >
    {dot && <span className={`w-1.5 h-1.5 rounded-full bg-current animate-pulse`} />}
    {children}
  </span>
);
