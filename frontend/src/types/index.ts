// ==================== User & Auth ====================
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'viewer';
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

// ==================== Endpoint ====================
export interface Endpoint {
  id: string;
  name: string;
  ip_address: string;
  status: 'active' | 'inactive' | 'warning';
  applications: Application[];
  policies: Policy[];
  recent_alerts: Alert[];
  traffic_logs: number;
  created_at: string;
}

export interface Application {
  id: string;
  name: string;
  process_name: string;
  status: 'running' | 'stopped';
  endpoint_id: string;
}

// ==================== Policy ====================
export interface PolicyPort {
  port: number;
  protocol: ('TCP' | 'UDP' | 'ICMP')[];
}

export interface PolicyConditions {
  domains: string[];
  ips: string[];
  ports: PolicyPort[];
  app_names: string[];
  time_range?: { start: string; end: string };
  days_of_week?: number[];
  geo_countries?: string[];
  anomaly_threshold?: number;
  attack_types?: string[];
  rate_limit?: number;
}

export interface Policy {
  id: string;
  name: string;
  description: string;
  purpose: 'block' | 'unblock';
  conditions: PolicyConditions;
  endpoint_id: string;
  created_at: string;
  is_active: boolean;
}

export interface PolicyCreateRequest {
  name: string;
  description: string;
  purpose: 'block' | 'unblock';
  conditions: PolicyConditions;
  endpoint_id?: string;
  natural_language?: string;
}

// ==================== Alert ====================
export interface Alert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: 'normal' | 'abnormal';
  attack_type: string;
  message: string;
  confidence: number;
  app_id?: string;
  app_name?: string;
  endpoint_id: string;
  endpoint_name?: string;
  timestamp: string;
}

// ==================== Network ====================
export interface NetworkUsage {
  id: string;
  endpoint_id: string;
  endpoint_name?: string;
  bytes_in: number;
  bytes_out: number;
  packets: number;
  avg_packet_size: number;
  timestamp: string;
}

export interface ConnectionInfo {
  id: string;
  endpoint: string;
  app: string;
  status: 'ESTABLISHED' | 'CLOSE_WAIT' | 'TIME_WAIT' | 'LISTEN';
  src_ip: string;
  dst_ip: string;
  src_port: number;
  dst_port: number;
  protocol: string;
}

// ==================== ML ====================
export interface MLPrediction {
  id: string;
  anomaly_score: number;
  attack_type: string;
  confidence: number;
  action: 'allow' | 'block' | 'alert';
  app_name: string;
  src_ip: string;
  dst_ip: string;
  context: FlowContext;
  timestamp: string;
}

export interface FlowContext {
  app_name: string;
  process_id: number;
  app_trust_score: number;
  hour: number;
  day_of_week: number;
  is_business_hours: boolean;
  time_since_last_request: number;
  rate_deviation: number;
  size_deviation: number;
  destination_novelty: number;
  dest_country: string;
  dest_asn: string;
  is_geo_anomaly: boolean;
}

export interface MLStatus {
  is_running: boolean;
  models_loaded: string[];
  predictions_per_minute: number;
  last_retrain: string;
  accuracy: {
    anomaly_detector: number;
    attack_classifier: number;
  };
  total_predictions: number;
  total_blocked: number;
}

// ==================== Attack ====================
export interface AttackStats {
  type: string;
  count: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

// ==================== Dashboard ====================
export interface DashboardStats {
  total_endpoints: number;
  active_endpoints: number;
  total_alerts: number;
  critical_alerts: number;
  total_policies: number;
  active_policies: number;
  blocked_threats: number;
  total_traffic_mb: number;
}

// ==================== NLP Policy ====================
export interface NLPPolicyParse {
  name: string;
  description: string;
  input: string;
  parsed: PolicyConditions;
  purpose: 'block' | 'unblock';
  confidence: number;
  explanation: string;
}

// ==================== WebSocket Messages ====================
export interface WSNetworkMessage {
  type: 'network_usage';
  data: Record<string, NetworkUsage>;
}

export interface WSAlertMessage {
  type: 'alert';
  data: Alert;
}

export interface WSPredictionMessage {
  type: 'prediction';
  data: MLPrediction;
}

export type WSMessage = WSNetworkMessage | WSAlertMessage | WSPredictionMessage;
