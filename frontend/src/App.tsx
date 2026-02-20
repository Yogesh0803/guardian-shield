import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { DashboardLayout } from './components/DashboardLayout';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Endpoints from './pages/Endpoints';
import EndpointDetail from './pages/EndpointDetail';
import Policies from './pages/Policies';
import PolicyCreate from './pages/PolicyCreate';
import Alerts from './pages/Alerts';
import Network from './pages/Network';
import MLEngine from './pages/MLEngine';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1f2937',
              color: '#f3f4f6',
              border: '1px solid rgba(75, 85, 99, 0.3)',
              borderRadius: '12px',
            },
            success: { iconTheme: { primary: '#06b6d4', secondary: '#fff' } },
            error: { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
          }}
        />
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/" element={<Dashboard />} />
              <Route path="/endpoints" element={<Endpoints />} />
              <Route path="/endpoints/:id" element={<EndpointDetail />} />
              <Route path="/policies" element={<Policies />} />
              <Route path="/policies/new" element={<PolicyCreate />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/network" element={<Network />} />
              <Route path="/ml" element={<MLEngine />} />
            </Route>
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
