import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({ children, className = '', hover = false }) => (
  <div
    className={`bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-2xl ${
      hover ? 'hover:border-cyan-500/30 hover:shadow-lg hover:shadow-cyan-500/5 transition-all duration-300' : ''
    } ${className}`}
  >
    {children}
  </div>
);

export const CardHeader: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <div className={`px-6 py-4 border-b border-gray-700/50 ${className}`}>{children}</div>;

export const CardContent: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => <div className={`px-6 py-4 ${className}`}>{children}</div>;
