import React, { useState, useEffect, useCallback } from 'react';
import {
  Brain,
  Activity,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Bell,
  Cpu,
  RefreshCw,
  Wifi,
  WifiOff,
  TrendingUp,
  Zap,
  Lock,
  BarChart3,
  AppWindow,
  Globe,
  Clock,
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Skeleton, StatCardSkeleton } from '../components/ui/Skeleton';
import { mlService } from '../services/ml.service';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../context/AuthContext';
import type { MLStatus, MLPrediction, WSPredictionMessage } from '../types';

const MAX_PREDICTIONS = 50;

const modelInfo: Record<string, { name: string; description: string; icon: React.ReactNode }> = {
  isolation_forest: {
    name: 'Isolation Forest',
    description: 'Unsupervised anomaly detection using random forest isolation',
    icon: <TrendingUp size={20} className="text-emerald-400" />,
  },
  autoencoder: {
    name: 'Autoencoder',
    description: 'Deep learning reconstruction-based anomaly detection',
    icon: <Brain size={20} className="text-purple-400" />,
  },
  lstm_cnn: {
    name: 'LSTM + CNN',
    description: 'Sequence and pattern recognition for traffic analysis',
    icon: <Activity size={20} className="text-cyan-400" />,
  },
  xgboost: {
    name: 'XGBoost',
    description: 'Gradient boosted attack classification model',
    icon: <Zap size={20} className="text-amber-400" />,
  },
};

const actionConfig: Record<
  MLPrediction['action'],
  { variant: 'success' | 'danger' | 'warning'; icon: React.ReactNode }
> = {
  allow: { variant: 'success', icon: <ShieldCheck size={12} /> },
  block: { variant: 'danger', icon: <ShieldAlert size={12} /> },
  alert: { variant: 'warning', icon: <Bell size={12} /> },
};

