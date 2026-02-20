import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Server,
  Shield,
  AlertTriangle,
  Activity,
  Brain,
  Menu,
  X,
  LogOut,
  ChevronLeft,
  User,
} from 'lucide-react';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/endpoints', icon: Server, label: 'Endpoints' },
  { path: '/policies', icon: Shield, label: 'Policies' },
  { path: '/alerts', icon: AlertTriangle, label: 'Alerts' },
  { path: '/network', icon: Activity, label: 'Network' },
  { path: '/ml', icon: Brain, label: 'ML Engine' },
];

export const DashboardLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full z-50 bg-gray-900/95 backdrop-blur-md border-r border-gray-800
          transition-all duration-300 flex flex-col
          ${sidebarOpen ? 'w-64' : 'w-20'}
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-6 border-b border-gray-800">
          <div className="relative flex-shrink-0">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <Shield size={20} className="text-white" />
            </div>
            <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-gray-900 animate-pulse" />
          </div>
          {sidebarOpen && (
            <div className="overflow-hidden">
              <h1 className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent leading-tight">
                Guardian Shield
              </h1>
              <p className="text-[10px] text-gray-500 uppercase tracking-widest">Context-Aware Firewall</p>
            </div>
          )}
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {navItems.map(({ path, icon: Icon, label }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group
                ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-sm shadow-cyan-500/5'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                }`
              }
            >
              <Icon size={20} className="flex-shrink-0" />
              {sidebarOpen && <span className="text-sm font-medium">{label}</span>}
            </NavLink>
          ))}
        </nav>

        {/* User section */}
        <div className="border-t border-gray-800 p-4">
          {sidebarOpen ? (
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-sm font-bold text-white flex-shrink-0">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">{user?.name || 'User'}</p>
                <p className="text-xs text-gray-500 truncate">{user?.role || 'admin'}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                title="Logout"
              >
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
              title="Logout"
            >
              <LogOut size={18} />
            </button>
          )}
        </div>

        {/* Collapse toggle (desktop) */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="hidden lg:flex absolute -right-3 top-20 w-6 h-6 bg-gray-800 border border-gray-700 rounded-full
            items-center justify-center text-gray-400 hover:text-white hover:border-cyan-500/50 transition-colors"
        >
          <ChevronLeft size={14} className={`transition-transform duration-300 ${sidebarOpen ? '' : 'rotate-180'}`} />
        </button>
      </aside>

      {/* Main content */}
      <main className={`transition-all duration-300 ${sidebarOpen ? 'lg:ml-64' : 'lg:ml-20'}`}>
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-gray-950/80 backdrop-blur-md border-b border-gray-800/50">
          <div className="flex items-center justify-between px-6 py-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="lg:hidden p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800"
            >
              <Menu size={20} />
            </button>
            <div className="flex items-center gap-4 ml-auto">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-medium text-emerald-400">System Active</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
