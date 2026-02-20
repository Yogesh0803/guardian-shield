import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield, Server, AlertTriangle, Activity, Brain, TrendingUp,
  ArrowUpRight, ArrowDownRight, Zap, Globe,
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ChartSkeleton, StatCardSkeleton } from '../components/ui/Skeleton';
import { useWebSocket } from '../hooks/useWebSocket';
import { endpointService } from '../services/endpoint.service';
import { alertService } from '../services/alert.service';
import { mlService } from '../services/ml.service';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  ArcElement, Tooltip, Legend, Filler,
} from 'chart.js';
import type { Alert, Endpoint, MLStatus, NetworkUsage as NetworkUsageType } from '../types';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, Tooltip, Legend, Filler);

interface StatCardProps {
  title: string;
  value: string | number;
  change?: string;
  trend?: 'up' | 'down';
  icon: React.ReactNode;
  color: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, change, trend, icon, color }) => (
  <Card hover>
    <CardContent className="p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {change && (
            <div className={`flex items-center gap-1 mt-2 text-xs ${trend === 'up' ? 'text-emerald-400' : 'text-red-400'}`}>
              {trend === 'up' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
              {change}
            </div>
          )}
        </div>
        <div className={`p-3 rounded-xl ${color}`}>
          {icon}
        </div>
      </div>
    </CardContent>
  </Card>
);