// Progress bar component with gradient
const AccuracyBar: React.FC<{ label: string; value: number; color: string }> = ({
  label,
  value,
  color,
}) => {
  const pct = Math.round(value * 100);
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs font-medium text-gray-300">{label}</span>
        <span className="text-xs font-bold text-gray-200">{pct}%</span>
      </div>
      <div className="h-2.5 bg-gray-700/50 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000 ease-out"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${color}, ${color}dd)`,
          }}
        />
      </div>
    </div>
  );
};

const MLEngine: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const [status, setStatus] = useState<MLStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [predictions, setPredictions] = useState<MLPrediction[]>([]);
  const [retraining, setRetraining] = useState(false);
  const [retrainMessage, setRetrainMessage] = useState<string | null>(null);

  // Fetch ML status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await mlService.getStatus();
        setStatus(data);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to fetch ML status';
        setError(message);
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
  }, []);

  // WebSocket for predictions
  const handleMessage = useCallback((data: unknown) => {
    const msg = data as WSPredictionMessage;
    if (msg.type === 'prediction' && msg.data) {
      setPredictions((prev) => [msg.data, ...prev].slice(0, MAX_PREDICTIONS));
    }
  }, []);

  const { isConnected } = useWebSocket({
    path: '/ws/predictions',
    onMessage: handleMessage,
  });

  // Retrain handler
  const handleRetrain = async () => {
    try {
      setRetraining(true);
      setRetrainMessage(null);
      const result = await mlService.retrain();
      setRetrainMessage(result.message);
      // Refresh status after retrain
      const newStatus = await mlService.getStatus();
      setStatus(newStatus);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to retrain models';
      setError(message);
    } finally {
      setRetraining(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6 lg:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-3">
            <Brain className="text-cyan-500" size={28} />
            ML Engine
          </h1>
          <p className="text-gray-400 mt-1">
            Machine learning model status, accuracy, and real-time predictions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={isConnected ? 'success' : 'danger'} dot>
            {isConnected ? (
              <span className="flex items-center gap-1">
                <Wifi size={12} /> Live Predictions
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <WifiOff size={12} /> Disconnected
              </span>
            )}
          </Badge>
          {isAdmin && (
            <Button
              variant="primary"
              icon={<RefreshCw size={16} className={retraining ? 'animate-spin' : ''} />}
              onClick={handleRetrain}
              loading={retraining}
            >
              Retrain Models
            </Button>
          )}
        </div>
      </div>

      {/* Retrain message */}
      {retrainMessage && (
        <Card className="mb-6 border-emerald-500/30">
          <CardContent>
            <p className="text-emerald-400 text-sm">{retrainMessage}</p>
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {error && (
        <Card className="mb-6 border-red-500/30">
          <CardContent>
            <p className="text-red-400 text-sm">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* ML Status Card */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {Array.from({ length: 4 }).map((_, i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
      ) : status ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-cyan-500/10 flex items-center justify-center">
                <Cpu size={18} className="text-cyan-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider">Engine Status</p>
                <Badge variant={status.is_running ? 'success' : 'danger'} dot className="mt-1">
                  {status.is_running ? 'Running' : 'Stopped'}
                </Badge>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                <Activity size={18} className="text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider">Predictions/min</p>
                <p className="text-xl font-bold text-gray-100">
                  {status.predictions_per_minute.toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center">
                <BarChart3 size={18} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider">Total Predictions</p>
                <p className="text-xl font-bold text-gray-100">
                  {status.total_predictions.toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-xl bg-red-500/10 flex items-center justify-center">
                <Shield size={18} className="text-red-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider">Total Blocked</p>
                <p className="text-xl font-bold text-gray-100">
                  {status.total_blocked.toLocaleString()}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Model Cards */}
        <div className="lg:col-span-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(modelInfo).map(([key, info]) => {
              const isLoaded = status?.models_loaded?.includes(key);
              return (
                <Card key={key} hover>
                  <CardContent className="space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gray-700/50 flex items-center justify-center">
                          {info.icon}
                        </div>
                        <div>
                          <h3 className="text-sm font-semibold text-gray-100">{info.name}</h3>
                          <p className="text-xs text-gray-500 mt-0.5">{info.description}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Badge variant={isLoaded ? 'success' : 'danger'} dot>
                        {isLoaded ? 'Loaded' : 'Not Loaded'}
                      </Badge>
                      {!isAdmin && !isLoaded && (
                        <Badge variant="default">
                          <Lock size={10} className="mr-1" />
                          Admin Required
                        </Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Accuracy Card */}
        <Card>
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <BarChart3 size={18} className="text-cyan-400" />
              Model Accuracy
            </h2>
          </CardHeader>
          <CardContent className="space-y-5">
            {loading ? (
              <>
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </>
            ) : status ? (
              <>
                <AccuracyBar
                  label="Anomaly Detector"
                  value={status.accuracy.anomaly_detector}
                  color="#22d3ee"
                />
                <AccuracyBar
                  label="Attack Classifier"
                  value={status.accuracy.attack_classifier}
                  color="#8b5cf6"
                />
              </>
            ) : (
              <p className="text-sm text-gray-500">No accuracy data available</p>
            )}
            {status?.last_retrain && (
              <div className="pt-3 border-t border-gray-700/30">
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <Clock size={12} />
                  Last retrained:{' '}
                  {new Date(status.last_retrain).toLocaleString()}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Real-time Prediction Feed */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
              <Activity size={18} className="text-cyan-400" />
              Real-Time Prediction Feed
              {predictions.length > 0 && (
                <Badge variant="info">{predictions.length}</Badge>
              )}
            </h2>
            {predictions.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPredictions([])}
              >
                Clear
              </Button>
            )}
          </div>
        </CardHeader>
        <div className="overflow-x-auto">
          {predictions.length === 0 ? (
            <CardContent className="py-16 text-center">
              <Brain className="mx-auto text-gray-600 mb-4 animate-pulse" size={48} />
              <h3 className="text-lg font-medium text-gray-300 mb-1">Waiting for Predictions</h3>
              <p className="text-gray-500 text-sm">
                Live ML predictions will appear here as they are processed
              </p>
            </CardContent>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700/50">
                  {['Action', 'Anomaly Score', 'Attack Type', 'Confidence', 'App', 'Source', 'Dest', 'Time'].map(
                    (h) => (
                      <th
                        key={h}
                        className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider"
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700/30">
                {predictions.map((pred) => {
                  const acfg = actionConfig[pred.action];
                  return (
                    <tr
                      key={pred.id}
                      className="hover:bg-gray-700/20 transition-colors duration-150"
                    >
                      <td className="px-5 py-3">
                        <Badge variant={acfg.variant}>
                          {acfg.icon}
                          <span className="ml-1 capitalize">{pred.action}</span>
                        </Badge>
                      </td>
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-gray-700/50 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full"
                              style={{
                                width: `${Math.round(pred.anomaly_score * 100)}%`,
                                background:
                                  pred.anomaly_score > 0.7
                                    ? '#ef4444'
                                    : pred.anomaly_score > 0.4
                                    ? '#f59e0b'
                                    : '#22d3ee',
                              }}
                            />
                          </div>
                          <span className="text-xs text-gray-300 font-mono">
                            {pred.anomaly_score.toFixed(3)}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        {pred.attack_type ? (
                          <Badge variant="warning">{pred.attack_type}</Badge>
                        ) : (
                          <span className="text-xs text-gray-500">--</span>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        <span
                          className={`text-xs font-mono ${
                            pred.confidence > 0.8
                              ? 'text-emerald-400'
                              : pred.confidence > 0.5
                              ? 'text-amber-400'
                              : 'text-gray-400'
                          }`}
                        >
                          {Math.round(pred.confidence * 100)}%
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-xs text-gray-300 flex items-center gap-1">
                          <AppWindow size={12} className="text-gray-500" />
                          {pred.app_name}
                        </span>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-xs text-gray-400 font-mono">{pred.src_ip}</span>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-xs text-gray-400 font-mono">{pred.dst_ip}</span>
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-xs text-gray-500">
                          {new Date(pred.timestamp).toLocaleTimeString()}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  );
};

export default MLEngine;
