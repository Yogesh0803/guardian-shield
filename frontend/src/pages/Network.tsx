import React, { useState, useCallback, useMemo } from 'react';
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Box,
  Filter,
  Network as NetworkIcon,
  Search,
  Wifi,
  WifiOff,
} from 'lucide-react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Skeleton, StatCardSkeleton, ChartSkeleton } from '../components/ui/Skeleton';
import { useWebSocket } from '../hooks/useWebSocket';
import type { NetworkUsage, ConnectionInfo, WSNetworkMessage } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const MAX_CHART_POINTS = 30;

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

const connectionStatusVariant: Record<ConnectionInfo['status'], 'success' | 'warning' | 'info' | 'default'> = {
  ESTABLISHED: 'success',
  CLOSE_WAIT: 'warning',
  TIME_WAIT: 'info',
  LISTEN: 'default',
};

const Network: React.FC = () => {
  const [trafficHistory, setTrafficHistory] = useState<{ time: string; bytesIn: number; bytesOut: number }[]>([]);
  const [latestUsage, setLatestUsage] = useState<Record<string, NetworkUsage>>({});
  const [connections, setConnections] = useState<ConnectionInfo[]>([]);
  const [connSearch, setConnSearch] = useState('');
  const [hasData, setHasData] = useState(false);

  // Process WebSocket messages
  const handleMessage = useCallback((data: unknown) => {
    const msg = data as { type: string; data: unknown };

    if (msg.type === 'network_usage') {
      const usageMap = msg.data as Record<string, NetworkUsage>;
      setLatestUsage(usageMap);
      setHasData(true);

      // Aggregate totals for chart
      let totalIn = 0;
      let totalOut = 0;
      Object.values(usageMap).forEach((u) => {
        totalIn += u.bytes_in;
        totalOut += u.bytes_out;
      });

      const time = new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });

      setTrafficHistory((prev) => {
        const next = [...prev, { time, bytesIn: totalIn, bytesOut: totalOut }];
        return next.slice(-MAX_CHART_POINTS);
      });
    }

    if (msg.type === 'connections') {
      setConnections(msg.data as unknown as ConnectionInfo[]);
    }
  }, []);

  const { isConnected } = useWebSocket({
    path: '/ws/network',
    onMessage: handleMessage,
  });

  // Aggregated stats
  const stats = useMemo(() => {
    const values = Object.values(latestUsage);
    const totalPackets = values.reduce((s, u) => s + u.packets, 0);
    const totalBytesIn = values.reduce((s, u) => s + u.bytes_in, 0);
    const totalBytesOut = values.reduce((s, u) => s + u.bytes_out, 0);
    const avgPacketSize =
      values.length > 0
        ? values.reduce((s, u) => s + u.avg_packet_size, 0) / values.length
        : 0;
    return { totalPackets, totalBytesIn, totalBytesOut, avgPacketSize };
  }, [latestUsage]);

  // Line chart data
  const lineChartData = useMemo(
    () => ({
      labels: trafficHistory.map((t) => t.time),
      datasets: [
        {
          label: 'Bytes In',
          data: trafficHistory.map((t) => t.bytesIn),
          borderColor: 'rgb(34, 211, 238)',
          backgroundColor: 'rgba(34, 211, 238, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          borderWidth: 2,
        },
        {
          label: 'Bytes Out',
          data: trafficHistory.map((t) => t.bytesOut),
          borderColor: 'rgb(99, 102, 241)',
          backgroundColor: 'rgba(99, 102, 241, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          borderWidth: 2,
        },
      ],
    }),
    [trafficHistory]
  );

  const lineChartOptions = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#9ca3af', usePointStyle: true, pointStyle: 'circle' as const },
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#f3f4f6',
          bodyColor: '#d1d5db',
          borderColor: 'rgba(75, 85, 99, 0.3)',
          borderWidth: 1,
          callbacks: {
            label: (ctx: { dataset: { label?: string }; parsed: { y: number } }) =>
              `${ctx.dataset.label}: ${formatBytes(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: '#6b7280', maxTicksLimit: 10 }, grid: { color: 'rgba(55, 65, 81, 0.3)' } },
        y: {
          ticks: {
            color: '#6b7280',
            callback: (value: string | number) => formatBytes(Number(value)),
          },
          grid: { color: 'rgba(55, 65, 81, 0.3)' },
        },
      },
    }),
    []
  );

  // Bar chart data for per-endpoint comparison
  const barChartData = useMemo(() => {
    const entries = Object.values(latestUsage);
    return {
      labels: entries.map((u) => u.endpoint_name || u.endpoint_id),
      datasets: [
        {
          label: 'Bytes In',
          data: entries.map((u) => u.bytes_in),
          backgroundColor: 'rgba(34, 211, 238, 0.6)',
          borderColor: 'rgb(34, 211, 238)',
          borderWidth: 1,
          borderRadius: 6,
        },
        {
          label: 'Bytes Out',
          data: entries.map((u) => u.bytes_out),
          backgroundColor: 'rgba(99, 102, 241, 0.6)',
          borderColor: 'rgb(99, 102, 241)',
          borderWidth: 1,
          borderRadius: 6,
        },
      ],
    };
  }, [latestUsage]);

  const barChartOptions = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#9ca3af', usePointStyle: true, pointStyle: 'circle' as const },
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 39, 0.95)',
          titleColor: '#f3f4f6',
          bodyColor: '#d1d5db',
          callbacks: {
            label: (ctx: { dataset: { label?: string }; parsed: { y: number } }) =>
              `${ctx.dataset.label}: ${formatBytes(ctx.parsed.y)}`,
          },
        },
      },
      scales: {
        x: { ticks: { color: '#6b7280' }, grid: { color: 'rgba(55, 65, 81, 0.3)' } },
        y: {
          ticks: {
            color: '#6b7280',
            callback: (value: string | number) => formatBytes(Number(value)),
          },
          grid: { color: 'rgba(55, 65, 81, 0.3)' },
        },
      },
    }),
    []
  );

  // Filtered connections
  const filteredConnections = useMemo(() => {
    if (!connSearch.trim()) return connections;
    const q = connSearch.toLowerCase();
    return connections.filter(
      (c) =>
        c.app.toLowerCase().includes(q) ||
        c.endpoint.toLowerCase().includes(q) ||
        c.src_ip.includes(q) ||
        c.dst_ip.includes(q) ||
        c.status.toLowerCase().includes(q) ||
        c.protocol.toLowerCase().includes(q)
    );
  }, [connections, connSearch]);

  return (
    <div className="min-h-screen bg-gray-950 p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-3">
            <NetworkIcon className="text-cyan-500" size={28} />
            Network Monitoring
          </h1>
          <p className="text-gray-400 mt-1">Real-time network traffic and connection analysis</p>
        </div>
        <Badge variant={isConnected ? 'success' : 'danger'} dot>
          {isConnected ? (
            <span className="flex items-center gap-1">
              <Wifi size={12} /> Live Stream
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <WifiOff size={12} /> Disconnected
            </span>
          )}
        </Badge>
      </div>

      {/* Stats Cards */}
      {!hasData ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center">
                <Box size={18} className="text-cyan-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider">Total Packets</p>
                <p className="text-xl font-bold text-gray-100">
                  {stats.totalPackets.toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                <ArrowDownRight size={18} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider">Bytes In</p>
                <p className="text-xl font-bold text-gray-100">
                  {formatBytes(stats.totalBytesIn)}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center">
                <ArrowUpRight size={18} className="text-indigo-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider">Bytes Out</p>
                <p className="text-xl font-bold text-gray-100">
                  {formatBytes(stats.totalBytesOut)}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                <Activity size={18} className="text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider">Avg Packet Size</p>
                <p className="text-xl font-bold text-gray-100">
                  {formatBytes(stats.avgPacketSize)}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Line Chart */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <Activity size={18} className="text-cyan-400" />
              Real-Time Traffic
            </h2>
          </CardHeader>
          <CardContent>
            {trafficHistory.length < 2 ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-center">
                  <Activity className="mx-auto text-gray-600 mb-3 animate-pulse" size={32} />
                  <p className="text-sm text-gray-500">Waiting for traffic data...</p>
                </div>
              </div>
            ) : (
              <div className="h-64">
                <Line data={lineChartData} options={lineChartOptions} />
              </div>
            )}
          </CardContent>
        </Card>

        {/* Bar Chart */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <NetworkIcon size={18} className="text-cyan-400" />
              Per-Endpoint Usage
            </h2>
          </CardHeader>
          <CardContent>
            {Object.keys(latestUsage).length === 0 ? (
              <div className="h-64 flex items-center justify-center">
                <div className="text-center">
                  <NetworkIcon className="mx-auto text-gray-600 mb-3 animate-pulse" size={32} />
                  <p className="text-sm text-gray-500">Waiting for endpoint data...</p>
                </div>
              </div>
            ) : (
              <div className="h-64">
                <Bar data={barChartData} options={barChartOptions} />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Connections Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <NetworkIcon size={18} className="text-cyan-400" />
              Active Connections
              {connections.length > 0 && (
                <Badge variant="info">{connections.length}</Badge>
              )}
            </h2>
            <div className="w-64">
              <Input
                placeholder="Filter connections..."
                value={connSearch}
                onChange={(e) => setConnSearch(e.target.value)}
                icon={<Search size={14} />}
              />
            </div>
          </div>
        </CardHeader>
        <div className="overflow-x-auto">
          {connections.length === 0 ? (
            <CardContent className="py-12 text-center">
              <NetworkIcon className="mx-auto text-gray-600 mb-3" size={36} />
              <p className="text-sm text-gray-500">No active connections</p>
            </CardContent>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/50">
                  {['Endpoint', 'App', 'Status', 'Source', 'Destination', 'Protocol'].map((h) => (
                    <th
                      key={h}
                      className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider"
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/30">
                {filteredConnections.map((conn) => (
                  <tr
                    key={conn.id}
                    className="hover:bg-gray-700/20 transition-colors duration-150"
                  >
                    <td className="px-6 py-3 text-sm text-gray-300">{conn.endpoint}</td>
                    <td className="px-6 py-3 text-sm text-gray-300">{conn.app}</td>
                    <td className="px-6 py-3">
                      <Badge variant={connectionStatusVariant[conn.status]}>
                        {conn.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-400 font-mono">
                      {conn.src_ip}:{conn.src_port}
                    </td>
                    <td className="px-6 py-3 text-sm text-gray-400 font-mono">
                      {conn.dst_ip}:{conn.dst_port}
                    </td>
                    <td className="px-6 py-3">
                      <Badge variant="default">{conn.protocol}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
};

export default Network;