const Dashboard: React.FC = () => {
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [mlStatus, setMlStatus] = useState<MLStatus | null>(null);
  const [networkData, setNetworkData] = useState<{ labels: string[]; values: number[] }>({
    labels: [],
    values: [],
  });
  const [loading, setLoading] = useState(true);
  const [realtimeAlerts, setRealtimeAlerts] = useState<Alert[]>([]);

  // WebSocket for live network data
  const onNetworkMessage = useCallback((data: unknown) => {
    const msg = data as { type: string; data: Record<string, NetworkUsageType> };
    if (msg.type === 'network_usage') {
      const totalBytes = Object.values(msg.data).reduce(
        (sum, n) => sum + (n.bytes_in || 0) + (n.bytes_out || 0), 0
      );
      setNetworkData((prev) => {
        const now = new Date().toLocaleTimeString();
        const labels = [...prev.labels, now].slice(-20);
        const values = [...prev.values, totalBytes / 1024].slice(-20);
        return { labels, values };
      });
    }
  }, []);

  const onAlertMessage = useCallback((data: unknown) => {
    const msg = data as { type: string; data: Alert };
    if (msg.type === 'alert') {
      setRealtimeAlerts((prev) => [msg.data, ...prev].slice(0, 10));
    }
  }, []);

  useWebSocket({ path: '/ws/network', onMessage: onNetworkMessage });
  useWebSocket({ path: '/ws/alerts', onMessage: onAlertMessage });

  useEffect(() => {
    const load = async () => {
      try {
        const [ep, al, ml] = await Promise.all([
          endpointService.getAll(),
          alertService.getAll({ limit: 10 }),
          mlService.getStatus(),
        ]);
        setEndpoints(ep);
        setAlerts(al);
        setMlStatus(ml);
      } catch {
        // API may not be running yet — show empty state
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const activeEndpoints = endpoints.filter((e) => e.status === 'active').length;
  const criticalAlerts = alerts.filter((a) => a.severity === 'critical' || a.severity === 'high').length;
  const allAlerts = [...realtimeAlerts, ...alerts];

  const attackDistribution = allAlerts.reduce<Record<string, number>>((acc, a) => {
    if (a.attack_type && a.attack_type !== 'benign') {
      acc[a.attack_type] = (acc[a.attack_type] || 0) + 1;
    }
    return acc;
  }, {});

  const severityColor = (s: string) => {
    switch (s) {
      case 'critical': return 'danger';
      case 'high': return 'danger';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <StatCardSkeleton key={i} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ChartSkeleton />
          <ChartSkeleton />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Real-time network security overview</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Endpoints"
          value={activeEndpoints}
          change={`${endpoints.length} total`}
          trend="up"
          icon={<Server size={20} className="text-cyan-400" />}
          color="bg-cyan-500/10"
        />
        <StatCard
          title="Threats Blocked"
          value={mlStatus?.total_blocked || 0}
          change="+12% this hour"
          trend="up"
          icon={<Shield size={20} className="text-emerald-400" />}
          color="bg-emerald-500/10"
        />
        <StatCard
          title="Active Alerts"
          value={criticalAlerts}
          change={`${allAlerts.length} total`}
          trend={criticalAlerts > 0 ? 'down' : 'up'}
          icon={<AlertTriangle size={20} className="text-amber-400" />}
          color="bg-amber-500/10"
        />
        <StatCard
          title="ML Predictions/min"
          value={mlStatus?.predictions_per_minute || 0}
          change={`${(mlStatus?.accuracy?.attack_classifier || 0) * 100}% accuracy`}
          trend="up"
          icon={<Brain size={20} className="text-purple-400" />}
          color="bg-purple-500/10"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Network traffic chart */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity size={18} className="text-cyan-400" />
                <h3 className="font-semibold text-white">Network Traffic</h3>
              </div>
              <Badge variant="info" dot>Live</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <Line
                data={{
                  labels: networkData.labels,
                  datasets: [
                    {
                      label: 'Traffic (KB/s)',
                      data: networkData.values,
                      borderColor: 'rgb(6, 182, 212)',
                      backgroundColor: 'rgba(6, 182, 212, 0.1)',
                      fill: true,
                      tension: 0.4,
                      pointRadius: 0,
                      borderWidth: 2,
                    },
                  ],
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6b7280', maxTicksLimit: 6 } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#6b7280' } },
                  },
                  interaction: { intersect: false, mode: 'index' },
                }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Attack distribution */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Zap size={18} className="text-amber-400" />
              <h3 className="font-semibold text-white">Attack Types</h3>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-64 flex items-center justify-center">
              {Object.keys(attackDistribution).length > 0 ? (
                <Doughnut
                  data={{
                    labels: Object.keys(attackDistribution),
                    datasets: [
                      {
                        data: Object.values(attackDistribution),
                        backgroundColor: [
                          'rgba(239, 68, 68, 0.8)', 'rgba(245, 158, 11, 0.8)',
                          'rgba(6, 182, 212, 0.8)', 'rgba(139, 92, 246, 0.8)',
                          'rgba(236, 72, 153, 0.8)', 'rgba(34, 197, 94, 0.8)',
                        ],
                        borderWidth: 0,
                      },
                    ],
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                      legend: { position: 'bottom', labels: { color: '#9ca3af', padding: 12, usePointStyle: true, pointStyleWidth: 8 } },
                    },
                  }}
                />
              ) : (
                <div className="text-center text-gray-500">
                  <Globe size={40} className="mx-auto mb-2 opacity-30" />
                  <p className="text-sm">No attacks detected</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent alerts + ML status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent alerts */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle size={18} className="text-amber-400" />
                <h3 className="font-semibold text-white">Recent Alerts</h3>
              </div>
              <Badge variant="default">{allAlerts.length}</Badge>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {allAlerts.length > 0 ? (
              <div className="divide-y divide-gray-800">
                {allAlerts.slice(0, 8).map((alert, i) => (
                  <div key={alert.id || i} className="px-6 py-3 flex items-center gap-4 hover:bg-gray-800/30 transition-colors">
                    <Badge variant={severityColor(alert.severity) as 'danger' | 'warning' | 'info' | 'default'} dot>
                      {alert.severity}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-200 truncate">{alert.message}</p>
                      <p className="text-xs text-gray-500">{alert.app_name || alert.attack_type}</p>
                    </div>
                    <span className="text-xs text-gray-500 flex-shrink-0">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center text-gray-500">
                <Shield size={40} className="mx-auto mb-2 opacity-30" />
                <p className="text-sm">No alerts — system is secure</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ML engine status */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Brain size={18} className="text-purple-400" />
              <h3 className="font-semibold text-white">ML Engine</h3>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">Status</span>
              <Badge variant={mlStatus?.is_running ? 'success' : 'danger'} dot>
                {mlStatus?.is_running ? 'Running' : 'Offline'}
              </Badge>
            </div>

            {mlStatus?.models_loaded?.map((model) => (
              <div key={model} className="flex items-center justify-between">
                <span className="text-sm text-gray-400">{model}</span>
                <Badge variant="success">Loaded</Badge>
              </div>
            ))}

            <div className="pt-2 border-t border-gray-700/50 space-y-3">
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Anomaly Detector</span>
                  <span className="text-cyan-400">{((mlStatus?.accuracy?.anomaly_detector || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500"
                    style={{ width: `${(mlStatus?.accuracy?.anomaly_detector || 0) * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-400">Attack Classifier</span>
                  <span className="text-purple-400">{((mlStatus?.accuracy?.attack_classifier || 0) * 100).toFixed(1)}%</span>
                </div>
                <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500"
                    style={{ width: `${(mlStatus?.accuracy?.attack_classifier || 0) * 100}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-gray-700/50">
              <div className="flex justify-between text-xs">
                <span className="text-gray-500">Total predictions</span>
                <span className="text-gray-300">{mlStatus?.total_predictions?.toLocaleString() || 0}</span>
              </div>
              <div className="flex justify-between text-xs mt-1">
                <span className="text-gray-500">Last retrain</span>
                <span className="text-gray-300">
                  {mlStatus?.last_retrain ? new Date(mlStatus.last_retrain).toLocaleDateString() : 'Never'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
