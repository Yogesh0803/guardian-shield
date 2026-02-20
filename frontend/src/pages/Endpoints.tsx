import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Plus,
  Server,
  ChevronRight,
  Shield,
  Wifi,
  WifiOff,
  AlertTriangle,
  AppWindow,
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Skeleton, TableSkeleton } from '../components/ui/Skeleton';
import { endpointService } from '../services/endpoint.service';
import type { Endpoint } from '../types';

const statusConfig: Record<Endpoint['status'], { variant: 'success' | 'danger' | 'warning'; icon: React.ReactNode }> = {
  active: { variant: 'success', icon: <Wifi size={14} /> },
  inactive: { variant: 'danger', icon: <WifiOff size={14} /> },
  warning: { variant: 'warning', icon: <AlertTriangle size={14} /> },
};

const Endpoints: React.FC = () => {
  const navigate = useNavigate();
  const [endpoints, setEndpoints] = useState<Endpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  // Add App modal state
  const [addAppModal, setAddAppModal] = useState(false);
  const [selectedEndpointId, setSelectedEndpointId] = useState<string | null>(null);
  const [appName, setAppName] = useState('');
  const [addingApp, setAddingApp] = useState(false);

  useEffect(() => {
    fetchEndpoints();
  }, []);

  const fetchEndpoints = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await endpointService.getAll();
      setEndpoints(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to fetch endpoints';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const filtered = useMemo(() => {
    if (!search.trim()) return endpoints;
    const q = search.toLowerCase();
    return endpoints.filter(
      (ep) =>
        ep.name.toLowerCase().includes(q) ||
        ep.ip_address.toLowerCase().includes(q) ||
        ep.status.toLowerCase().includes(q)
    );
  }, [endpoints, search]);

  const handleAddApp = async () => {
    if (!selectedEndpointId || !appName.trim()) return;
    try {
      setAddingApp(true);
      await endpointService.addApp(selectedEndpointId, appName.trim());
      setAddAppModal(false);
      setAppName('');
      setSelectedEndpointId(null);
      await fetchEndpoints();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to add application';
      setError(message);
    } finally {
      setAddingApp(false);
    }
  };

  const openAddAppModal = (e: React.MouseEvent, endpointId: string) => {
    e.stopPropagation();
    setSelectedEndpointId(endpointId);
    setAddAppModal(true);
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-3">
            <Server className="text-cyan-500" size={28} />
            Endpoint Management
          </h1>
          <p className="text-gray-400 mt-1">Monitor and manage your protected endpoints</p>
        </div>
        <Button
          variant="primary"
          icon={<Shield size={16} />}
          onClick={() => navigate('/policies/new')}
        >
          Deploy Policy
        </Button>
      </div>

      {/* Search Bar */}
      <div className="mb-6 max-w-md">
        <Input
          placeholder="Search endpoints by name, IP, or status..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          icon={<Search size={16} />}
        />
      </div>

      {/* Error State */}
      {error && (
        <Card className="mb-6 border-red-500/30">
          <CardContent>
            <p className="text-red-400 text-sm">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent>
            <TableSkeleton rows={6} />
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!loading && !error && filtered.length === 0 && (
        <Card>
          <CardContent className="py-16 text-center">
            <Server className="mx-auto text-gray-600 mb-4" size={48} />
            <h3 className="text-lg font-medium text-gray-300 mb-1">
              {search ? 'No matching endpoints' : 'No endpoints found'}
            </h3>
            <p className="text-gray-500 text-sm">
              {search
                ? 'Try adjusting your search query'
                : 'Endpoints will appear here once agents are connected'}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Endpoints Table */}
      {!loading && filtered.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
                {filtered.length} Endpoint{filtered.length !== 1 ? 's' : ''}
              </h2>
            </div>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/50">
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="text-left px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Apps
                  </th>
                  <th className="text-right px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/30">
                {filtered.map((ep) => {
                  const cfg = statusConfig[ep.status];
                  return (
                    <tr
                      key={ep.id}
                      onClick={() => navigate(`/endpoints/${ep.id}`)}
                      className="hover:bg-gray-700/20 cursor-pointer transition-colors duration-150"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                            <Server size={16} className="text-cyan-400" />
                          </div>
                          <span className="text-sm font-medium text-gray-200">{ep.name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm text-gray-400 font-mono">{ep.ip_address}</span>
                      </td>
                      <td className="px-6 py-4">
                        <Badge variant={cfg.variant} dot>
                          {cfg.icon}
                          <span className="ml-1 capitalize">{ep.status}</span>
                        </Badge>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <AppWindow size={14} className="text-gray-500" />
                          <span className="text-sm text-gray-300">
                            {ep.applications?.length ?? 0}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<Plus size={14} />}
                            onClick={(e) => openAddAppModal(e, ep.id)}
                          >
                            Add App
                          </Button>
                          <ChevronRight size={16} className="text-gray-500" />
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Add App Modal */}
      <Modal isOpen={addAppModal} onClose={() => setAddAppModal(false)} title="Add Application">
        <div className="space-y-4">
          <Input
            label="Application Name"
            placeholder="e.g., nginx, postgres, redis"
            value={appName}
            onChange={(e) => setAppName(e.target.value)}
            icon={<AppWindow size={16} />}
          />
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setAddAppModal(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleAddApp}
              loading={addingApp}
              disabled={!appName.trim()}
            >
              Add Application
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Endpoints;
