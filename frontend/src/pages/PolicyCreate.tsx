import React, { useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Brain,
  Settings2,
  Sparkles,
  Plus,
  X,
  Send,
  Shield,
  Globe,
  Network,
  Clock,
  AppWindow,
  MapPin,
  Activity,
} from 'lucide-react';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Input, Select, Textarea } from '../components/ui/Input';
import { policyService } from '../services/policy.service';
import type { PolicyConditions, PolicyCreateRequest, NLPPolicyParse } from '../types';

type Mode = 'natural' | 'manual';

const emptyConditions: PolicyConditions = {
  domains: [],
  ips: [],
  ports: [],
  app_names: [],
  time_range: undefined,
  days_of_week: undefined,
  geo_countries: [],
  anomaly_threshold: undefined,
  attack_types: [],
  rate_limit: undefined,
};

// Tag input helper component
const TagInput: React.FC<{
  label: string;
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  icon?: React.ReactNode;
}> = ({ label, tags, onChange, placeholder, icon }) => {
  const [input, setInput] = useState('');

  const addTag = () => {
    const val = input.trim();
    if (val && !tags.includes(val)) {
      onChange([...tags, val]);
    }
    setInput('');
  };

  const removeTag = (tag: string) => {
    onChange(tags.filter((t) => t !== tag));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  };

  return (
    <div className="space-y-1.5">
      <label className="block text-sm font-medium text-gray-300">{label}</label>
      <div className="flex gap-2">
        <div className="flex-1 relative">
          {icon && <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">{icon}</div>}
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={`w-full bg-gray-800/80 border border-gray-700 rounded-xl px-4 py-2.5 text-gray-200
              placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 focus:border-cyan-500/40
              transition-all duration-200 ${icon ? 'pl-10' : ''}`}
          />
        </div>
        <Button variant="secondary" size="md" icon={<Plus size={14} />} onClick={addTag} type="button">
          Add
        </Button>
      </div>
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                className="hover:text-cyan-200 transition-colors"
              >
                <X size={12} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

const PolicyCreate: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedEndpoint = searchParams.get('endpoint') || '';

  const [mode, setMode] = useState<Mode>('natural');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Natural language state
  const [nlInput, setNlInput] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parsedResult, setParsedResult] = useState<NLPPolicyParse | null>(null);

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [purpose, setPurpose] = useState<'block' | 'unblock'>('block');
  const [endpointId, setEndpointId] = useState(preselectedEndpoint);
  const [conditions, setConditions] = useState<PolicyConditions>({ ...emptyConditions });
  const [timeStart, setTimeStart] = useState('');
  const [timeEnd, setTimeEnd] = useState('');

  const updateConditions = useCallback(
    (partial: Partial<PolicyConditions>) => {
      setConditions((prev) => ({ ...prev, ...partial }));
    },
    []
  );

  // Parse natural language
  const handleParse = async () => {
    if (!nlInput.trim()) return;
    try {
      setParsing(true);
      setError(null);
      const result = await policyService.parseNaturalLanguage(nlInput);
      setParsedResult(result);
      // Pre-fill form fields from parsed result
      setName(result.name || `Block: ${nlInput.slice(0, 60)}`);
      setDescription(result.description || nlInput);
      setPurpose(result.purpose);
      setConditions(result.parsed);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to parse policy description';
      setError(message);
    } finally {
      setParsing(false);
    }
  };

  // Submit policy
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Policy name is required');
      return;
    }
    const finalConditions = { ...conditions };
    if (timeStart && timeEnd) {
      finalConditions.time_range = { start: timeStart, end: timeEnd };
    }

    const payload: PolicyCreateRequest = {
      name: name.trim(),
      description: description.trim(),
      purpose,
      conditions: finalConditions,
      ...(endpointId.trim() ? { endpoint_id: endpointId.trim() } : {}),
      ...(mode === 'natural' && nlInput ? { natural_language: nlInput } : {}),
    };

    try {
      setSubmitting(true);
      setError(null);
      await policyService.create(payload);
      navigate('/policies');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create policy';
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 p-6 lg:p-8">
      {/* Back */}
      <Button
        variant="ghost"
        icon={<ArrowLeft size={16} />}
        onClick={() => navigate('/policies')}
        className="mb-6"
      >
        Back to Policies
      </Button>

      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-100 flex items-center gap-3">
          <Shield className="text-cyan-500" size={28} />
          Create Policy
        </h1>
        <p className="text-gray-400 mt-1">
          Define a new firewall rule using natural language or manual configuration
        </p>
      </div>

      {/* Mode Tabs */}
      <div className="flex gap-1 p-1 bg-gray-800/50 rounded-xl w-fit mb-8 border border-gray-700/50">
        <button
          onClick={() => setMode('natural')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
            mode === 'natural'
              ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
          }`}
        >
          <Brain size={16} />
          Natural Language
        </button>
        <button
          onClick={() => setMode('manual')}
          className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
            mode === 'manual'
              ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20'
              : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'
          }`}
        >
          <Settings2 size={16} />
          Manual
        </button>
      </div>

      {/* Error */}
      {error && (
        <Card className="mb-6 border-red-500/30">
          <CardContent>
            <p className="text-red-400 text-sm">{error}</p>
          </CardContent>
        </Card>
      )}

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Natural Language Input */}
            {mode === 'natural' && (
              <Card>
                <CardHeader>
                  <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
                    <Sparkles size={18} className="text-cyan-400" />
                    Describe Your Policy
                  </h2>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Textarea
                    label="Policy Description"
                    placeholder="e.g., Block all traffic from China and Russia to port 443 during business hours for the nginx application, and also block any requests with anomaly scores above 0.8"
                    value={nlInput}
                    onChange={(e) => setNlInput(e.target.value)}
                    rows={5}
                  />
                  <Button
                    type="button"
                    variant="primary"
                    icon={<Brain size={16} />}
                    onClick={handleParse}
                    loading={parsing}
                    disabled={!nlInput.trim()}
                  >
                    Parse with AI
                  </Button>

                  {/* Parsed Result */}
                  {parsedResult && (
                    <div className="mt-4 p-4 rounded-xl bg-gray-900/80 border border-cyan-500/20">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-sm font-semibold text-cyan-400 flex items-center gap-2">
                          <Sparkles size={14} />
                          Parsed Result
                        </h3>
                        <Badge variant={parsedResult.confidence > 0.8 ? 'success' : 'warning'}>
                          {Math.round(parsedResult.confidence * 100)}% confident
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-300 mb-3">{parsedResult.explanation}</p>
                      <div className="flex flex-wrap gap-2 mb-3">
                        <Badge variant={parsedResult.purpose === 'block' ? 'danger' : 'success'}>
                          {parsedResult.purpose}
                        </Badge>
                        {parsedResult.parsed.domains?.map((d) => (
                          <Badge key={d} variant="info">
                            <Globe size={10} className="mr-1" />
                            {d}
                          </Badge>
                        ))}
                        {parsedResult.parsed.geo_countries?.map((c) => (
                          <Badge key={c} variant="warning">
                            <MapPin size={10} className="mr-1" />
                            {c}
                          </Badge>
                        ))}
                        {parsedResult.parsed.app_names?.map((a) => (
                          <Badge key={a} variant="default">
                            <AppWindow size={10} className="mr-1" />
                            {a}
                          </Badge>
                        ))}
                      </div>
                      <p className="text-xs text-gray-500">
                        You can edit the parsed conditions below before submitting.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Manual / Editable Form */}
            <Card>
              <CardHeader>
                <h2 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
                  <Settings2 size={18} className="text-cyan-400" />
                  Policy Configuration
                </h2>
              </CardHeader>
              <CardContent className="space-y-5">
                {/* Name & Description */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Input
                    label="Policy Name"
                    placeholder="e.g., Block Malicious IPs"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                  <Input
                    label="Endpoint ID"
                    placeholder="Endpoint ID"
                    value={endpointId}
                    onChange={(e) => setEndpointId(e.target.value)}
                  />
                </div>
                <Textarea
                  label="Description"
                  placeholder="Describe what this policy does..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                />
                <Select
                  label="Purpose"
                  value={purpose}
                  onChange={(e) => setPurpose(e.target.value as 'block' | 'unblock')}
                  options={[
                    { value: 'block', label: 'Block Traffic' },
                    { value: 'unblock', label: 'Allow Traffic' },
                  ]}
                />

                {/* Domains */}
                <TagInput
                  label="Domains"
                  tags={conditions.domains}
                  onChange={(tags) => updateConditions({ domains: tags })}
                  placeholder="e.g., malicious-site.com"
                  icon={<Globe size={16} />}
                />

                {/* IPs */}
                <TagInput
                  label="IP Addresses"
                  tags={conditions.ips}
                  onChange={(tags) => updateConditions({ ips: tags })}
                  placeholder="e.g., 192.168.1.0/24"
                  icon={<Network size={16} />}
                />

                {/* App Names */}
                <TagInput
                  label="Application Names"
                  tags={conditions.app_names}
                  onChange={(tags) => updateConditions({ app_names: tags })}
                  placeholder="e.g., nginx, postgres"
                  icon={<AppWindow size={16} />}
                />

                {/* Geo Countries */}
                <TagInput
                  label="Geo Countries"
                  tags={conditions.geo_countries || []}
                  onChange={(tags) => updateConditions({ geo_countries: tags })}
                  placeholder="e.g., CN, RU, KP"
                  icon={<MapPin size={16} />}
                />

                {/* Time Range */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5 flex items-center gap-1">
                    <Clock size={14} />
                    Time Range
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <Input
                      placeholder="Start (e.g., 09:00)"
                      value={timeStart}
                      onChange={(e) => setTimeStart(e.target.value)}
                    />
                    <Input
                      placeholder="End (e.g., 17:00)"
                      value={timeEnd}
                      onChange={(e) => setTimeEnd(e.target.value)}
                    />
                  </div>
                </div>

                {/* Anomaly Threshold */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1.5 flex items-center gap-1">
                    <Activity size={14} />
                    Anomaly Threshold (0 - 1)
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={conditions.anomaly_threshold ?? 0.5}
                    onChange={(e) =>
                      updateConditions({ anomaly_threshold: parseFloat(e.target.value) })
                    }
                    className="w-full accent-cyan-500"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                    <span>0 (sensitive)</span>
                    <span className="text-cyan-400 font-medium">
                      {conditions.anomaly_threshold ?? 0.5}
                    </span>
                    <span>1 (permissive)</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Summary Card */}
            <Card className="sticky top-6">
              <CardHeader>
                <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
                  Policy Summary
                </h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-xs text-gray-500">Name</p>
                  <p className="text-sm text-gray-200">{name || '--'}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Purpose</p>
                  <Badge variant={purpose === 'block' ? 'danger' : 'success'} className="mt-1">
                    {purpose === 'block' ? 'Block' : 'Allow'}
                  </Badge>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Domains</p>
                  <p className="text-sm text-gray-300">
                    {conditions.domains.length || 'None'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">IPs</p>
                  <p className="text-sm text-gray-300">
                    {conditions.ips.length || 'None'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Apps</p>
                  <p className="text-sm text-gray-300">
                    {conditions.app_names.length || 'None'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Countries</p>
                  <p className="text-sm text-gray-300">
                    {conditions.geo_countries?.length || 'None'}
                  </p>
                </div>

                <div className="pt-4 border-t border-gray-700/30 space-y-3">
                  <Button
                    type="submit"
                    variant="primary"
                    className="w-full"
                    icon={<Send size={16} />}
                    loading={submitting}
                    disabled={!name.trim()}
                  >
                    Deploy Policy
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    className="w-full"
                    onClick={() => navigate('/policies')}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
};

export default PolicyCreate;
