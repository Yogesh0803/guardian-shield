import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Server,
  ArrowLeft,
  Wifi,
  WifiOff,
  AlertTriangle,
  AppWindow,
  Clock,
  Shield,
  Activity,
  Globe,
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Skeleton, StatCardSkeleton } from '../components/ui/Skeleton';
import { endpointService } from '../services/endpoint.service';
import type { Endpoint, Application, Alert } from '../types';

const statusConfig: Record<
  Endpoint['status'],
  { variant: 'success' | 'danger' | 'warning'; label: string; icon: React.ReactNode }
> = {
  active: { variant: 'success', label: 'Active', icon: <Wifi size={14} /> },
  inactive: { variant: 'danger', label: 'Inactive', icon: <WifiOff size={14} /> },
  warning: { variant: 'warning', label: 'Warning', icon: <AlertTriangle size={14} /> },
};

const appStatusVariant: Record<Application['status'], 'success' | 'danger'> = {
  running: 'success',
  stopped: 'danger',
};

const severityVariant: Record<Alert['severity'], 'danger' | 'warning' | 'info' | 'default'> = {
  critical: 'danger',
  high: 'danger',
  medium: 'warning',
  low: 'info',
  info: 'default',
};

const EndpointDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [endpoint, setEndpoint] = useState<Endpoint | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const fetchEndpoint = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await endpointService.getById(id);
        setEndpoint(data);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to fetch endpoint details';
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    fetchEndpoint();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 p-6 lg:p-8">
        <Skeleton className="h-8 w-48 mb-8" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
        <Skeleton className="h-64 w-full mb-6" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !endpoint) {
    return (
      <div className="min-h-screen bg-gray-950 p-6 lg:p-8">
        <Button variant="ghost" icon={<ArrowLeft size={16} />} onClick={() => navigate('/endpoints')}>
          Back to Endpoints
        </Button>
        <Card className="mt-6 border-red-500/30">
          <CardContent className="py-12 text-center">
            <AlertTriangle className="mx-auto text-red-400 mb-4" size={40} />
            <h3 className="text-lg font-medium text-gray-200 mb-1">Error Loading Endpoint</h3>
            <p className="text-gray-400 text-sm">{error || 'Endpoint not found'}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const cfg = statusConfig[endpoint.status];

  return (
    <div className="min-h-screen bg-gray-950 p-6 lg:p-8">
      {/* Back button */}
      <Button
        variant="ghost"
        icon={<ArrowLeft size={16} />}
        onClick={() => navigate('/endpoints')}
        className="mb-6"
      >
        Back to Endpoints
      </Button>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 flex items-center justify-center">
            <Server size={24} className="text-cyan-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-100">{endpoint.name}</h1>
            <p className="text-gray-400 font-mono text-sm">{endpoint.ip_address}</p>
          </div>
        </div>
        <Button
          variant="primary"
          icon={<Shield size={16} />}
          onClick={() => navigate(`/policies/new?endpoint=${endpoint.id}`)}
        >
          Create Policy for Endpoint
        </Button>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center">
              {cfg.icon}
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wider">Status</p>
              <Badge variant={cfg.variant} dot>
                {cfg.label}
              </Badge>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
              <AppWindow size={18} className="text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wider">Applications</p>
              <p className="text-xl font-bold text-gray-100">{endpoint.applications?.length ?? 0}</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
              <Activity size={18} className="text-amber-400" />
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wider">Traffic Logs</p>
              <p className="text-xl font-bold text-gray-100">
                {endpoint.traffic_logs?.toLocaleString() ?? 0}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
              <Clock size={18} className="text-purple-400" />
            </div>
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wider">Created</p>
              <p className="text-sm font-medium text-gray-200">
                {new Date(endpoint.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'short',
                  day: 'numeric',
                })}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Applications */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <AppWindow size={18} className="text-cyan-400" />
              Applications
            </h2>
          </CardHeader>
          <CardContent>
            {(!endpoint.applications || endpoint.applications.length === 0) ? (
              <div className="text-center py-8">
                <AppWindow className="mx-auto text-gray-600 mb-3" size={36} />
                <p className="text-gray-400 text-sm">No applications registered</p>
              </div>
            ) : (
              <div className="space-y-3">
                {endpoint.applications.map((app) => (
                  <div
                    key={app.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-gray-900/50 border border-gray-700/30 hover:border-gray-600/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                        <AppWindow size={14} className="text-blue-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-200">{app.name}</p>
                        <p className="text-xs text-gray-500 font-mono">{app.process_name}</p>
                      </div>
                    </div>
                    <Badge variant={appStatusVariant[app.status]} dot>
                      {app.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <AlertTriangle size={18} className="text-amber-400" />
              Recent Alerts
            </h2>
          </CardHeader>
          <CardContent>
            {(!endpoint.recent_alerts || endpoint.recent_alerts.length === 0) ? (
              <div className="text-center py-8">
                <Shield className="mx-auto text-gray-600 mb-3" size={36} />
                <p className="text-gray-400 text-sm">No recent alerts -- all clear</p>
              </div>
            ) : (
              <div className="space-y-3">
                {endpoint.recent_alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-3 rounded-xl bg-gray-900/50 border border-gray-700/30"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant={severityVariant[alert.severity]}>
                        {alert.severity.toUpperCase()}
                      </Badge>
                      <span className="text-xs text-gray-500">
                        {new Date(alert.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-200 mb-1">{alert.message}</p>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      {alert.attack_type && (
                        <span className="flex items-center gap-1">
                          <Globe size={12} />
                          {alert.attack_type}
                        </span>
                      )}
                      {alert.app_name && (
                        <span className="flex items-center gap-1">
                          <AppWindow size={12} />
                          {alert.app_name}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Policies Section */}
      {endpoint.policies && endpoint.policies.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <Shield size={18} className="text-cyan-400" />
              Active Policies
            </h2>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {endpoint.policies.map((policy) => (
                <div
                  key={policy.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-gray-900/50 border border-gray-700/30 hover:border-gray-600/50 transition-colors cursor-pointer"
                  onClick={() => navigate(`/policies`)}
                >
                  <div>
                    <p className="text-sm font-medium text-gray-200">{policy.name}</p>
                    <p className="text-xs text-gray-500">{policy.description}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={policy.purpose === 'block' ? 'danger' : 'success'}>
                      {policy.purpose}
                    </Badge>
                    {policy.is_active && (
                      <Badge variant="info" dot>
                        Active
                      </Badge>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default EndpointDetail;
