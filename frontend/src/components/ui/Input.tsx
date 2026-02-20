import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({ label, error, icon, className = '', ...props }) => (
  <div className="space-y-1.5">
    {label && <label className="block text-sm font-medium text-gray-300">{label}</label>}
    <div className="relative">
      {icon && <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">{icon}</div>}
      <input
        className={`w-full bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-200
          placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500/40
          transition-all duration-200 ${icon ? 'pl-10' : ''} ${error ? 'border-red-500/50 focus:ring-red-500/40' : ''}
          ${className}`}
        {...props}
      />
    </div>
    {error && <p className="text-xs text-red-400">{error}</p>}
  </div>
);

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
}

export const Select: React.FC<SelectProps> = ({ label, error, options, className = '', ...props }) => (
  <div className="space-y-1.5">
    {label && <label className="block text-sm font-medium text-gray-300">{label}</label>}
    <select
      className={`w-full bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-200
        focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500/40
        transition-all duration-200 ${error ? 'border-red-500/50' : ''} ${className}`}
      {...props}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
    {error && <p className="text-xs text-red-400">{error}</p>}
  </div>
);

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const Textarea: React.FC<TextareaProps> = ({ label, error, className = '', ...props }) => (
  <div className="space-y-1.5">
    {label && <label className="block text-sm font-medium text-gray-300">{label}</label>}
    <textarea
      className={`w-full bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-200
        placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500/40
        transition-all duration-200 resize-none ${error ? 'border-red-500/50' : ''} ${className}`}
      {...props}
    />
    {error && <p className="text-xs text-red-400">{error}</p>}
  </div>
);
